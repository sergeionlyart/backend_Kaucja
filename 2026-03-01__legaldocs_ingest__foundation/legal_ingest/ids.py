import hashlib
from urllib.parse import urlparse


def get_source_system(hostname: str) -> str:
    if "eli.gov.pl" in hostname:
        return "eli_pl"
    if "isap.sejm.gov.pl" in hostname:
        return "isap_pl"
    if "sip.lex.pl" in hostname:
        return "lex_pl"
    if "sn.pl" in hostname:
        return "sn_pl"
    if "saos.org.pl" in hostname:
        return "saos_pl"
    if "orzeczenia." in hostname:
        return "courts_pl"
    if "eur-lex.europa.eu" in hostname:
        return "eurlex_eu"
    if "curia.europa.eu" in hostname:
        return "curia_eu"
    if "uokik.gov.pl" in hostname:
        return "uokik_pl"
    if "prawo.pl" in hostname:
        return "prawo_pl"
    return "unknown"


def generate_doc_uid(url: str, external_ids: dict = None) -> str:
    parsed = urlparse(url)
    sys = get_source_system(parsed.hostname or "")
    if external_ids:
        # TechSpec prefers primary ID if available from config
        if "eli" in external_ids:
            return f"{sys}:{external_ids['eli']}"
        if "isap_wdu" in external_ids:
            return f"{sys}:{external_ids['isap_wdu']}"
        if "saos_id" in external_ids:
            return f"{sys}:{external_ids['saos_id']}"
        if "sn_signature" in external_ids:
            # normalize signature: III CZP 58/02 -> III_CZP_58-02
            sig = external_ids["sn_signature"].replace(" ", "_").replace("/", "-")
            return f"{sys}:{sig}"

    # fallback to urlsha
    hashed = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{sys}:urlsha:{hashed}"


def generate_source_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def generate_page_id(doc_uid: str, source_hash: str, page_index: int) -> str:
    return f"{doc_uid}|{source_hash}|p:{page_index}"


def generate_node_id(doc_uid: str, source_hash: str, node_id: str) -> str:
    return f"{doc_uid}|{source_hash}|node:{node_id}"


def generate_citation_id(
    doc_uid: str, source_hash: str, from_node: str, text: str, anchor: str = ""
) -> str:
    seed = f"{from_node}|{anchor}|{text}"
    cit_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"{doc_uid}|{source_hash}|cit:{cit_hash}"


def generate_source_id(doc_uid: str, source_hash: str) -> str:
    return f"{doc_uid}|{source_hash}"
