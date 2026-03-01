import os
import json
import uuid
import hashlib
import re
from datetime import datetime
import traceback

from .config import PipelineConfig
from .logging import setup_logging, set_log_context
from .store.models import (
    IngestRun,
    RunStats,
    RunError,
    DocumentSource,
    Document,
    ContentStats,
)
from .ids import generate_doc_uid, generate_source_hash, generate_source_id
from .fetch import fetch_source
from .store.mongo import save_run, save_document_pipeline_results

from .parsers.pdf import parse_pdf
from .parsers.html import parse_html
from .parsers.saos import parse_saos
from .parsers.tree import build_tree_nodes


def get_run_id(cfg_run_id: str) -> str:
    if cfg_run_id in ("", "auto"):
        return uuid.uuid4().hex
    return cfg_run_id


def compute_config_hash(config: PipelineConfig) -> str:
    js = config.model_dump_json(exclude={"run": {"run_id", "artifact_dir"}})
    return hashlib.sha256(js.encode("utf-8")).hexdigest()


def detect_mime(fetch_result, url: str) -> str:
    ct = fetch_result.headers.get("content-type", "").lower()
    if "application/pdf" in ct or url.lower().endswith(".pdf"):
        return "application/pdf"
    if "application/json" in ct:
        return "application/json"
    if "text/html" in ct or url.lower().endswith(".html"):
        return "text/html"
    return "application/octet-stream"


def extract_metadata(pages, mime: str, raw_bytes: bytes, doc_type: str):
    title = "Untitled Document"
    date_published = None
    date_decision = None

    if mime == "application/json":
        try:
            payload = json.loads(raw_bytes)
            data = (
                payload.get("data", payload) if isinstance(payload, dict) else payload
            )
            case_number = data.get("courtCases", [{}])[0].get("caseNumber", "")
            judgment_type = data.get("judgmentType", "WYROK")
            court = data.get("courtType", "")
            title = f"{judgment_type} {case_number} ({court})".strip()
            date_decision = data.get("judgmentDate")
        except Exception:
            pass
        return title, date_published, date_decision

    if mime == "text/html":
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw_bytes, "html.parser")
        title_tag = soup.title.string if soup.title else ""
        h1_tag = soup.h1.string if soup.h1 else ""
        title = h1_tag or title_tag or "Untitled HTML Document"
        return title.strip(), date_published, date_decision

    if mime == "application/pdf":
        first_text = ""
        for p in pages[:2]:
            first_text += p.text + "\n"
        match = re.search(
            r"(Ustawa\s+z\s+dnia\s+[^\n]+|Kodeks\s+[^\n]+|WYROK\s+[^\n]+|UCHWA\u0141A\s+[^\n]+|POSTANOWIENIE\s+[^\n]+)",
            first_text,
            re.IGNORECASE,
        )
        if match:
            title = match.group(1).strip()

    return title.strip(), date_published, date_decision


