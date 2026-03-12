from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, parse_qsl, unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

Fetcher = Callable[[str, float], "FetchResponse"]

DEFAULT_INPUT_PATH = Path("docs/legal/cas_law_V_2.2 2.md")
DEFAULT_OUTPUT_PATH = Path("artifacts/legal_collection")
DEFAULT_TIMEOUT_SECONDS = 30.0
USER_AGENT = "backend-kaucja/legal-collection/0.1"
SOURCE_LINE_PATTERN = re.compile(r"^\s*(\d+)\.\s+(https?://\S+)\s*$")


@dataclass(frozen=True, slots=True)
class SourceEntry:
    index: int
    category: str
    url: str
    canonical_url: str
    source_system: str
    fetch_strategy: str
    source_id: str
    doc_uid: str
    jurisdiction: str
    license_tag: str


@dataclass(frozen=True, slots=True)
class FetchResponse:
    url: str
    status_code: int
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True, slots=True)
class DownloadRecord:
    index: int
    source_id: str
    doc_uid: str
    url: str
    fetch_strategy: str
    status: str
    http_status: int | None
    final_url: str | None
    source_hash: str | None
    raw_object_path: str | None
    response_meta_path: str | None
    error: str | None


def parse_source_markdown(text: str) -> list[SourceEntry]:
    sources: list[SourceEntry] = []
    current_category = "Uncategorized"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = SOURCE_LINE_PATTERN.match(line)
        if match is None:
            current_category = line
            continue

        index = int(match.group(1))
        url = match.group(2)
        canonical_url = canonicalize_url(url)
        source_system = detect_source_system(url)
        doc_uid = derive_doc_uid(url)
        sources.append(
            SourceEntry(
                index=index,
                category=current_category,
                url=url,
                canonical_url=canonical_url,
                source_system=source_system,
                fetch_strategy=derive_fetch_strategy(url),
                source_id=derive_source_id(
                    source_system=source_system, doc_uid=doc_uid
                ),
                doc_uid=doc_uid,
                jurisdiction=derive_jurisdiction(source_system),
                license_tag=derive_license_tag(source_system),
            )
        )

    return sources


def parse_source_markdown_file(path: Path) -> list[SourceEntry]:
    return parse_source_markdown(path.read_text(encoding="utf-8"))


def build_local_collection(
    *,
    input_path: Path,
    output_dir: Path,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    limit: int | None = None,
    dry_run: bool = False,
    fetcher: Fetcher | None = None,
) -> dict[str, object]:
    sources = parse_source_markdown_file(input_path)
    if limit is not None:
        sources = sources[:limit]

    active_fetcher = fetcher or urlopen_fetch
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed_sources_path = output_dir / "parsed_sources.json"
    write_json(parsed_sources_path, [asdict(source) for source in sources])

    records: list[DownloadRecord] = []
    for source in sources:
        if dry_run:
            records.append(
                DownloadRecord(
                    index=source.index,
                    source_id=source.source_id,
                    doc_uid=source.doc_uid,
                    url=source.url,
                    fetch_strategy=source.fetch_strategy,
                    status="dry_run",
                    http_status=None,
                    final_url=None,
                    source_hash=None,
                    raw_object_path=None,
                    response_meta_path=None,
                    error=None,
                )
            )
            continue

        records.append(
            download_source(
                source=source,
                output_dir=output_dir,
                timeout_seconds=timeout_seconds,
                fetcher=active_fetcher,
            )
        )

    report = {
        "input_path": str(input_path.resolve()),
        "output_dir": str(output_dir.resolve()),
        "source_count": len(sources),
        "dry_run": dry_run,
        "summary": {
            "ok": sum(1 for record in records if record.status == "ok"),
            "error": sum(1 for record in records if record.status == "error"),
            "dry_run": sum(1 for record in records if record.status == "dry_run"),
        },
        "downloads": [asdict(record) for record in records],
        "generated_at": utc_now(),
    }
    write_json(output_dir / "collection_manifest.json", report)
    return report


