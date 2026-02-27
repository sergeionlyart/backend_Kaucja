import textwrap
from pathlib import Path


def convert_txt_to_pdf(txt_path: Path, pdf_path: Path) -> None:
    """
    Converts a plain text file into a paginated PDF document.

    Args:
        txt_path: Path to the input .txt file
        pdf_path: Path where the output .pdf should be saved
    """
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("pymupdf package is not installed") from error

    text = txt_path.read_text(encoding="utf-8")

    doc = fitz.open()
    font_size = 11
    line_height = font_size * 1.2
    margin = 50

    # Standard A4 dimensions
    page_width = 595.0
    page_height = 842.0

    usable_width = page_width - 2 * margin
    usable_height = page_height - 2 * margin

    # Empirical calculation for characters per line in Helvetica 11pt
    chars_per_line = int(usable_width / (font_size * 0.55))
    max_lines_per_page = int(usable_height / line_height)

    lines = []
    for raw_line in text.splitlines():
        # Retain empty lines for paragraph spacing
        if not raw_line.strip():
            lines.append("")
        else:
            wrapped = textwrap.wrap(raw_line, width=chars_per_line)
            lines.extend(wrapped)

    # Paginate and render
    for i in range(0, len(lines), max_lines_per_page):
        page_lines = lines[i : i + max_lines_per_page]
        page = doc.new_page(width=page_width, height=page_height)

        y = margin
        for line in page_lines:
            page.insert_text(
                fitz.Point(margin, y + font_size),
                line,
                fontsize=font_size,
                fontname="helv",
                color=(0, 0, 0),
            )
            y += line_height

    # Guarantee at least one valid page to prevent Corrupted file errors
    if len(doc) == 0:
        doc.new_page()

    doc.save(pdf_path)
    doc.close()