def run_pipeline(config: PipelineConfig, limit: int = None):
    run_id = get_run_id(config.run.run_id)
    artifact_dir = os.path.join(config.run.artifact_dir, "runs", run_id)
    os.makedirs(artifact_dir, exist_ok=True)

    log_file = os.path.join(artifact_dir, "logs.jsonl")
    logger = setup_logging(log_file=log_file)
    set_log_context(run_id=run_id)

    logger.info(
        "Starting ingest pipeline",
        extra={"metrics": {"sources": len(config.sources), "limit": limit}},
    )

    run_model = IngestRun(
        _id=f"run:{run_id}",
        run_id=run_id,
        config_hash=compute_config_hash(config),
        started_at=datetime.utcnow(),
    )

    stats = RunStats(sources_total=len(config.sources))

    if not config.run.dry_run:
        save_run(config.mongo, run_model)

    from .fetch import expand_saos_search

    expanded_sources = []
    for s in config.sources:
        if s.fetch_strategy == "saos_search":
            logger.info(
                f"Expanding saos_search for {s.source_id}", extra={"stage": "init"}
            )
            try:
                new_s = expand_saos_search(config.run.http, s)
                expanded_sources.extend(new_s)
                logger.info(
                    f"saos_search yielded {len(new_s)} judgments",
                    extra={"stage": "init"},
                )
            except Exception as e:
                logger.error(
                    f"Failed to expand saos_search {s.source_id}: {e}",
                    extra={"stage": "init"},
                )
        else:
            expanded_sources.append(s)

    config.sources = expanded_sources
    stats.sources_total = len(expanded_sources)

    for i, source in enumerate(config.sources):
        if limit is not None and i >= limit:
            logger.info("Reached limit, stopping", extra={"metrics": {"limit": limit}})
            break

        doc_uid = generate_doc_uid(str(source.url), source.external_ids)
        set_log_context(source_id=source.source_id, doc_uid=doc_uid)

        logger.info(f"Processing source {source.source_id}", extra={"stage": "init"})

        try:
            # 1. Fetch
            set_log_context(stage="fetch")
            fetch_result = fetch_source(config.run.http, source)

            source_hash = generate_source_hash(fetch_result.raw_bytes)
            mime = detect_mime(fetch_result, str(source.url))

            # Save raw artifacts
            doc_raw_dir = os.path.join(
                config.run.artifact_dir, "docs", doc_uid, "raw", source_hash
            )
            raw_bin_path = os.path.join(doc_raw_dir, "original.bin")

            if not config.run.dry_run:
                os.makedirs(doc_raw_dir, exist_ok=True)
                with open(raw_bin_path, "wb") as f:
                    f.write(fetch_result.raw_bytes)

                meta_path = os.path.join(doc_raw_dir, "response_meta.json")
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "status_code": fetch_result.status_code,
                            "headers": fetch_result.headers,
                            "final_url": fetch_result.final_url,
                        },
                        f,
                    )

            logger.info(
                "Fetched source",
                extra={"metrics": {"bytes": len(fetch_result.raw_bytes)}},
            )

            # 2. DocumentSource Create
            doc_source = DocumentSource(
                _id=generate_source_id(doc_uid, source_hash),
                doc_uid=doc_uid,
                source_hash=source_hash,
                source_id=source.source_id,
                url=str(source.url),
                final_url=fetch_result.final_url,
                http={"status_code": fetch_result.status_code},
                raw_object_path=raw_bin_path,
                raw_mime=mime,
                license_tag=source.license_tag,
            )

            # 3. Detect & Parse
            set_log_context(stage="parse")
            pages = []
            parse_method = "PDF_TEXT"

            # Check for paywalls / restrictions in HTML before parse
            access_status = "OK"
            if mime == "text/html":
                text_lower = fetch_result.raw_bytes.decode(
                    "utf-8", errors="ignore"
                ).lower()
                if (
                    "zaloguj" in text_lower
                    or "abonament" in text_lower
                    or "kup dostęp" in text_lower
                ):
                    access_status = "RESTRICTED"
                    logger.warning(
                        "Restricted content detected via heuristics",
                        extra={"stage": "parse"},
                    )
            if source.license_tag == "COMMERCIAL":
                access_status = "RESTRICTED"

            if mime == "application/pdf":
                pages = parse_pdf(
                    fetch_result.raw_bytes,
                    doc_uid,
                    source_hash,
                    config.parsers.pdf,
                    config.ocr,
                    str(source.url),
                )
                if pages and any(p.extraction.method == "OCR3" for p in pages):
                    parse_method = "OCR3"
                else:
                    parse_method = "PDF_TEXT"
            elif mime == "text/html":
                pages = parse_html(
                    fetch_result.raw_bytes, doc_uid, source_hash, config.parsers.html
                )
                parse_method = "HTML"
                total_chars = sum(len(p.text) for p in pages)
                if total_chars < 500:
                    access_status = "RESTRICTED"
                    logger.warning(
                        "Restricted content detected via low char count",
                        extra={"stage": "parse"},
                    )
            elif mime == "application/json" or source.fetch_strategy == "saos_judgment":
                pages = parse_saos(fetch_result.raw_bytes, doc_uid, source_hash)
                parse_method = "SAOS_JSON"
                access_status = "OK"  # saos is ok
            else:
                raise ValueError(f"Unsupported MIME type: {mime}")

            stats.pages_written += len(pages)

            # 4. Extract Metadata & Build Tree
            set_log_context(stage="normalize")
            title, date_published, date_decision = extract_metadata(
                pages, mime, fetch_result.raw_bytes, source.doc_type_hint
            )
            nodes, tree_nested = build_tree_nodes(
                pages, source.doc_type_hint, doc_uid, source_hash
            )
            citations = []

            # Extract citations for SAOS
            if mime == "application/json" or source.fetch_strategy == "saos_judgment":
                from .parsers.saos import extract_saos_citations

                citations = extract_saos_citations(
                    fetch_result.raw_bytes, doc_uid, source_hash
                )

            stats.citations_written += len(citations)
            stats.nodes_written += len(nodes)

            # Save normalized artifacts
            if not config.run.dry_run:
                doc_norm_dir = os.path.join(
                    config.run.artifact_dir, "docs", doc_uid, "normalized", source_hash
                )
                os.makedirs(doc_norm_dir, exist_ok=True)
                with open(
                    os.path.join(doc_norm_dir, "pages.jsonl"), "w", encoding="utf-8"
                ) as f:
                    for p in pages:
                        f.write(p.model_dump_json(by_alias=True) + "\n")
                with open(
                    os.path.join(doc_norm_dir, "nodes.jsonl"), "w", encoding="utf-8"
                ) as f:
                    for n in nodes:
                        f.write(n.model_dump_json(by_alias=True) + "\n")
                with open(
                    os.path.join(doc_norm_dir, "citations.jsonl"), "w", encoding="utf-8"
                ) as f:
                    for c in citations:
                        f.write(c.model_dump_json(by_alias=True) + "\n")

            # 5. Build Document root
            total_chars = sum(p.char_count for p in pages)
            total_tokens = sum(p.token_count_est for p in pages)

            doc_model = Document(
                _id=doc_uid,
                doc_uid=doc_uid,
                doc_type=source.doc_type_hint,
                jurisdiction=source.jurisdiction,
                language=source.language,
                source_system=doc_uid.split(":")[0],
                title=title,
                external_ids=source.external_ids or {},
                source_urls=[str(source.url)],
                license_tag="COMMERCIAL"
                if access_status == "RESTRICTED"
                else source.license_tag,
                access_status=access_status,
                date_published=date_published,
                date_decision=date_decision,
                current_source_hash=source_hash,
                mime=mime,
                page_count=len(pages),
                content_stats=ContentStats(
                    total_chars=total_chars,
                    total_tokens_est=total_tokens,
                    parse_method=parse_method,
                    ocr_used=(parse_method == "OCR3"),
                ),
                pageindex_tree=tree_nested,
            )

            # Save to Mongo
            set_log_context(stage="save")
            if not config.run.dry_run:
                save_document_pipeline_results(
                    config.mongo,
                    doc_source,
                    pages,
                    nodes,
                    citations=citations,
                    document=doc_model,
                )

            if access_status == "OK":
                stats.docs_ok += 1
            else:
                stats.docs_restricted += 1

            logger.info(
                "Document saved successfully",
                extra={"metrics": {"pages": len(pages), "nodes": len(nodes)}},
            )

        except Exception as e:
            logger.error(
                f"Error processing source: {e}\n{traceback.format_exc()}",
                extra={"stage": "pipeline"},
            )
            stats.docs_error += 1
            run_model.errors.append(
                RunError(
                    source_id=source.source_id,
                    stage="pipeline",
                    error_type=type(e).__name__,
                    message=str(e),
                )
            )

    # Finalize
    run_model.stats = stats
    run_model.finished_at = datetime.utcnow()

    if not config.run.dry_run:
        save_run(config.mongo, run_model)

    report_path = os.path.join(artifact_dir, "run_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(run_model.model_dump_json(by_alias=True, indent=2))

    logger.info(
        "Pipeline run finished", extra={"stage": "finalize", "metrics": stats.dict()}
    )