def download_source(
    *,
    source: SourceEntry,
    output_dir: Path,
    timeout_seconds: float,
    fetcher: Fetcher,
) -> DownloadRecord:
    try:
        response = fetcher(source.url, timeout_seconds)
    except Exception as error:  # noqa: BLE001
        return DownloadRecord(
            index=source.index,
            source_id=source.source_id,
            doc_uid=source.doc_uid,
            url=source.url,
            fetch_strategy=source.fetch_strategy,
            status="error",
            http_status=None,
            final_url=None,
            source_hash=None,
            raw_object_path=None,
            response_meta_path=None,
            error=str(error),
        )

    if response.status_code >= 400:
        return DownloadRecord(
            index=source.index,
            source_id=source.source_id,
            doc_uid=source.doc_uid,
            url=source.url,
            fetch_strategy=source.fetch_strategy,
            status="error",
            http_status=response.status_code,
            final_url=response.url,
            source_hash=None,
            raw_object_path=None,
            response_meta_path=None,
            error=f"HTTP {response.status_code}",
        )

    source_hash = hashlib.sha256(response.body).hexdigest()
    doc_root = output_dir / "docs" / filesystem_token(source.doc_uid)
    raw_dir = doc_root / "raw" / source_hash
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_object_path = raw_dir / "original.bin"
    response_meta_path = raw_dir / "response_meta.json"
    raw_object_path.write_bytes(response.body)
    write_json(
        response_meta_path,
        {
            "source_id": source.source_id,
            "doc_uid": source.doc_uid,
            "url": source.url,
            "final_url": response.url,
            "http_status": response.status_code,
            "headers": response.headers,
            "source_hash": source_hash,
            "downloaded_at": utc_now(),
        },
    )
    write_json(
        doc_root / "document.json",
        {
            "doc_uid": source.doc_uid,
            "source_id": source.source_id,
            "category": source.category,
            "source_system": source.source_system,
            "fetch_strategy": source.fetch_strategy,
            "jurisdiction": source.jurisdiction,
            "license_tag": source.license_tag,
            "source_urls": [source.url],
            "current_source_hash": source_hash,
            "raw_object_path": str(raw_object_path.resolve()),
            "response_meta_path": str(response_meta_path.resolve()),
            "updated_at": utc_now(),
        },
    )

    return DownloadRecord(
        index=source.index,
        source_id=source.source_id,
        doc_uid=source.doc_uid,
        url=source.url,
        fetch_strategy=source.fetch_strategy,
        status="ok",
        http_status=response.status_code,
        final_url=response.url,
        source_hash=source_hash,
        raw_object_path=str(raw_object_path.resolve()),
        response_meta_path=str(response_meta_path.resolve()),
        error=None,
    )


def urlopen_fetch(url: str, timeout_seconds: float) -> FetchResponse:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            status_code = int(getattr(response, "status", response.getcode()))
            headers = dict(response.headers.items())
            final_url = response.geturl()
            return FetchResponse(
                url=final_url,
                status_code=status_code,
                headers=headers,
                body=body,
            )
    except HTTPError as error:
        return FetchResponse(
            url=error.geturl(),
            status_code=error.code,
            headers=dict(error.headers.items()),
            body=error.read(),
        )
    except URLError as error:
        raise RuntimeError(
            f"Network error while fetching {url}: {error.reason}"
        ) from error


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url)
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    normalized_query = "&".join(
        f"{key}={value}" for key, value in sorted(query_items, key=lambda item: item)
    )
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            normalized_query,
            parsed.fragment,
        )
    )


def detect_source_system(url: str) -> str:
    hostname = (urlsplit(url).hostname or "").lower()
    if hostname == "eli.gov.pl":
        return "eli_pl"
    if hostname == "isap.sejm.gov.pl":
        return "isap_pl"
    if hostname == "sip.lex.pl":
        return "lex_pl"
    if hostname in {"sn.pl", "www.sn.pl"}:
        return "sn_pl"
    if hostname.endswith("saos.org.pl"):
        return "saos_pl"
    if hostname == "eur-lex.europa.eu":
        return "eurlex_eu"
    if hostname == "curia.europa.eu":
        return "curia_eu"
    if hostname in {
        "uokik.gov.pl",
        "rejestr.uokik.gov.pl",
        "decyzje.uokik.gov.pl",
    }:
        return "uokik_pl"
    if hostname in {"prawo.pl", "www.prawo.pl"}:
        return "prawo_pl"
    if hostname.startswith("orzeczenia.") and hostname.endswith(".gov.pl"):
        return "courts_pl"
    return "web"


def derive_fetch_strategy(url: str) -> str:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path

    if hostname.endswith("saos.org.pl") and path.startswith("/search"):
        return "saos_search"
    if hostname.endswith("saos.org.pl") and path.startswith("/judgments/"):
        return "saos_judgment"
    return "direct"


