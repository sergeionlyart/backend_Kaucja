from legal_ingest.parsers.tree import build_tree_nodes
from legal_ingest.store.models import Page, PageExtraction, PageExtractionQuality


def test_tree_root_invariants():
    # 1. page_count = 0
    nodes, _ = build_tree_nodes([], "STATUTE", "doc1", "hash1")
    root = nodes[0]
    assert root.start_index == 0
    assert root.end_index == 0

    # 2. page_count = 3
    p1 = Page(
        _id="1",
        doc_uid="doc1",
        source_hash="hash1",
        page_index=0,
        text="page 1",
        token_count_est=1,
        char_count=1,
        extraction=PageExtraction(
            method="HTML", quality=PageExtractionQuality(alpha_ratio=1.0, empty=False)
        ),
    )
    p2 = Page(
        _id="2",
        doc_uid="doc1",
        source_hash="hash1",
        page_index=1,
        text="page 2",
        token_count_est=1,
        char_count=1,
        extraction=PageExtraction(
            method="HTML", quality=PageExtractionQuality(alpha_ratio=1.0, empty=False)
        ),
    )
    p3 = Page(
        _id="3",
        doc_uid="doc1",
        source_hash="hash1",
        page_index=2,
        text="page 3",
        token_count_est=1,
        char_count=1,
        extraction=PageExtraction(
            method="HTML", quality=PageExtractionQuality(alpha_ratio=1.0, empty=False)
        ),
    )

    nodes, _ = build_tree_nodes([p1, p2, p3], "STATUTE", "doc1", "hash1")
    root = nodes[0]
    assert root.start_index == 0
    assert root.end_index == 3
