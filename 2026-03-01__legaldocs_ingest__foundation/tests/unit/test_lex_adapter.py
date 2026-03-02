from legal_ingest.fetch import transform_lex_url

def test_transform_lex_url_base_doc():
    url = "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658"
    expected = "https://sip.lex.pl/apimobile/document/16903658?documentConfigurationId=lawJournal"
    assert transform_lex_url(url) == expected

def test_transform_lex_url_with_unit_id_simple():
    url = "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118"
    expected = "https://sip.lex.pl/apimobile/document/16785996?documentConfigurationId=lawJournal&unitId=art%28118%29"
    assert transform_lex_url(url) == expected

def test_transform_lex_url_with_unit_id_compound():
    url = "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a"
    expected = "https://sip.lex.pl/apimobile/document/16903658?documentConfigurationId=lawJournal&unitId=art%2819%28a%29%29"
    assert transform_lex_url(url) == expected

def test_transform_lex_url_not_lex():
    url = "https://example.com/some/path-123"
    assert transform_lex_url(url) == url