def derive_doc_uid(url: str) -> str:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    path = unquote(parsed.path)
    query = parse_qs(parsed.query)

    if hostname == "eli.gov.pl":
        match = re.search(r"/api/acts/([^/]+)/([^/]+)/([^/]+)/", path)
        if match is not None:
            return f"eli_pl:{match.group(1)}/{match.group(2)}/{match.group(3)}"

    if hostname == "isap.sejm.gov.pl":
        match = re.search(r"/(WDU\d+)", path, flags=re.IGNORECASE)
        if match is not None:
            return f"isap_pl:{match.group(1).upper()}"

    if hostname == "sip.lex.pl":
        return f"lex_pl:{extract_lex_identifier(path)}"

    if hostname in {"sn.pl", "www.sn.pl"}:
        return f"sn_pl:{extract_sn_identifier(path)}"

    if hostname.endswith("saos.org.pl") and path.startswith("/search"):
        keywords = first_query_value(query, "keywords") or parsed.query or "search"
        return f"saos_pl:search:{slugify(keywords)}"

    if hostname.endswith("saos.org.pl"):
        match = re.search(r"/judgments/(\d+)", path)
        if match is not None:
            return f"saos_pl:{match.group(1)}"

    if hostname.startswith("orzeczenia.") and hostname.endswith(".gov.pl"):
        segment = path.split("/content/$N/")[-1].strip("/") or Path(path).name
        return f"courts_pl:{segment}"

    if hostname == "eur-lex.europa.eu":
        uri = first_query_value(query, "uri")
        if uri and uri.upper().startswith("CELEX:"):
            return f"eurlex_eu:celex:{uri.split(':', 1)[1]}"
        if path.startswith("/eli/"):
            return f"eurlex_eu:eli:{path.split('/eli/', 1)[1].strip('/')}"

    if hostname == "curia.europa.eu":
        doc_id = first_query_value(query, "docid")
        if doc_id:
            return f"curia_eu:docid:{doc_id}"
        match = re.search(r"/jcms/jcms/(p\d+_\d+)", path)
        if match is not None:
            return f"curia_eu:jcms:{match.group(1)}"

    if hostname in {
        "uokik.gov.pl",
        "rejestr.uokik.gov.pl",
        "decyzje.uokik.gov.pl",
    }:
        return f"uokik_pl:{extract_last_path_identifier(path)}"

    if hostname in {"prawo.pl", "www.prawo.pl"}:
        return f"prawo_pl:{extract_last_path_identifier(path)}"

    canonical_url = canonicalize_url(url)
    short_hash = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]
    source_system = detect_source_system(url)
    return f"{source_system}:urlsha:{short_hash}"


def extract_lex_identifier(path: str) -> str:
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return "unknown"

    main_slug = segments[-1]
    article_slug = ""
    if len(segments) >= 2 and not re.search(r"-\d+$", segments[-1]):
        main_slug = segments[-2]
        article_slug = segments[-1]

    match = re.search(r"-(\d+)$", main_slug)
    if match is None:
        base = slugify(main_slug)
    else:
        base = match.group(1)

    if article_slug:
        return f"{base}:{article_slug}"
    return base


def extract_sn_identifier(path: str) -> str:
    filename = Path(path).name
    base = re.sub(r"(\.docx\.html|\.pdf|\.html)$", "", filename, flags=re.IGNORECASE)
    normalized = re.sub(r"\s+", " ", base).strip()
    match = re.match(
        r"(?i)^([ivxlcdm]+\s+[a-z]{2,5}\s+\d+-\d+)(?:-\d+)?$",
        normalized,
    )
    if match is None:
        return slugify(normalized)
    return match.group(1).upper().replace(" ", "_")


def extract_last_path_identifier(path: str) -> str:
    filename = Path(path).name or path.strip("/")
    base = re.sub(r"(\.pdf|\.html|\.htm)$", "", filename, flags=re.IGNORECASE)
    return base or "unknown"


def derive_source_id(source_system: str, doc_uid: str) -> str:
    prefix_map = {
        "eli_pl": "pl_eli",
        "isap_pl": "pl_isap",
        "lex_pl": "pl_lex",
        "sn_pl": "pl_sn",
        "saos_pl": "pl_saos",
        "courts_pl": "pl_courts",
        "eurlex_eu": "eu_eurlex",
        "curia_eu": "eu_curia",
        "uokik_pl": "pl_uokik",
        "prawo_pl": "pl_prawo",
        "web": "web",
    }
    suffix = doc_uid.split(":", 1)[1] if ":" in doc_uid else doc_uid
    cleaned_suffix = suffix
    cleaned_suffix = cleaned_suffix.replace("celex:", "")
    cleaned_suffix = cleaned_suffix.replace("docid:", "")
    return f"{prefix_map.get(source_system, source_system)}_{slugify(cleaned_suffix)}"


def derive_jurisdiction(source_system: str) -> str:
    if source_system in {"eurlex_eu", "curia_eu"}:
        return "EU"
    return "PL"


def derive_license_tag(source_system: str) -> str:
    if source_system == "lex_pl":
        return "COMMERCIAL"
    if source_system in {
        "eli_pl",
        "isap_pl",
        "sn_pl",
        "saos_pl",
        "courts_pl",
        "eurlex_eu",
        "curia_eu",
        "uokik_pl",
    }:
        return "OFFICIAL"
    return "UNKNOWN"


def slugify(value: str) -> str:
    normalized = unquote(value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "item"


def filesystem_token(value: str) -> str:
    return slugify(value.replace(":", "_").replace("/", "_"))


def first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    first = values[0].strip()
    return first or None


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a markdown source list and download documents into a local "
            "filesystem collection."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=f"Path to markdown source list (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output directory for local collection (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for the number of sources to process.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Network timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only parse and emit manifests without network downloads.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")

    report = build_local_collection(
        input_path=args.input,
        output_dir=args.output,
        timeout_seconds=args.timeout_seconds,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    summary = report["summary"]
    print(
        "local_collection "
        f"sources={report['source_count']} "
        f"ok={summary['ok']} "
        f"error={summary['error']} "
        f"dry_run={summary['dry_run']} "
        f"manifest={args.output / 'collection_manifest.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
