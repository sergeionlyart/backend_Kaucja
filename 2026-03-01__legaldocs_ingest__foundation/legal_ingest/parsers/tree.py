import re
from typing import Tuple, List, Dict, Any
from ..store.models import Page, Node
from ..ids import generate_node_id


def build_tree_nodes(
    pages: list[Page], doc_type: str, doc_uid: str, source_hash: str
) -> Tuple[list[Node], List[Dict[str, Any]]]:
    """
    Builds the flat list of Nodes and a nested tree hierarchy for documents.pageindex_tree.
    Enforces a 'root' node for all documents.
    Iteration 1 MVP: simplified regex for STATUTE/EU_ACT and CASELAW.
    """
    nodes = []
    tree_nested = []

    page_count = len(pages)

    # Always create root node
    root_node = Node(
        _id=generate_node_id(doc_uid, source_hash, "root"),
        doc_uid=doc_uid,
        source_hash=source_hash,
        node_id="root",
        parent_node_id="none",
        depth=0,
        order_index=0,
        title="Root Document",
        start_index=0,
        end_index=page_count,
    )
    nodes.append(root_node)

    root_dict = {
        "title": root_node.title,
        "node_id": root_node.node_id,
        "start_index": root_node.start_index,
        "end_index": root_node.end_index,
        "summary": None,
        "nodes": [],
    }
    tree_nested.append(root_dict)

    # Only build deeper tree if doc_type is STATUTE, CASELAW, or EU_ACT
    if doc_type in ["STATUTE", "EU_ACT"]:
        art_idx_map = []
        for p in pages:
            lines = p.text.splitlines()
            for line in lines:
                line = line.strip()
                # matches "Art. 1." or "Article 1"
                m = re.match(r"^(?:Art\.|Article)\s+(\d+[a-z]?)\b", line, re.IGNORECASE)
                if m:
                    art_num = m.group(1)
                    # only keep the first occurrence of an article to define its start page
                    if not any(a["num"] == art_num for a in art_idx_map):
                        art_idx_map.append(
                            {
                                "num": art_num,
                                "title": line[:50],
                                "page_index": p.page_index,
                            }
                        )

        # create nodes for each found article
        for i, art in enumerate(art_idx_map):
            start_idx = art["page_index"]
            end_idx = (
                art_idx_map[i + 1]["page_index"]
                if i + 1 < len(art_idx_map)
                else page_count
            )
            # Edge case: multiple articles on the same page
            if end_idx < start_idx:
                end_idx = start_idx + 1  # force minimum 1 length range or same page
            if end_idx == start_idx:
                end_idx = start_idx + 1

            node_id = f"art:{art['num']}"
            n = Node(
                _id=generate_node_id(doc_uid, source_hash, node_id),
                doc_uid=doc_uid,
                source_hash=source_hash,
                node_id=node_id,
                parent_node_id="root",
                depth=1,
                order_index=i + 1,
                title=art["title"],
                start_index=start_idx,
                end_index=end_idx,
                anchors={"article": art["num"]},
            )
            nodes.append(n)
            root_dict["nodes"].append(
                {
                    "title": n.title,
                    "node_id": n.node_id,
                    "start_index": n.start_index,
                    "end_index": n.end_index,
                    "summary": None,
                    "nodes": [],
                }
            )

    elif doc_type == "CASELAW":
        # MVP for Caselaw: find sections like UZASADNIENIE, SENTENCJA
        sec_idx_map = []
        for p in pages:
            for line in p.text.splitlines():
                if line.strip().upper() in [
                    "UZASADNIENIE",
                    "SENTENCJA",
                    "WYROK",
                    "POSTANOWIENIE",
                    "UCHWAŁA",
                ]:
                    sec_title = line.strip()
                    sec_idx_map.append({"title": sec_title, "page_index": p.page_index})

        for i, sec in enumerate(sec_idx_map):
            start_idx = sec["page_index"]
            end_idx = (
                sec_idx_map[i + 1]["page_index"]
                if i + 1 < len(sec_idx_map)
                else page_count
            )
            if end_idx == start_idx:
                end_idx = start_idx + 1

            node_id = f"sec:{sec['title'].lower()[:10]}"
            n = Node(
                _id=generate_node_id(doc_uid, source_hash, node_id),
                doc_uid=doc_uid,
                source_hash=source_hash,
                node_id=node_id,
                parent_node_id="root",
                depth=1,
                order_index=i + 1,
                title=sec["title"],
                start_index=start_idx,
                end_index=end_idx,
            )
            nodes.append(n)
            root_dict["nodes"].append(
                {
                    "title": n.title,
                    "node_id": n.node_id,
                    "start_index": n.start_index,
                    "end_index": n.end_index,
                    "summary": None,
                    "nodes": [],
                }
            )

    # For HTML/SAOS, they already have basic structural virtualization.
    return nodes, tree_nested
