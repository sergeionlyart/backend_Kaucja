from bs4 import BeautifulSoup
from ..config import HtmlParserConfig
from ..store.models import Page, PageExtraction, PageExtractionQuality
from ..ids import generate_page_id


def parse_html(
    raw_bytes: bytes, doc_uid: str, source_hash: str, config: HtmlParserConfig
) -> list[Page]:
    soup = BeautifulSoup(raw_bytes, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Virtual chunking logic using BS4. We'll simply chunk by h1/h2 tags or token count
    # Simplified string extraction for Iteration 1
    chunks = []
    current_chunk = []
    current_tokens = 0

    for element in soup.body.descendants if soup.body else soup.descendants:
        if element.name in ["h1", "h2"] and current_chunk:
            # Yield virtual page on Heading (if we have collected stuff)
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0

        if element.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]:
            text = element.get_text(strip=True)
            if not text:
                continue

            # Simple markdown-ish conversion
            if element.name.startswith("h"):
                level = int(element.name[1])
                text = f"{'#' * level} {text}"
            elif element.name == "li":
                text = f"- {text}"

            current_chunk.append(text)
            current_tokens += len(text.split())

            if current_tokens >= config.max_tokens_per_virtual_page:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    if not chunks:
        # Fallback if no specific tags matched
        text = soup.get_text(separator="\n", strip=True)
        chunks = [text]

    pages = []
    for idx, text in enumerate(chunks):
        extraction = PageExtraction(
            method="HTML", quality=PageExtractionQuality(alpha_ratio=1.0, empty=False)
        )
        p = Page(
            _id=generate_page_id(doc_uid, source_hash, idx),
            doc_uid=doc_uid,
            source_hash=source_hash,
            page_index=idx,
            text=text,
            token_count_est=len(text.split()),
            char_count=len(text),
            extraction=extraction,
        )
        pages.append(p)

    return pages
