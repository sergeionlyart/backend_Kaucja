"""Test URL parity between cas_law_V_2.2 2.md and config.caslaw_v22.full.yml"""
import re
import os
import yaml


FOUNDATION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MARKDOWN_PATH = os.path.join(
    FOUNDATION_DIR, "..", "..", "backend_Kaucja", "docs", "legal", "cas_law_V_2.2 2.md"
)
YAML_CONFIG_PATH = os.path.join(
    FOUNDATION_DIR, "configs", "config.caslaw_v22.full.yml"
)


def _extract_urls_from_markdown(path: str) -> list[str]:
    """Extract all URLs from the numbered list in the markdown file."""
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Match lines like: \t1.\thttps://... or 6. https://...
            m = re.search(r'(?:^|\t)\d+\.\s*(https?://\S+)', line.strip())
            if m:
                urls.append(m.group(1))
    return urls


def _extract_urls_from_yaml(path: str) -> list[str]:
    """Extract source URLs from the YAML config file in order."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [src["url"] for src in data.get("sources", [])]


def test_markdown_has_38_urls():
    if not os.path.exists(MARKDOWN_PATH):
        import pytest
        pytest.skip("Markdown source file not found (cross-repo)")
    urls = _extract_urls_from_markdown(MARKDOWN_PATH)
    assert len(urls) == 38, f"Expected 38 URLs in markdown, got {len(urls)}"


def test_yaml_has_38_sources():
    sources_urls = _extract_urls_from_yaml(YAML_CONFIG_PATH)
    assert len(sources_urls) == 38, f"Expected 38 sources in YAML, got {len(sources_urls)}"


def test_url_parity_markdown_vs_yaml():
    """Verify exact 1:1 order and URL match between markdown and YAML config."""
    if not os.path.exists(MARKDOWN_PATH):
        import pytest
        pytest.skip("Markdown source file not found (cross-repo)")

    md_urls = _extract_urls_from_markdown(MARKDOWN_PATH)
    yaml_urls = _extract_urls_from_yaml(YAML_CONFIG_PATH)

    assert len(md_urls) == len(yaml_urls) == 38

    for i, (md_url, yaml_url) in enumerate(zip(md_urls, yaml_urls)):
        assert md_url == yaml_url, (
            f"URL mismatch at index {i+1}: "
            f"markdown={md_url} vs yaml={yaml_url}"
        )
