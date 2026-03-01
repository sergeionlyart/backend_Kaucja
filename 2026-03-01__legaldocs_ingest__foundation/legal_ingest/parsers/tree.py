import re
from typing import Tuple, List, Dict, Any
from ..store.models import Page, Node
from ..ids import generate_node_id


def build_tree_nodes(
    pages: list[Page], doc_type: str, doc_uid: str, source_hash: str
) -> Tuple[list[Node], List[Dict[str, Any]]]:
    nodes = []
    tree_nested = []

    page_count = len(pages)

    # Invariant: Root covers [0, page_count) unconditionally
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
        end_index=max(1, page_count),
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

    if not pages:
        return nodes, tree_nested

    idx_map = []

    if doc_type in ["STATUTE", "EU_ACT"]:
        for p in pages:
            for line in p.text.splitlines():
                line = line.strip()
                # Chapters
                m_chap = re.match(
                    r"^(?:Rozdzia\u0142|ROZDZIA\u0141|Chapter)\s+(\S+)",
                    line,
                    re.IGNORECASE,
                )
                if m_chap:
                    chap_num = m_chap.group(1)
                    if not any(a.get("chap") == chap_num for a in idx_map):
                        idx_map.append(
                            {
                                "type": "chapter",
                                "chap": chap_num,
                                "title": line[:100],
                                "page_index": p.page_index,
                            }
                        )
                    continue
                # Articles
                m_art = re.match(
                    r"^(?:Art\.|Article)\s+(\d+[a-z]?)\b", line, re.IGNORECASE
                )
                if m_art:
                    art_num = m_art.group(1)
                    if not any(a.get("art") == art_num for a in idx_map):
                        idx_map.append(
                            {
                                "type": "article",
                                "art": art_num,
                                "title": line[:50],
                                "page_index": p.page_index,
                            }
                        )

    elif doc_type == "CASELAW":
        for p in pages:
            for line in p.text.splitlines():
                clean_line = line.strip().upper()
                if clean_line in [
                    "UZASADNIENIE",
                    "SENTENCJA",
                    "WYROK",
                    "POSTANOWIENIE",
                    "UCHWA\u0141A",
                ]:
                    if not any(a["title"].upper() == clean_line for a in idx_map):
                        idx_map.append(
                            {
                                "title": line.strip(),
                                "page_index": p.page_index,
                                "type": "section",
                            }
                        )
                        break

    # HTML/Markdown Headings fallback
    if not idx_map:
        for p in pages:
            for line in p.text.splitlines():
                m_heading = re.match(r"^(#{1,3})\s+(.+)", line.strip())
                if m_heading:
                    level = len(m_heading.group(1))
                    title = m_heading.group(2)[:100]
                    if not any(a.get("title") == title for a in idx_map):
                        idx_map.append(
                            {
                                "type": "heading",
                                "level": level,
                                "title": title,
                                "page_index": p.page_index,
                            }
                        )

    # Build node instances enforcing exclusive bounds logic
    for i, item in enumerate(idx_map):
        start_idx = item["page_index"]
        end_idx = idx_map[i + 1]["page_index"] if i + 1 < len(idx_map) else page_count

        # Enforce end-exclusive math & bounds clipping
        if end_idx <= start_idx:
            end_idx = start_idx + 1
        if end_idx > page_count:
            end_idx = max(start_idx + 1, page_count)

        anchors = {}
        if item.get("type") == "article":
            node_id = f"art:{item['art']}"
            anchors["article"] = item["art"]
        elif item.get("type") == "chapter":
            node_id = f"chap:{item['chap']}"
        elif item.get("type") == "section":
            node_id = f"sec:{item['title'].lower()[:10]}"
        elif item.get("type") == "heading":
            node_id = f"hdg:{item['title'].lower()[:10]}"
        else:
            node_id = f"node:{i}"

        # Clean ID
        node_id = "".join(c if c.isalnum() or c in ":-" else "_" for c in node_id)

        n = Node(
            _id=generate_node_id(doc_uid, source_hash, node_id),
            doc_uid=doc_uid,
            source_hash=source_hash,
            node_id=node_id,
            parent_node_id="root",
            depth=1,
            order_index=i + 1,
            title=item.get("title", ""),
            start_index=start_idx,
            end_index=end_idx,
            anchors=anchors,
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

    return nodes, tree_nested
