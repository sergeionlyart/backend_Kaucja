from legal_ingest.ids import generate_doc_uid, generate_source_hash


def test_generate_doc_uid_with_external():
    # Test ELI priority
    ext = {"eli": "DU/2001/733"}
    uid = generate_doc_uid("https://eli.gov.pl/test.pdf", ext)
    assert uid == "eli_pl:DU/2001/733"


def test_generate_doc_uid_sn():
    ext = {"sn_signature": "III CZP 58/02"}
    uid = generate_doc_uid("https://www.sn.pl/test.pdf", ext)
    assert uid == "sn_pl:III_CZP_58-02"


def test_generate_doc_uid_fallback():
    url = "https://example.com/doc.pdf"
    uid = generate_doc_uid(url)
    assert uid.startswith("unknown:urlsha:")


def test_generate_source_hash():
    b = b"hello world"
    h = generate_source_hash(b)
    assert len(h) == 64
