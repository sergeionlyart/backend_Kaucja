from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "backend-kaucja/legal-ingest/0.2"


@dataclass(frozen=True, slots=True)
class HttpResponse:
    url: str
    status_code: int
    headers: dict[str, str]
    body: bytes


def fetch_binary(url: str, *, timeout_seconds: float = 60.0) -> HttpResponse:
    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            return HttpResponse(
                url=response.geturl(),
                status_code=int(getattr(response, "status", response.getcode())),
                headers=dict(response.headers.items()),
                body=body,
            )
    except HTTPError as error:
        return HttpResponse(
            url=error.geturl(),
            status_code=int(error.code),
            headers=dict(error.headers.items()),
            body=error.read(),
        )
    except URLError as error:
        raise RuntimeError(
            f"Network error while fetching {url}: {error.reason}"
        ) from error
