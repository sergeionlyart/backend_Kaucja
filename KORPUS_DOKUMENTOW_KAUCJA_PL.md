# KORPUS dokumentow Kaucja PL

_Read-only external corpus reference rebuilt from the current `legal_rag_runtime` snapshot._

## 1. Snapshot

- MongoDB: `mongodb://localhost:27017`
- Database: `legal_rag_runtime`
- Documents in full corpus: **931**
- Unique `doc_uid` values: **931**
- Operational slice documents: **925**
- Broken inventory exclusions: **6**
- Operational slice excludes only the 6 intentionally broken inventory records; the full reference below still lists canonical, alias and excluded records for traceability.

## 2. Status Distribution

| status | count |
| --- | ---: |
| `canonical` | 18 |
| `active` | 876 |
| `optional` | 11 |
| `alias` | 12 |
| `excluded` | 12 |
| `article_node` | 2 |

## 3. Kind Distribution

| document_kind | count |
| --- | ---: |
| `STATUTE` | 9 |
| `EU_ACT` | 7 |
| `GUIDANCE` | 6 |
| `COMMENTARY` | 1 |
| `STATUTE_REF` | 2 |
| `CASELAW` | 906 |

## 4. Source-System Distribution

| source_system | count |
| --- | ---: |
| `saos_pl` | 886 |
| `eurlex_eu` | 13 |
| `sn_pl` | 10 |
| `eli_pl` | 5 |
| `curia_eu` | 4 |
| `courts_pl` | 3 |
| `lex_pl` | 3 |
| `uokik_pl` | 3 |
| `isap_pl` | 2 |
| `prawo_pl` | 1 |
| `unknown` | 1 |

## 5. Broken Inventory Records

These records remain `excluded` / `INVENTORY_ONLY`, have broken checksum and/or artifact paths, and do not enter the operational slice.

- `eurlex_eu:urlsha:8f4d90b5081ec765` — Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts | reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.
- `curia_eu:urlsha:556c3aa0fb85f92e` — Curia fact sheet on unfair terms | reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.
- `eurlex_eu:urlsha:27e3506c61c42585` — EUR-Lex document celex:32019H1128(01) | reason: Broken imported artifact retained for inventory only. Reasons: invalid checksum sentinel; synthetic storage_uri.
- `eurlex_eu:urlsha:86a3a115b4b0e267` — EUR-Lex document celex:62008CJ0243 | reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.
- `eurlex_eu:urlsha:3cc91aee0436279b` — EUR-Lex document celex:62011CJ0415 | reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.
- `eurlex_eu:urlsha:51fd4eed44abc101` — EUR-Lex document celex:62019CJ0725 | reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

## 6. Corpus Reference

### `STATUTE` (9)

#### `eli_pl` (5)

##### `eli_pl:DU/1964/296` — Kodeks postepowania cywilnego

- status: `canonical`
- document_kind: `STATUTE`
- legal_role: `PROCESS_NORM`
- source_system: `eli_pl`
- source_tier: `official`
- title_short: Kodeks postepowania cywilnego
- summary_1line: Normative corpus record: Kodeks postepowania cywilnego.
- external_id: eli:DU/1964/296
- source_url: https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf
- normalized_source_url: https://eli.gov.pl/api/acts/DU/1964/296/text/U/D19640296Lj.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_ingest/corpus/docs/eli_pl:DU/1964/296/raw/cd8d9d567c8d69cde01203524dad9179a515b0a63de5384267133d931f66e5b7/original.bin

##### `eli_pl:DU/2005/1398` — Ustawa o kosztach sadowych w sprawach cywilnych

- status: `canonical`
- document_kind: `STATUTE`
- legal_role: `PROCESS_NORM`
- source_system: `eli_pl`
- source_tier: `official`
- title_short: Ustawa o kosztach sadowych
- summary_1line: Normative corpus record: Ustawa o kosztach sadowych.
- external_id: eli:DU/2005/1398
- source_url: https://eli.gov.pl/api/acts/DU/2005/1398/text/U/D20051398Lj.pdf
- normalized_source_url: https://eli.gov.pl/api/acts/DU/2005/1398/text/U/D20051398Lj.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_ingest/corpus/docs/eli_pl:DU/2005/1398/raw/426d3df24f61ef6c3b798ddc0817b80c75e517be14bf4ae690ec8b49c9f920b2/original.bin

##### `eli_pl:DU/2007/331` — Ustawa o ochronie konkurencji i konsumentow

- status: `canonical`
- document_kind: `STATUTE`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `eli_pl`
- source_tier: `official`
- title_short: Ustawa o ochronie konkurencji i konsumentow
- summary_1line: Normative corpus record: Ustawa o ochronie konkurencji i konsumentow.
- external_id: eli:DU/2007/331
- source_url: https://eli.gov.pl/api/acts/DU/2007/331/text/U/D20070331Lj.pdf
- normalized_source_url: https://eli.gov.pl/api/acts/DU/2007/331/text/U/D20070331Lj.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_ingest/corpus/docs/eli_pl:DU/2007/331/raw/defeb297eda0ce082a8f180a988f737421486740be3c4adcba0de253f343e57f/original.bin

##### `eli_pl:DU/2001/733` — Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego

- status: `canonical`
- document_kind: `STATUTE`
- legal_role: `DIRECT_NORM`
- source_system: `eli_pl`
- source_tier: `official`
- title_short: Ustawa o ochronie praw lokatorow
- summary_1line: Normative corpus record: Ustawa o ochronie praw lokatorow.
- external_id: eli:DU/2001/733
- source_url: https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf
- normalized_source_url: https://eli.gov.pl/api/acts/DU/2001/733/text/U/D20010733Lj.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_ingest/corpus/docs/eli_pl:DU/2001/733/raw/605ff81b94c0d0d99caf4ab771506ff8821df84803d50d7bfa5d0324ef195380/original.bin
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `eli_pl:DU/2001/733`

##### `eli_pl:urlsha:8b1bb9b48a8ca9ec` — Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego

- status: `alias`
- document_kind: `STATUTE`
- legal_role: `DUPLICATE_ALIAS`
- source_system: `eli_pl`
- source_tier: `official`
- title_short: Ustawa o ochronie praw lokatorow
- summary_1line: Alias record for Ustawa o ochronie praw lokatorow; refer to eli_pl:DU/2001/733 for operational use.
- external_id: eli:DU/2001/733
- source_url: https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf
- normalized_source_url: https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eli_pl:urlsha:8b1bb9b48a8ca9ec/raw/01bfc26482f1b6b69fdc177a8c9c023d729ff1964053e45d29949bef94e2e76c/original.bin
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `eli_pl:DU/2001/733`
- canonical_doc_uid: `eli_pl:DU/2001/733`
- superseded_by: `eli_pl:DU/2001/733`

#### `isap_pl` (2)

##### `isap_pl:WDU19640160093` — Kodeks cywilny

- status: `canonical`
- document_kind: `STATUTE`
- legal_role: `DIRECT_NORM`
- source_system: `isap_pl`
- source_tier: `official`
- title_short: Kodeks cywilny
- summary_1line: Normative corpus record: Kodeks cywilny.
- external_id: isap:WDU19640160093
- source_url: https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf
- normalized_source_url: https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf
- storage_uri: artifacts_dev/docs/isap_pl:WDU19640160093/raw/9e2f81d59c774bf17b0cd7917c0320abd05ba2a7307bf648d93d37e433be9baa/original.bin
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `isap_pl:WDU19640160093`

##### `isap_pl:urlsha:444655e6a3a3aef1` — Kodeks cywilny

- status: `alias`
- document_kind: `STATUTE`
- legal_role: `DUPLICATE_ALIAS`
- source_system: `isap_pl`
- source_tier: `official`
- title_short: Kodeks cywilny
- summary_1line: Alias record for Kodeks cywilny; refer to isap_pl:WDU19640160093 for operational use.
- external_id: isap:WDU19640160093
- source_url: https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf
- normalized_source_url: https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/isap_pl:urlsha:444655e6a3a3aef1/raw/9e2f81d59c774bf17b0cd7917c0320abd05ba2a7307bf648d93d37e433be9baa/original.bin
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `isap_pl:WDU19640160093`
- canonical_doc_uid: `isap_pl:WDU19640160093`
- superseded_by: `isap_pl:WDU19640160093`

#### `lex_pl` (1)

##### `lex_pl:urlsha:2c175d980032d2be` — Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego

- status: `alias`
- document_kind: `STATUTE`
- legal_role: `SECONDARY_SOURCE`
- source_system: `lex_pl`
- source_tier: `commercial_secondary`
- title_short: Ustawa o ochronie praw lokatorow
- summary_1line: Alias record for Ustawa o ochronie praw lokatorow; refer to eli_pl:DU/2001/733 for operational use.
- external_id: lex:16903658
- source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658
- normalized_source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/lex_pl:urlsha:2c175d980032d2be/raw/658f31cdf959b39b6e79ff69af730d082a31be576895f1f6b009fa950a0409ad/original.bin
- canonical_doc_uid: `eli_pl:DU/2001/733`
- superseded_by: `eli_pl:DU/2001/733`

#### `unknown` (1)

##### `unknown:urlsha:4307a0f3b0cab777` — Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorow, mieszkaniowym zasobie gminy i o zmianie Kodeksu cywilnego

- status: `alias`
- document_kind: `STATUTE`
- legal_role: `SECONDARY_SOURCE`
- source_system: `unknown`
- source_tier: `official`
- title_short: Ustawa o ochronie praw lokatorow
- summary_1line: Alias record for Ustawa o ochronie praw lokatorow; refer to eli_pl:DU/2001/733 for operational use.
- external_id: eli:DU/2001/733
- source_url: https://dziennikustaw.gov.pl/DU/2001/733
- normalized_source_url: https://dziennikustaw.gov.pl/DU/2001/733
- storage_uri: artifacts_dev/docs/unknown:urlsha:4307a0f3b0cab777/raw/46d1c6109d731fe0d46830f64dd62accd895d7f8d2b27ae61469beeff0978126/original.bin
- canonical_doc_uid: `eli_pl:DU/2001/733`
- superseded_by: `eli_pl:DU/2001/733`

### `EU_ACT` (7)

#### `eurlex_eu` (7)

##### `eurlex_eu:dir/1993/13/oj/eng` — Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts

- status: `canonical`
- document_kind: `EU_ACT`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Directive 93/13/EEC
- summary_1line: Normative corpus record: Directive 93/13/EEC.
- external_id: eli:dir/1993/13/oj/eng
- source_url: https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng
- normalized_source_url: https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:dir/1993/13/oj/eng/raw/32d7e5f06d35241d02cbd1a2440a2e37d03eabf4a478ba944794012bc0c1565a/original.bin
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `eurlex_eu:dir/1993/13/oj/eng`

##### `eurlex_eu:urlsha:28e0daf274cba11a` — Regulation (EC) No 1896/2006

- status: `optional`
- document_kind: `EU_ACT`
- legal_role: `EU_CROSS_BORDER_PROCEDURE`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Regulation (EC) No 1896/2006
- summary_1line: Normative corpus record: Regulation (EC) No 1896/2006.
- external_id: eli:reg/2006/1896/oj/eng
- source_url: https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng
- normalized_source_url: https://eur-lex.europa.eu/eli/reg/2006/1896/oj/eng
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:urlsha:28e0daf274cba11a/raw/7b033c508862f743c3d47713b6e890e2f66992bdd4456d423c9f52b2cef791dd/original.bin

##### `eurlex_eu:urlsha:6926cb298a9d475c` — Regulation (EC) No 805/2004

- status: `optional`
- document_kind: `EU_ACT`
- legal_role: `EU_CROSS_BORDER_PROCEDURE`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Regulation (EC) No 805/2004
- summary_1line: Normative corpus record: Regulation (EC) No 805/2004.
- external_id: eli:reg/2004/805/oj/eng
- source_url: https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng
- normalized_source_url: https://eur-lex.europa.eu/eli/reg/2004/805/oj/eng
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:urlsha:6926cb298a9d475c/raw/bd872562c00925607e91245e50f5db92380b6644dadb19dd3361741ece6be44f/original.bin

##### `eurlex_eu:urlsha:3699a38071d24cc4` — Regulation (EC) No 861/2007

- status: `optional`
- document_kind: `EU_ACT`
- legal_role: `EU_CROSS_BORDER_PROCEDURE`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Regulation (EC) No 861/2007
- summary_1line: Normative corpus record: Regulation (EC) No 861/2007.
- external_id: eli:reg/2007/861/oj/eng
- source_url: https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng
- normalized_source_url: https://eur-lex.europa.eu/eli/reg/2007/861/oj/eng
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:urlsha:3699a38071d24cc4/raw/af525cebd7e3a4419c0e1bda9652fd132431b32a3dfff615528649357a943d2a/original.bin

##### `eurlex_eu:http://data.europa.eu/eli/dir/1993/13/oj` — Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts

- status: `alias`
- document_kind: `EU_ACT`
- legal_role: `SECONDARY_SOURCE`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Directive 93/13/EEC
- summary_1line: Alias record for Directive 93/13/EEC; refer to eurlex_eu:dir/1993/13/oj/eng for operational use.
- external_id: eli:dir/1993/13/oj/eng
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31993L0013
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31993L0013
- storage_uri: artifacts_dev/docs/eurlex_eu:http://data.europa.eu/eli/dir/1993/13/oj/raw/090dd11b649f61bbc0ef62b9069d9bb0f9a0152536e2e622be8ca7254a135e6f/original.bin
- canonical_doc_uid: `eurlex_eu:dir/1993/13/oj/eng`
- superseded_by: `eurlex_eu:dir/1993/13/oj/eng`

##### `eurlex_eu:urlsha:7246ba2d89b3c7ed` — Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts

- status: `alias`
- document_kind: `EU_ACT`
- legal_role: `LEGACY_MIRROR`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Directive 93/13/EEC
- summary_1line: Alias record for Directive 93/13/EEC; refer to eurlex_eu:dir/1993/13/oj/eng for operational use.
- external_id: celex:31993L0013
- source_url: https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:31993L0013:en:HTML
- normalized_source_url: https://eur-lex.europa.eu/LexUriServ/LexUriServ.do?uri=CELEX:31993L0013:en:HTML
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:urlsha:7246ba2d89b3c7ed/raw/b4724d6c794bcd156f5f334a2435c653860ee1e1dffef4a572167354c5fcafb4/original.bin
- canonical_doc_uid: `eurlex_eu:dir/1993/13/oj/eng`
- superseded_by: `eurlex_eu:dir/1993/13/oj/eng`

##### `eurlex_eu:urlsha:8f4d90b5081ec765` — Council Directive 93/13/EEC of 5 April 1993 on unfair terms in consumer contracts

- status: `excluded`
- document_kind: `EU_ACT`
- legal_role: `INVENTORY_ONLY`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Directive 93/13/EEC
- summary_1line: Excluded inventory record retained for traceability: Directive 93/13/EEC.
- external_id: eli:dir/1993/13/oj/eng
- source_url: https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng
- normalized_source_url: https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng
- storage_uri: docs/eurlex_eu:urlsha:8f4d90b5081ec765/raw/ERROR/original.bin
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `eurlex_eu:dir/1993/13/oj/eng`
- canonical_doc_uid: `eurlex_eu:dir/1993/13/oj/eng`
- superseded_by: `eurlex_eu:dir/1993/13/oj/eng`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

### `GUIDANCE` (6)

#### `eurlex_eu` (3)

##### `eurlex_eu:urlsha:252f802534879b95` — Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC

- status: `canonical`
- document_kind: `GUIDANCE`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC
- summary_1line: Corpus record: Commission Notice - Guidance on the interpretation and application of Directive 93/13/EEC.
- external_id: celex:52019XC0927(01)
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?from=FR&uri=CELEX:52019XC0927(01)
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/eurlex_eu:urlsha:252f802534879b95/raw/e512d4a9af3ffbe883ac204406461094a6560fa23b5b1d3d7631fc7537f5f5ce/original.bin

##### `eurlex_eu:urlsha:2024e4eb39e6964c` — Official Journal C 380/2019

- status: `active`
- document_kind: `GUIDANCE`
- legal_role: `GUIDANCE`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: Official Journal C 380/2019
- summary_1line: Corpus record: Official Journal C 380/2019.
- external_id: eurlex_eu:urlsha:2024e4eb39e6964c
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:C:2019:380:FULL
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:C:2019:380:FULL
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-guide-20260306T191700Z/docs/eurlex_eu:urlsha:2024e4eb39e6964c/raw/13fa531c055c6d7c13a2f1e0debc2db730c17f98bd3a301e26b2746a289a75e2/original.bin

##### `eurlex_eu:urlsha:27e3506c61c42585` — EUR-Lex document celex:32019H1128(01)

- status: `excluded`
- document_kind: `GUIDANCE`
- legal_role: `INVENTORY_ONLY`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: EUR-Lex document celex:32019H1128(01)
- summary_1line: Excluded inventory record retained for traceability: EUR-Lex document celex:32019H1128(01).
- external_id: celex:32019H1128(01)
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019H1128(01)
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019H1128(01)
- storage_uri: document_sources:eurlex_eu:urlsha:27e3506c61c42585:ERROR
- superseded_by: `inventory_only`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: invalid checksum sentinel; synthetic storage_uri.

#### `uokik_pl` (2)

##### `uokik_pl:urlsha:c506ff470f4740ad` — Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK)

- status: `canonical`
- document_kind: `GUIDANCE`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `uokik_pl`
- source_tier: `official`
- title_short: Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK)
- summary_1line: Corpus record: Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK).
- external_id: uokik:RKR-37/2013
- source_url: https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf
- normalized_source_url: https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/uokik_pl:urlsha:c506ff470f4740ad/raw/21453041e80a68f3484bd319ab8c9173e8e1a17d62be356176183e89b667044d/original.bin

##### `uokik_pl:urlsha:054662ca9a699d16` — UOKiK Niedozwolone klauzule

- status: `canonical`
- document_kind: `GUIDANCE`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `uokik_pl`
- source_tier: `official`
- title_short: UOKiK Niedozwolone klauzule
- summary_1line: Corpus record: UOKiK Niedozwolone klauzule.
- external_id: uokik:niedozwolone-klauzule
- source_url: https://uokik.gov.pl/niedozwolone-klauzule
- normalized_source_url: https://uokik.gov.pl/niedozwolone-klauzule
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/uokik_pl:urlsha:054662ca9a699d16/raw/e6a6f3a50ef0d6118f4e2ac25473f88c7a9d25083315bd092d9fb56f7a39f809/original.bin

#### `curia_eu` (1)

##### `curia_eu:urlsha:556c3aa0fb85f92e` — Curia fact sheet on unfair terms

- status: `excluded`
- document_kind: `GUIDANCE`
- legal_role: `INVENTORY_ONLY`
- source_system: `curia_eu`
- source_tier: `official`
- title_short: Curia fact sheet on unfair terms
- summary_1line: Excluded inventory record retained for traceability: Curia fact sheet on unfair terms.
- external_id: curia:jcms:p1_4220451
- source_url: https://curia.europa.eu/jcms/jcms/p1_4220451/en/
- normalized_source_url: https://curia.europa.eu/jcms/jcms/p1_4220451/en/
- storage_uri: docs/curia_eu:urlsha:556c3aa0fb85f92e/raw/ERROR/original.bin
- superseded_by: `inventory_only`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

### `COMMENTARY` (1)

#### `prawo_pl` (1)

##### `prawo_pl:urlsha:7315b25566b744a4` — Prawo.pl commentary on abusive clauses in lease contracts

- status: `optional`
- document_kind: `COMMENTARY`
- legal_role: `COMMENTARY`
- source_system: `prawo_pl`
- source_tier: `commentary`
- title_short: Prawo.pl commentary on abusive clauses in lease contracts
- summary_1line: Corpus record: Prawo.pl commentary on abusive clauses in lease contracts.
- external_id: prawo:510151
- source_url: https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-skutki-ochrona-lokatora%2C510151.html
- normalized_source_url: https://www.prawo.pl/student/niedozwolone-klauzule-w-umowach-najmu-skutki-ochrona-lokatora%2C510151.html
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/prawo_pl:urlsha:7315b25566b744a4/raw/4f7649d3e048b3db4110acf5de50ce84e36b23355b88a094dc22711436c0ef26/original.bin

### `STATUTE_REF` (2)

#### `lex_pl` (2)

##### `lex_pl:urlsha:c31ee8071848130d` — Art. 118 Kodeksu cywilnego

- status: `article_node`
- document_kind: `STATUTE_REF`
- legal_role: `ARTICLE_NODE`
- source_system: `lex_pl`
- source_tier: `commercial_secondary`
- title_short: lex:118
- summary_1line: Corpus record: lex:118.
- external_id: lex:118
- source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118
- normalized_source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/lex_pl:urlsha:c31ee8071848130d/raw/a32699d60020d2ee98105ff0531182d25d23039263e87bb1957b2e3e1c60961c/original.bin

##### `lex_pl:urlsha:4f0332a0f08cee51` — Art. 19a ustawy o ochronie praw lokatorow

- status: `article_node`
- document_kind: `STATUTE_REF`
- legal_role: `ARTICLE_NODE`
- source_system: `lex_pl`
- source_tier: `commercial_secondary`
- title_short: lex:16903658:art-19-a
- summary_1line: Corpus record: lex:16903658:art-19-a.
- external_id: lex:16903658:art-19-a
- source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a
- normalized_source_url: https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/lex_pl:urlsha:4f0332a0f08cee51/raw/484a4cf303021688299ab291d20acaaf49fb59cbe6c3cd8bbbc0690d5827f43a/original.bin

### `CASELAW` (906)

#### `saos_pl` (886)

##### `saos_pl:346698` — Wyrok I C 106/17

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `FACTUAL_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 106/17
- summary_1line: Caselaw corpus record: I C 106/17.
- external_id: saos:346698
- source_url: https://www.saos.org.pl/judgments/346698
- normalized_source_url: https://www.saos.org.pl/judgments/346698
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:346698/raw/2d17c759da877e9283b0395da4f3865e778018c7bf1daaf65c094d7301211819/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_346698`

##### `saos_pl:279345` — Wyrok I C 743/16

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `FACTUAL_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 743/16
- summary_1line: Caselaw corpus record: I C 743/16.
- external_id: saos:279345
- source_url: https://www.saos.org.pl/judgments/279345
- normalized_source_url: https://www.saos.org.pl/judgments/279345
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:279345/raw/2c743a8f5827912ba25b7bfb9e09ae3e60da3828245629ebb0d220d0e6052f01/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_279345`

##### `saos_pl:171957` — Wyrok II Ca 886/14

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `FACTUAL_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 886/14
- summary_1line: Caselaw corpus record: II CA 886/14.
- external_id: saos:171957
- source_url: https://www.saos.org.pl/judgments/171957
- normalized_source_url: https://www.saos.org.pl/judgments/171957
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:171957/raw/4b1996ce85325e8809211f840016fe18d358044646181eb8cd4763f9fdb25603/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171957`

##### `saos_pl:505310` — Wyrok III C 224/22

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `FACTUAL_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 224/22
- summary_1line: Caselaw corpus record: III C 224/22.
- external_id: saos:505310
- source_url: https://www.saos.org.pl/judgments/505310
- normalized_source_url: https://www.saos.org.pl/judgments/505310
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:505310/raw/e7d1798624491344047278280cb6f6511627ecdf429010466d8269b362e33310/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_505310`

##### `saos_pl:205996` — Wyrok TK K 33/99

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `LEADING_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: K 33/99
- summary_1line: Caselaw corpus record: K 33/99.
- external_id: saos:205996
- source_url: https://www.saos.org.pl/judgments/205996
- normalized_source_url: https://www.saos.org.pl/judgments/205996
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:205996/raw/177c0d2880f3e9acfa9129e271bd1f6105f61b4a66949e5d01cca77e663ca15b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_205996`

##### `saos_pl:472812` — Wyrok VI C 837/21

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `FACTUAL_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 837/21
- summary_1line: Caselaw corpus record: VI C 837/21.
- external_id: saos:472812
- source_url: https://www.saos.org.pl/judgments/472812
- normalized_source_url: https://www.saos.org.pl/judgments/472812
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:472812/raw/bee18ee7c0aacceb292664a699a7e2d4f178cb9953fa52a24965f3c77c1e97e7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_472812`

##### `saos_pl:15890` — DECISION I ACz 124/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACZ 124/13
- summary_1line: Caselaw corpus record: I ACZ 124/13.
- external_id: saos:15890
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:15890/raw/a4c1a67cc41c67da63510edadbd03cabb78339c6455338efe1af2ed7d7cb98c5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_15890`

##### `saos_pl:139118` — DECISION I ACz 653/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACZ 653/13
- summary_1line: Caselaw corpus record: I ACZ 653/13.
- external_id: saos:139118
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:139118/raw/a085b9bde89d0d55feafa93340795f57b10dc28e44988acfb40b298eb52e5189/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_139118`

##### `saos_pl:145699` — DECISION I C 1688/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1688/13
- summary_1line: Caselaw corpus record: I C 1688/13.
- external_id: saos:145699
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:145699/raw/0dd85a1efb5e0735e0c3775027c8fd5645ba0dcb023ae38c753641ad80c06ee6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_145699`

##### `saos_pl:467230` — DECISION I C 862/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 862/12
- summary_1line: Caselaw corpus record: I C 862/12.
- external_id: saos:467230
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:467230/raw/66a0a24837f750168ba3eae7955b0ffc11bfcef6f6504f50867802d71fa4921b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_467230`

##### `saos_pl:467231` — DECISION I C 862/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 862/12
- summary_1line: Caselaw corpus record: I C 862/12.
- external_id: saos:467231
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:467231/raw/fd91d8dbd32408875f1372d5ed7437b31d254b39164f6fd6377dd32eae208fab/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_467231`

##### `saos_pl:63836` — DECISION I Ca 222/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 222/14
- summary_1line: Caselaw corpus record: I CA 222/14.
- external_id: saos:63836
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:63836/raw/a82a79e469344ceca4a4843ff27195253ee71e624559eafb9c9f9ae5a615df2b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_63836`

##### `saos_pl:252474` — DECISION I Ns 1151/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 1151/13
- summary_1line: Caselaw corpus record: I NS 1151/13.
- external_id: saos:252474
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:252474/raw/e76069ae0d2ae8d3aedbd43db597640bc6c9f7427c162a70e454d30908f395af/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_252474`

##### `saos_pl:384919` — DECISION I Ns 161/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 161/16
- summary_1line: Caselaw corpus record: I NS 161/16.
- external_id: saos:384919
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:384919/raw/134071343b1c7994a1f071fe9d6ca0b5196974a33904c620ceb2d6d20a0ebe13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_384919`

##### `saos_pl:155664` — DECISION I Ns 2178/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 2178/12
- summary_1line: Caselaw corpus record: I NS 2178/12.
- external_id: saos:155664
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155664/raw/2c01ab9747d197fe965c27aaf7211a337aca1d284aee343bce7766de6aaaef66/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155664`

##### `saos_pl:412298` — DECISION I Ns 341/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 341/19
- summary_1line: Caselaw corpus record: I NS 341/19.
- external_id: saos:412298
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:412298/raw/4d55e7fde5d5fa298cb83fadc66879171c343a717381b92e0585ebe2a41500df/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_412298`

##### `saos_pl:275504` — DECISION I Ns 614/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 614/13
- summary_1line: Caselaw corpus record: I NS 614/13.
- external_id: saos:275504
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:275504/raw/d850534d5802b11ab753a849b5551072e1bd05b286d4a0605265132a1be599d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_275504`

##### `saos_pl:477867` — DECISION I Ns 693/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 693/19
- summary_1line: Caselaw corpus record: I NS 693/19.
- external_id: saos:477867
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:477867/raw/f824256db8684b21d2acb51c5d26fd15ae65e388defdae85726f3202f2b684cc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_477867`

##### `saos_pl:153265` — DECISION I Ns 889/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 889/14
- summary_1line: Caselaw corpus record: I NS 889/14.
- external_id: saos:153265
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153265/raw/f54302b05623de7ccf9cdd890b956b9425d8695559a038bee9ffee1b140f95ac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153265`

##### `saos_pl:423229` — DECISION I Ns 925/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 925/14
- summary_1line: Caselaw corpus record: I NS 925/14.
- external_id: saos:423229
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:423229/raw/9af854b90c2cbd847bfc6cfa1ec4c7ed4d1cca67d2c9322e4812d03b3d414e65/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_423229`

##### `saos_pl:450295` — DECISION I Ns 959/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 959/11
- summary_1line: Caselaw corpus record: I NS 959/11.
- external_id: saos:450295
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:450295/raw/4b9a2d53146f954c35484f4d6b74576ea42d25ab54630e185fad3281999adf7c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_450295`

##### `saos_pl:426985` — DECISION II C 570/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 570/19
- summary_1line: Caselaw corpus record: II C 570/19.
- external_id: saos:426985
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:426985/raw/d86b0d0d0cdbff2685c1224f73a360e2e30dd07e762bd3e64d0bf2e54db44e28/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_426985`

##### `saos_pl:298117` — DECISION II Ca 1366/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1366/14
- summary_1line: Caselaw corpus record: II CA 1366/14.
- external_id: saos:298117
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:298117/raw/58363ced4cd1dd255464999dc47cf00676076323c35e597d3b2918d8e54baba1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_298117`

##### `saos_pl:305224` — DECISION II Ca 1680/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1680/15
- summary_1line: Caselaw corpus record: II CA 1680/15.
- external_id: saos:305224
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305224/raw/7d1ce0fa88829fd091bd39a92746ddea98c81971b06b5f42dc43f942d123fd69/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305224`

##### `saos_pl:315321` — DECISION II Ca 213/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 213/17
- summary_1line: Caselaw corpus record: II CA 213/17.
- external_id: saos:315321
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:315321/raw/3d340de88a574ea8465fe7edca312e1b7da0032a7adab9132d1e3e35bfa27f7f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_315321`

##### `saos_pl:270320` — DECISION II Ca 2585/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 2585/15
- summary_1line: Caselaw corpus record: II CA 2585/15.
- external_id: saos:270320
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:270320/raw/63b178e96ee4539ec715fa0d003ccc871c9937a84a583602dc89859af2433ee2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_270320`

##### `saos_pl:475718` — DECISION II Ca 268/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 268/22
- summary_1line: Caselaw corpus record: II CA 268/22.
- external_id: saos:475718
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:475718/raw/f69a39d2d05457802cd60a60005d88478902d7920e98b4c1e9cf70febdfed6ae/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_475718`

##### `saos_pl:296738` — DECISION II Ca 313/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 313/14
- summary_1line: Caselaw corpus record: II CA 313/14.
- external_id: saos:296738
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:296738/raw/0dbd9f6fd6d80c503071ff5ffdf0688b5e220ea0ee89c3a1acc13bc9aaf98bbd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_296738`

##### `saos_pl:293644` — DECISION II Ca 559/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 559/13
- summary_1line: Caselaw corpus record: II CA 559/13.
- external_id: saos:293644
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:293644/raw/f2baf19848311bdc1a35ffaef3c49b8f4a0891f09658ced97d3bf2d88d085e2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_293644`

##### `saos_pl:37490` — DECISION II Ca 668/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 668/12
- summary_1line: Caselaw corpus record: II CA 668/12.
- external_id: saos:37490
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:37490/raw/39b514d276f60dddf59dd9e9a47c2a9ea8593b7f033049b64d3d01876915a0d2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_37490`

##### `saos_pl:296829` — DECISION II Ca 683/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 683/15
- summary_1line: Caselaw corpus record: II CA 683/15.
- external_id: saos:296829
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:296829/raw/53c8e4450fa6f39f9af0878787efa86fe12c33a13737661514a3d50dde563abe/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_296829`

##### `saos_pl:248226` — DECISION II Ca 712/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 712/14
- summary_1line: Caselaw corpus record: II CA 712/14.
- external_id: saos:248226
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:248226/raw/495d020ecf646149e3a2b62fd0ca7308514ab774cb47fa95ad580223d9a93c76/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_248226`

##### `saos_pl:46729` — DECISION II Ca 773/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 773/13
- summary_1line: Caselaw corpus record: II CA 773/13.
- external_id: saos:46729
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:46729/raw/946d13968ae725ad4703647ccb6ec436aacc64cf26e5e822ee117c94ef7c10e4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_46729`

##### `saos_pl:346611` — DECISION II Ns 1488/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II NS 1488/12
- summary_1line: Caselaw corpus record: II NS 1488/12.
- external_id: saos:346611
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:346611/raw/271b722da7a9c3f5990a8975288ea7188f65345eb3ffa33654f75fdb8a991ef1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_346611`

##### `saos_pl:307420` — DECISION II Ns 2228/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II NS 2228/16
- summary_1line: Caselaw corpus record: II NS 2228/16.
- external_id: saos:307420
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:307420/raw/3b691df2fe0d031458045c1c87725b3ad64205356d6a4b84c52faf001bdb8485/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_307420`

##### `saos_pl:305604` — DECISION II Ns 2578/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II NS 2578/16
- summary_1line: Caselaw corpus record: II NS 2578/16.
- external_id: saos:305604
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305604/raw/08ba1c8aa52e702a5bb32c1c6017ecec63fb72053504d5ce905949701b3c3363/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305604`

##### `saos_pl:260151` — DECISION II Ns 374/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II NS 374/14
- summary_1line: Caselaw corpus record: II NS 374/14.
- external_id: saos:260151
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:260151/raw/163298ad147a60eb58b3abaea18530e6209feff6524421c1e1dba39f611854e3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_260151`

##### `saos_pl:370005` — DECISION II Ns 985/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II NS 985/16
- summary_1line: Caselaw corpus record: II NS 985/16.
- external_id: saos:370005
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:370005/raw/25a1562f88a7ef35c5be06370f0309d56c5abdd7645ecf0f69b43352468c5891/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_370005`

##### `saos_pl:222559` — DECISION III C 1024/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 1024/13
- summary_1line: Caselaw corpus record: III C 1024/13.
- external_id: saos:222559
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222559/raw/f83e17970bced0e5a7d60cbf51b2e64b907c67381b89435f0f56840bc328f05f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222559`

##### `saos_pl:470853` — DECISION III C 171/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 171/16
- summary_1line: Caselaw corpus record: III C 171/16.
- external_id: saos:470853
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:470853/raw/33f04a02fcf55ec1e35330b922b15db7c5e757a762ae33b93c81ba695f8aeb03/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_470853`

##### `saos_pl:170193` — DECISION III C 376/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 376/13
- summary_1line: Caselaw corpus record: III C 376/13.
- external_id: saos:170193
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:170193/raw/4458382878f53f77a1b57921f237c3c126a0d76580ca87dff614677332c3b20d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_170193`

##### `saos_pl:332648` — DECISION III Ca 1438/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1438/16
- summary_1line: Caselaw corpus record: III CA 1438/16.
- external_id: saos:332648
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:332648/raw/d08142e9fe37a3c33b04547cbece407e4e708549c9773c32ac7fc2ab750e81c5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_332648`

##### `saos_pl:185408` — DECISION III Ca 717/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 717/14
- summary_1line: Caselaw corpus record: III CA 717/14.
- external_id: saos:185408
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:185408/raw/583d707a85eabfc1cb2e829218d7b634c6563f2de4f1f13969bfb58f33a46f13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_185408`

##### `saos_pl:260836` — DECISION III Ca 896/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 896/16
- summary_1line: Caselaw corpus record: III CA 896/16.
- external_id: saos:260836
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:260836/raw/fd8fff8acb43b350753eed9c76a5b62621b898250ca4e0d0ad34c985609686b9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_260836`

##### `saos_pl:185546` — DECISION III Cz 1033/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CZ 1033/15
- summary_1line: Caselaw corpus record: III CZ 1033/15.
- external_id: saos:185546
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:185546/raw/fbd9567462044315cc0be80a9c1cd1ddf22ef22f43eb20e6221f61351abf8b50/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_185546`

##### `saos_pl:227719` — DECISION III Ns 294/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III NS 294/14
- summary_1line: Caselaw corpus record: III NS 294/14.
- external_id: saos:227719
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:227719/raw/0ff013de560091d99361e5a31467e3b7b8a3bba8575f0b2df5983fe227e688f7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_227719`

##### `saos_pl:460171` — DECISION IV Ca 2307/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV CA 2307/19
- summary_1line: Caselaw corpus record: IV CA 2307/19.
- external_id: saos:460171
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:460171/raw/9420a2d051901cafb9c50482f6c1ed1268d3b905b6179806af7c72f8529bdf32/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_460171`

##### `saos_pl:467781` — DECISION IX Ca 1373/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 1373/21
- summary_1line: Caselaw corpus record: IX CA 1373/21.
- external_id: saos:467781
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:467781/raw/601e54aea655cb2efc1063eeaaa665078243742cbf85ba80cba1572794c84469/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_467781`

##### `saos_pl:351690` — DECISION IX Ca 186/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 186/18
- summary_1line: Caselaw corpus record: IX CA 186/18.
- external_id: saos:351690
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:351690/raw/c72ca6c3fa766684367d790ff944fdd6876dcba8b4974444e58ea23be73e2b2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_351690`

##### `saos_pl:153466` — DECISION IX Ca 949/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 949/14
- summary_1line: Caselaw corpus record: IX CA 949/14.
- external_id: saos:153466
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153466/raw/90bf4f288442508546469157a3ebcc2bca7a510650edace1da740a750336cb65/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153466`

##### `saos_pl:510813` — DECISION VI Ca 236/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI CA 236/22
- summary_1line: Caselaw corpus record: VI CA 236/22.
- external_id: saos:510813
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:510813/raw/4385e20cd441df8141e45bb5753da07e801386acd47442b0b9486e3c8ca9e022/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_510813`

##### `saos_pl:309817` — DECISION VI Ca 721/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI CA 721/17
- summary_1line: Caselaw corpus record: VI CA 721/17.
- external_id: saos:309817
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:309817/raw/df61e5a2079f06bb79d3427bf7cd21a00e5fdb444e949a2d8a98a2ac57192809/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_309817`

##### `saos_pl:357529` — DECISION VI Gz 212/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GZ 212/18
- summary_1line: Caselaw corpus record: VI GZ 212/18.
- external_id: saos:357529
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:357529/raw/4a3efecfc174714fe77ba60dbd9f976c892550d6978ba2bee93ae6fcb9576a0c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_357529`

##### `saos_pl:191749` — DECISION VIII Gz 183/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GZ 183/15
- summary_1line: Caselaw corpus record: VIII GZ 183/15.
- external_id: saos:191749
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:191749/raw/3abe2e91d454e7a36a0a2fd8084a6a9228c61e0046a9849f2ffe94c0b39f27ec/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_191749`

##### `saos_pl:65285` — DECISION VIII Ns 186/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII NS 186/11
- summary_1line: Caselaw corpus record: VIII NS 186/11.
- external_id: saos:65285
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:65285/raw/1a1553aa068887cd7ba4ed3d874afaca70e4b6b4468a1927c4d2e4ff7456cae4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_65285`

##### `saos_pl:43469` — DECISION XI Ns 71/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI NS 71/11
- summary_1line: Caselaw corpus record: XI NS 71/11.
- external_id: saos:43469
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:43469/raw/f216e63cf5077939622f17972d489a2f0172ddbe3f5ab83b9f5cb3da7f7f52bc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_43469`

##### `saos_pl:47666` — DECISION XV Ca 1211/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 1211/13
- summary_1line: Caselaw corpus record: XV CA 1211/13.
- external_id: saos:47666
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:47666/raw/d2932e344c393750e86c95a88b7910b85d4423544ca23f4fbfe82f7b794b1c9a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_47666`

##### `saos_pl:484503` — REASONS I C 1508/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1508/18
- summary_1line: Caselaw corpus record: I C 1508/18.
- external_id: saos:484503
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484503/raw/b8207192a21e2adae2f3594e6f1739c5836947c26b44526ce72bc2afe80a2f6d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484503`

##### `saos_pl:277320` — REASONS I C 162/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 162/16
- summary_1line: Caselaw corpus record: I C 162/16.
- external_id: saos:277320
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:277320/raw/8b13eae5bbb68b5591deee56cff1e87a8ea817fc13f9adf3563655387c28a8b8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_277320`

##### `saos_pl:171555` — REASONS I C 205/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 205/11
- summary_1line: Caselaw corpus record: I C 205/11.
- external_id: saos:171555
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171555/raw/5dc727e0a0048de417514203341e5ef1d1148cdb3e425950d7277dfe8e62b142/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171555`

##### `saos_pl:441458` — REASONS I C 285/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 285/17
- summary_1line: Caselaw corpus record: I C 285/17.
- external_id: saos:441458
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:441458/raw/0e3ae5b29951f485357bbe526a6f142c3d3c7e30d2a513f678e75418c3f164cd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_441458`

##### `saos_pl:361791` — REASONS I C 3438/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 3438/16
- summary_1line: Caselaw corpus record: I C 3438/16.
- external_id: saos:361791
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:361791/raw/273d1b63067e3d6b9ce5eb407fd1686238da4189fb4823cfc5c889c2853202f2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_361791`

##### `saos_pl:143737` — REASONS I C 480/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 480/13
- summary_1line: Caselaw corpus record: I C 480/13.
- external_id: saos:143737
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:143737/raw/135777158918f0f3f50f1d1e05cddc293f63adcb85e8d8be1290d56e00146b77/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_143737`

##### `saos_pl:143442` — REASONS I C 481/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 481/13
- summary_1line: Caselaw corpus record: I C 481/13.
- external_id: saos:143442
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:143442/raw/56bce32bbf7be8aaf34f9c44e4c82e7b00262cf41d5198ae8003bf4751695daf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_143442`

##### `saos_pl:212797` — REASONS I C 605/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 605/15
- summary_1line: Caselaw corpus record: I C 605/15.
- external_id: saos:212797
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:212797/raw/611d467dfd058f6c13c279c78a12de7a6aa661ea997840360bd7d7d264e70dad/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_212797`

##### `saos_pl:466203` — REASONS I C 96/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 96/22
- summary_1line: Caselaw corpus record: I C 96/22.
- external_id: saos:466203
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:466203/raw/d8993063115be37deac22bcd58b2d0d0c4820db523d770e56a8a42c89abb150b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_466203`

##### `saos_pl:60815` — REASONS I Ns 3/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 3/11
- summary_1line: Caselaw corpus record: I NS 3/11.
- external_id: saos:60815
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:60815/raw/d50ff59c1bf6ba2d279d8099eac72b5f306eae72d29300c7db1b0e6f1b12363b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_60815`

##### `saos_pl:220682` — REASONS I Ns 73/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 73/14
- summary_1line: Caselaw corpus record: I NS 73/14.
- external_id: saos:220682
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:220682/raw/5faaa513562e8554dc32552e60fcc741c40e24d2ac25cf4c9308920da47093d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_220682`

##### `saos_pl:526847` — REASONS II AKa 103/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 103/22
- summary_1line: Caselaw corpus record: II AKA 103/22.
- external_id: saos:526847
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:526847/raw/7f75182a6875348622817426571bcfbccc943fcafba38bad34d9c7c5fd5dcde3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_526847`

##### `saos_pl:485247` — REASONS II AKa 90/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 90/21
- summary_1line: Caselaw corpus record: II AKA 90/21.
- external_id: saos:485247
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:485247/raw/50ff4a80e0438969112ce89542a89682f27aada31a192e8219a6d2834bda673a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_485247`

##### `saos_pl:145906` — REASONS II C 1693/10 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 1693/10
- summary_1line: Caselaw corpus record: II C 1693/10.
- external_id: saos:145906
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:145906/raw/d68ed9607107b3f5f73bb6788721aeff9ae1f1cfa4a4b20413fd7448098929a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_145906`

##### `saos_pl:215208` — REASONS II C 1860/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 1860/14
- summary_1line: Caselaw corpus record: II C 1860/14.
- external_id: saos:215208
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:215208/raw/bdf044d1151e424e50c2f1987069fa43e8021e4757d433c77466537f6d070077/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_215208`

##### `saos_pl:177578` — REASONS II C 32/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 32/14
- summary_1line: Caselaw corpus record: II C 32/14.
- external_id: saos:177578
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:177578/raw/ea7442d577d19a76d13c7c86c10a4f0599c4af0e30d77cfe3d9b14e224e8bb00/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_177578`

##### `saos_pl:377814` — REASONS II C 563/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 563/17
- summary_1line: Caselaw corpus record: II C 563/17.
- external_id: saos:377814
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:377814/raw/0c6a4c31a57e30bc1d01f2f091f1678a2d9e3312c4fee4103f5014d15e8ea834/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_377814`

##### `saos_pl:175247` — REASONS II C 636/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 636/14
- summary_1line: Caselaw corpus record: II C 636/14.
- external_id: saos:175247
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:175247/raw/e7866657a5a109588d45b9595e711b7d535ef24a6edba32bd00f663eb38d2847/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_175247`

##### `saos_pl:487223` — REASONS II Ca 1428/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1428/22
- summary_1line: Caselaw corpus record: II CA 1428/22.
- external_id: saos:487223
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:487223/raw/b033c6aa9c3315d8b68e9c9668c40b93594a492e83c32ebb9c4f25e2b7b12e51/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487223`

##### `saos_pl:45409` — REASONS II Ca 446/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 446/13
- summary_1line: Caselaw corpus record: II CA 446/13.
- external_id: saos:45409
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:45409/raw/9b665a9bf6af6f3f966ff94c667b4277d058d150a619893949df691d9f36db78/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_45409`

##### `saos_pl:21290` — REASONS II Ca 448/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 448/13
- summary_1line: Caselaw corpus record: II CA 448/13.
- external_id: saos:21290
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:21290/raw/6a2fd108e2a394ef854a2bbae564f32fe96841d856d7d9e49891a64434e86b41/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_21290`

##### `saos_pl:240403` — REASONS II Ca 573/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 573/15
- summary_1line: Caselaw corpus record: II CA 573/15.
- external_id: saos:240403
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:240403/raw/67f62da14865e0aa174d85f500ba24cac7597d0666a02ffe7b8bd0d0f9be3b0a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_240403`

##### `saos_pl:516842` — REASONS II Ca 673/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 673/22
- summary_1line: Caselaw corpus record: II CA 673/22.
- external_id: saos:516842
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:516842/raw/094eadd1dcd9c17500bb4723a335c61a397464a5f05802de794c030098e27012/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_516842`

##### `saos_pl:172079` — REASONS II Ca 805/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 805/13
- summary_1line: Caselaw corpus record: II CA 805/13.
- external_id: saos:172079
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:172079/raw/c631e348e709aee30f35d6e006c8c0cca62ed3d34d492b2e6f6acddbe1c15d29/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_172079`

##### `saos_pl:169829` — REASONS II Ca 893/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 893/14
- summary_1line: Caselaw corpus record: II CA 893/14.
- external_id: saos:169829
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:169829/raw/4523f11a7fde30dcdbd659c2f832288f3ae8457b6271bd80f990480ff10585cd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_169829`

##### `saos_pl:59115` — REASONS II Ca 946/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 946/13
- summary_1line: Caselaw corpus record: II CA 946/13.
- external_id: saos:59115
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:59115/raw/bacfbc9b9c28803f4f1730c242823f34a8b9ae7cbeef3316a569b5d2b90becea/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_59115`

##### `saos_pl:444460` — REASONS III Ca 1176/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1176/20
- summary_1line: Caselaw corpus record: III CA 1176/20.
- external_id: saos:444460
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:444460/raw/0e28d492f5c48ace4390756ff679d97621d2d98fa22ccea47da3be3bd1cbca0e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_444460`

##### `saos_pl:42930` — REASONS III Ca 1195/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1195/13
- summary_1line: Caselaw corpus record: III CA 1195/13.
- external_id: saos:42930
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:42930/raw/456a0548bc1f1d05214ef0de1a8abb4ca2905f39d62ac6ab20bcd320258f202f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_42930`

##### `saos_pl:452709` — REASONS III Ca 1199/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1199/20
- summary_1line: Caselaw corpus record: III CA 1199/20.
- external_id: saos:452709
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:452709/raw/cae87d5acf6c7b740b8ad48c89d1ec8c2a1ffe357775af58ab228ff8d5b81dfa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_452709`

##### `saos_pl:261423` — REASONS III Ca 1236/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1236/16
- summary_1line: Caselaw corpus record: III CA 1236/16.
- external_id: saos:261423
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:261423/raw/3b42a0941092f52c5947e591f9c77c2a2363413db18fe4e12bbf3bd6d509a540/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_261423`

##### `saos_pl:205260` — REASONS III Ca 1246/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1246/15
- summary_1line: Caselaw corpus record: III CA 1246/15.
- external_id: saos:205260
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:205260/raw/278725ac54beef1ff43360900ad52f5cba8e0370ff0ef780dd0e67d8e5d879a6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_205260`

##### `saos_pl:45232` — REASONS III Ca 1248/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1248/13
- summary_1line: Caselaw corpus record: III CA 1248/13.
- external_id: saos:45232
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:45232/raw/d4173fb42380c962bd3bd02444d9af718f773ee2e11f09c07da386e8239bee9e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_45232`

##### `saos_pl:323742` — REASONS III Ca 1269/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1269/17
- summary_1line: Caselaw corpus record: III CA 1269/17.
- external_id: saos:323742
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:323742/raw/1308124d10b0dd77721b948b21213467698657ecd11bcab3bd81539e6e1b088f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_323742`

##### `saos_pl:194534` — REASONS III Ca 1306/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1306/15
- summary_1line: Caselaw corpus record: III CA 1306/15.
- external_id: saos:194534
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194534/raw/46856ccc23be7bb556669f86a8c74da915f414461c251787a45d845fe2877aee/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194534`

##### `saos_pl:476190` — REASONS III Ca 135/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 135/21
- summary_1line: Caselaw corpus record: III CA 135/21.
- external_id: saos:476190
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:476190/raw/9af460d9d0d04801a38e0ea7a003aa2762fbb026449142ada328d68e99952ad4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_476190`

##### `saos_pl:194592` — REASONS III Ca 1364/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1364/15
- summary_1line: Caselaw corpus record: III CA 1364/15.
- external_id: saos:194592
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194592/raw/4d61d01582276d3937de966181c061736d3d4e5a149866773aa06e7b5fd98641/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194592`

##### `saos_pl:174405` — REASONS III Ca 137/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 137/15
- summary_1line: Caselaw corpus record: III CA 137/15.
- external_id: saos:174405
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:174405/raw/0da13f15adb58c35f3ce1ffe0454f80917f78bf34af2a4f6adcd090339b87b21/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_174405`

##### `saos_pl:330573` — REASONS III Ca 1391/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1391/17
- summary_1line: Caselaw corpus record: III CA 1391/17.
- external_id: saos:330573
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:330573/raw/418f8d74f1fd5063c0249960bd9c1fc4e1187afd40cf3e2af6f73eb8501937cc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_330573`

##### `saos_pl:157500` — REASONS III Ca 1433/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1433/14
- summary_1line: Caselaw corpus record: III CA 1433/14.
- external_id: saos:157500
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:157500/raw/bd1a0f3b16c9595c5c04310d82f9e8d46bcb698003c431fb583ec521f3881ae7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_157500`

##### `saos_pl:272609` — REASONS III Ca 1456/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1456/16
- summary_1line: Caselaw corpus record: III CA 1456/16.
- external_id: saos:272609
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:272609/raw/48c47d7de5d1cca53c74eb35d56fa0bac8827522e01d6a4b2850a7b6123051c9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_272609`

##### `saos_pl:366152` — REASONS III Ca 1507/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1507/18
- summary_1line: Caselaw corpus record: III CA 1507/18.
- external_id: saos:366152
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:366152/raw/74cd6a7ff59f0f2b909e2332cf70c3fcfa1c75fa6305f9049aa656bd64cc1889/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_366152`

##### `saos_pl:378825` — REASONS III Ca 1594/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1594/18
- summary_1line: Caselaw corpus record: III CA 1594/18.
- external_id: saos:378825
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:378825/raw/47478fafff3aadc5c6161dd36272653b67665537ce0e3257a8f632698968d10c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_378825`

##### `saos_pl:276389` — REASONS III Ca 1595/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1595/16
- summary_1line: Caselaw corpus record: III CA 1595/16.
- external_id: saos:276389
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:276389/raw/ea01c639e7797b18f455221e392bda218628a7d5cf2fca588b04886c436afa70/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_276389`

##### `saos_pl:214395` — REASONS III Ca 1597/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1597/15
- summary_1line: Caselaw corpus record: III CA 1597/15.
- external_id: saos:214395
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:214395/raw/eee4230939d16a5470a6d08544bbb811564c9a1a7edc7dbaf35dbb037f7b4c4e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_214395`

##### `saos_pl:387613` — REASONS III Ca 1626/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1626/18
- summary_1line: Caselaw corpus record: III CA 1626/18.
- external_id: saos:387613
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:387613/raw/0f316066ebaeafacef5175f1bebca4e7db41875df0d05219abdfdf82ea6fac8f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_387613`

##### `saos_pl:56253` — REASONS III Ca 1633/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1633/13
- summary_1line: Caselaw corpus record: III CA 1633/13.
- external_id: saos:56253
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:56253/raw/7881fc7abb0fefbd916b8eaacf5de319f6d0cc4f8c361d56f4e5d8af7c457bd6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_56253`

##### `saos_pl:282274` — REASONS III Ca 1676/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1676/16
- summary_1line: Caselaw corpus record: III CA 1676/16.
- external_id: saos:282274
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:282274/raw/ee6a669549dc154e8225ed38ac484dc4f6e4fe96423e0ed545ce352595868f9f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_282274`

##### `saos_pl:385394` — REASONS III Ca 1707/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1707/18
- summary_1line: Caselaw corpus record: III CA 1707/18.
- external_id: saos:385394
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:385394/raw/c7e4bdd54316c3f6d1e889533257b1bf2ff7fd2db615fd2a795abfced521cc45/original.bin
- same_case_group_id: `same_case:iii_ca_1707_18`

##### `saos_pl:194706` — REASONS III Ca 1730/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1730/15
- summary_1line: Caselaw corpus record: III CA 1730/15.
- external_id: saos:194706
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194706/raw/f55a9fda65ab2519a9b19f930d3b16a7abc017ea14e7f24b4457d3f5e13e5686/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194706`

##### `saos_pl:196347` — REASONS III Ca 1798/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1798/15
- summary_1line: Caselaw corpus record: III CA 1798/15.
- external_id: saos:196347
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:196347/raw/b2bb5a928b87edfec53319286d174119ba09dea76a9bd4510010470b457b084a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_196347`

##### `saos_pl:505907` — REASONS III Ca 1848/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1848/21
- summary_1line: Caselaw corpus record: III CA 1848/21.
- external_id: saos:505907
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:505907/raw/9f922e7428b26d3ec1d4418d2f052eda38b237c94a69a06d3d11f39048e10bc2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_505907`

##### `saos_pl:191902` — REASONS III Ca 187/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 187/15
- summary_1line: Caselaw corpus record: III CA 187/15.
- external_id: saos:191902
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:191902/raw/b79826ad2094250ea9f431ea4d898215fa7de0c923b07581b7f6a3255ba450dc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_191902`

##### `saos_pl:369604` — REASONS III Ca 189/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 189/18
- summary_1line: Caselaw corpus record: III CA 189/18.
- external_id: saos:369604
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:369604/raw/e3845387afc3e3187cbb5bac511f7862638930bb5584bc13a99bd8366b52880f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_369604`

##### `saos_pl:151115` — REASONS III Ca 1895/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1895/14
- summary_1line: Caselaw corpus record: III CA 1895/14.
- external_id: saos:151115
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:151115/raw/4d1eadd2ae9b060f8e9d3b021d1b6e8b121b4859f20c409b5cded901339e2177/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_151115`

##### `saos_pl:286564` — REASONS III Ca 1946/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1946/16
- summary_1line: Caselaw corpus record: III CA 1946/16.
- external_id: saos:286564
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:286564/raw/5783fc94f3f34e8945e2c3bac459d57eca39b0047ffa6f380bb488a907a97237/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_286564`

##### `saos_pl:240424` — REASONS III Ca 209/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 209/16
- summary_1line: Caselaw corpus record: III CA 209/16.
- external_id: saos:240424
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:240424/raw/6796ccef9c19c2fd54681d81db51c0332f6731e16dd45d7326f8eb9d3b68de62/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_240424`

##### `saos_pl:424173` — REASONS III Ca 2315/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 2315/19
- summary_1line: Caselaw corpus record: III CA 2315/19.
- external_id: saos:424173
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:424173/raw/b33417c86dd78eb0feb5371f757f63f6e21ff6e37a29c0da3d3d8a2c5d1a65c8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_424173`

##### `saos_pl:506287` — REASONS III Ca 2428/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 2428/21
- summary_1line: Caselaw corpus record: III CA 2428/21.
- external_id: saos:506287
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:506287/raw/b6ed11906740847509b416fc7f80527c5ebbe575dcfb62732966bda1c0154f2c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_506287`

##### `saos_pl:506404` — REASONS III Ca 2594/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 2594/21
- summary_1line: Caselaw corpus record: III CA 2594/21.
- external_id: saos:506404
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:506404/raw/55886d94e78f05254990d071c88a1606d7092c61414aa3f1b981018440d62029/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_506404`

##### `saos_pl:460130` — REASONS III Ca 449/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 449/20
- summary_1line: Caselaw corpus record: III CA 449/20.
- external_id: saos:460130
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:460130/raw/548eed927d832ecab4b5ffeebb17b1067a750d02fe386038d0a51d437a8d1556/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_460130`

##### `saos_pl:185177` — REASONS III Ca 486/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 486/15
- summary_1line: Caselaw corpus record: III CA 486/15.
- external_id: saos:185177
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:185177/raw/bb9233566f9d48b46cf9f5b2e6cf3a84915b821ae16ee54f423ea20d463512b6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_185177`

##### `saos_pl:291164` — REASONS III Ca 507/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 507/17
- summary_1line: Caselaw corpus record: III CA 507/17.
- external_id: saos:291164
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:291164/raw/b48e619529b63a5bbbf5f779fcb947ed87289f6699d4e0385cdad2c0ea655a4c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_291164`

##### `saos_pl:56537` — REASONS III Ca 542/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 542/14
- summary_1line: Caselaw corpus record: III CA 542/14.
- external_id: saos:56537
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:56537/raw/fef2877e96833ed3aad8061644fa74f51d0599129d29847e4cbcb84858b6ce94/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_56537`

##### `saos_pl:190004` — REASONS III Ca 550/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 550/15
- summary_1line: Caselaw corpus record: III CA 550/15.
- external_id: saos:190004
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:190004/raw/c98a0fd9d8df3447936548b48b95230dc8b4e9a1aecd05fa6caf61eb8264a210/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_190004`

##### `saos_pl:191350` — REASONS III Ca 650/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 650/15
- summary_1line: Caselaw corpus record: III CA 650/15.
- external_id: saos:191350
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:191350/raw/4fdc74dfda33b3ff3489ba164ddc02ea03f28d8f4f4af8926c67a52fc9865279/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_191350`

##### `saos_pl:303301` — REASONS III Ca 672/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 672/17
- summary_1line: Caselaw corpus record: III CA 672/17.
- external_id: saos:303301
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:303301/raw/3b99f3ab755f378f4dc7146829b196a07bce4a4e674e81a2d7578493e6f0098b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_303301`

##### `saos_pl:74482` — REASONS III Ca 674/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 674/14
- summary_1line: Caselaw corpus record: III CA 674/14.
- external_id: saos:74482
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:74482/raw/f1c437b860dce98ba264cccdf0b8fe065afe009178262ef171e3a5a8835d8283/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_74482`

##### `saos_pl:305793` — REASONS III Ca 678/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 678/17
- summary_1line: Caselaw corpus record: III CA 678/17.
- external_id: saos:305793
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305793/raw/cab4feb1313d85487aa8c3f80f68f3c01184ee39cdd587e07cd881de004e2dc8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305793`

##### `saos_pl:191378` — REASONS III Ca 691/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 691/15
- summary_1line: Caselaw corpus record: III CA 691/15.
- external_id: saos:191378
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:191378/raw/7a006d559891212eb77888a6f17f9bbbe55d827e445e52025cf141c68d1d0335/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_191378`

##### `saos_pl:475018` — REASONS III Ca 726/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 726/21
- summary_1line: Caselaw corpus record: III CA 726/21.
- external_id: saos:475018
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:475018/raw/5a725653e5821014ff928ef4c432d6ff066ed17d51bb0f7b7b2aa450f6f94672/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_475018`

##### `saos_pl:313303` — REASONS III Ca 770/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 770/17
- summary_1line: Caselaw corpus record: III CA 770/17.
- external_id: saos:313303
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:313303/raw/b375580995c8470ee072ab4846aa9c9bc2f728f403c568e2c343e09c023a834e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_313303`

##### `saos_pl:75681` — REASONS III Ca 791/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 791/14
- summary_1line: Caselaw corpus record: III CA 791/14.
- external_id: saos:75681
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:75681/raw/27a26d5ee19c1ab0e616136bd7605298b31eafd81a3692dc448d38edfb5bc265/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_75681`

##### `saos_pl:415223` — REASONS III Ca 808/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 808/19
- summary_1line: Caselaw corpus record: III CA 808/19.
- external_id: saos:415223
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:415223/raw/f4b9a51a9dffd2797812ba8ed7279f6948fb07e37217f4a1e14553eb11c27418/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_415223`

##### `saos_pl:460158` — REASONS III Ca 818/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 818/20
- summary_1line: Caselaw corpus record: III CA 818/20.
- external_id: saos:460158
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:460158/raw/32f1e1d7df90b9ea2a7fa2ee1da4d7802b594fa8b342121d4b32f599c7131ce9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_460158`

##### `saos_pl:255492` — REASONS III Ca 916/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 916/16
- summary_1line: Caselaw corpus record: III CA 916/16.
- external_id: saos:255492
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:255492/raw/2bd2b5ab17473c24310a3c67a05f21700cf263546bdfd81af6b9fe63933af59a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_255492`

##### `saos_pl:228108` — REASONS III K 482/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III K 482/14
- summary_1line: Caselaw corpus record: III K 482/14.
- external_id: saos:228108
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:228108/raw/d97a1e3f609e32f632d65530d6a9dfad2ac63a400d79538e4767bf316ff6b654/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_228108`

##### `saos_pl:190325` — REASONS III RC 169/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 169/15
- summary_1line: Caselaw corpus record: III RC 169/15.
- external_id: saos:190325
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:190325/raw/b4142608ec28cef1251bf28676a8ff3cc3d59d3c4ec806b5d146b88ce1c0a8e8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_190325`

##### `saos_pl:293923` — REASONS III RC 170/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 170/17
- summary_1line: Caselaw corpus record: III RC 170/17.
- external_id: saos:293923
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:293923/raw/229cc2b156c6e0d07f8edcafbdabac81c5edbd4b99a332df02f833f2a5d15a2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_293923`

##### `saos_pl:222759` — REASONS III RC 335/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 335/14
- summary_1line: Caselaw corpus record: III RC 335/14.
- external_id: saos:222759
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222759/raw/0c0c6c3fe47b0e766b2cc386bbca0106ac3dc82d9aedb5ff23bae10fa2f7d368/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222759`

##### `saos_pl:370923` — REASONS III RC 89/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 89/16
- summary_1line: Caselaw corpus record: III RC 89/16.
- external_id: saos:370923
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:370923/raw/80d71d17931e88dc50a6a5f1813491c17f970e6f6ea04c29e0a77f9024e2cdf0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_370923`

##### `saos_pl:352416` — REASONS IV K 119/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV K 119/13
- summary_1line: Caselaw corpus record: IV K 119/13.
- external_id: saos:352416
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:352416/raw/a4d80addbe13ce08790ded213c68bce0d86b65db517ed0125cf338970c42f65b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_352416`

##### `saos_pl:315367` — REASONS IV K 23/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV K 23/14
- summary_1line: Caselaw corpus record: IV K 23/14.
- external_id: saos:315367
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:315367/raw/f8fe316af24794abc8eb7e9fc040b97f4fa4a266846d0e328b9e36c3b10a3d1e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_315367`

##### `saos_pl:516177` — REASONS IX GC 3566/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX GC 3566/19
- summary_1line: Caselaw corpus record: IX GC 3566/19.
- external_id: saos:516177
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:516177/raw/ca58557f01e802530545441cb1d621b87dca9d120747883579518859347c64a3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_516177`

##### `saos_pl:288159` — REASONS V Ka 1557/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V KA 1557/16
- summary_1line: Caselaw corpus record: V KA 1557/16.
- external_id: saos:288159
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:288159/raw/07076ca69e9762e5a9c85fa824a5207ad3d3280978d999b816adcd8b81e6667b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_288159`

##### `saos_pl:450344` — REASONS V RC 217/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V RC 217/20
- summary_1line: Caselaw corpus record: V RC 217/20.
- external_id: saos:450344
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:450344/raw/5a77c72bd5f1665af646ad2410c6ad085fb25621981eea0e4f47b855a6a1bc5c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_450344`

##### `saos_pl:487673` — REASONS VI C 1673/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 1673/22
- summary_1line: Caselaw corpus record: VI C 1673/22.
- external_id: saos:487673
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:487673/raw/b921beb06902cce6ed7d5c4fc23e44f5a3fbc30ec3205e27b9b3c3f640bb5891/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487673`

##### `saos_pl:45528` — REASONS VI C 2193/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 2193/13
- summary_1line: Caselaw corpus record: VI C 2193/13.
- external_id: saos:45528
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:45528/raw/7ee025c61ed1719a041a4c503b83e3f8f9cb7080dcabc5cf8f27ec4db121f229/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_45528`

##### `saos_pl:461054` — REASONS VI C 539/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 539/21
- summary_1line: Caselaw corpus record: VI C 539/21.
- external_id: saos:461054
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:461054/raw/e459b469df95bc84c8c46c5483c9d4f919d22305c76f72a586752118c1e5a96a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_461054`

##### `saos_pl:219462` — REASONS VIII GC 18/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 18/16
- summary_1line: Caselaw corpus record: VIII GC 18/16.
- external_id: saos:219462
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:219462/raw/5d91107e042cbb2d17c5412e0290aa30eebc07aa79aa85d1bec582069f74f620/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_219462`

##### `saos_pl:470301` — REASONS VIII GC 293/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 293/20
- summary_1line: Caselaw corpus record: VIII GC 293/20.
- external_id: saos:470301
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:470301/raw/f32d42917d621eccb4560e115329ce46846699132cec45697a1ce8670a9b04af/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_470301`

##### `saos_pl:484778` — REASONS VIII GC 474/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 474/22
- summary_1line: Caselaw corpus record: VIII GC 474/22.
- external_id: saos:484778
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484778/raw/f32b22593d693ae54d97effa830351c6a4e1e2592841d01d665c4e30225f71ef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484778`

##### `saos_pl:356840` — REASONS X C 3541/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 3541/17
- summary_1line: Caselaw corpus record: X C 3541/17.
- external_id: saos:356840
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:356840/raw/ddbd9553fc7317e4bce47bda89340e52329f400b469cbcce1d9eac05ccfd6eb6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_356840`

##### `saos_pl:60094` — REASONS X C 477/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 477/14
- summary_1line: Caselaw corpus record: X C 477/14.
- external_id: saos:60094
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:60094/raw/6a8d1050a1a6e6f8e8d1382f3dad05d85350ea0426d92040ea371dec94bf7c94/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_60094`

##### `saos_pl:349674` — REASONS X GC 860/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X GC 860/17
- summary_1line: Caselaw corpus record: X GC 860/17.
- external_id: saos:349674
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:349674/raw/9e2e085d35ac3a0c99ea662bf4689820c27cf25395c29f4553990754c0e91ede/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_349674`

##### `saos_pl:257924` — REASONS XIV K 261/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XIV K 261/14
- summary_1line: Caselaw corpus record: XIV K 261/14.
- external_id: saos:257924
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:257924/raw/1fea992475eb7c25f0170272553a7de534efc035f08b0b3d989feee43a9619fe/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_257924`

##### `saos_pl:376228` — REASONS XIV K 351/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XIV K 351/16
- summary_1line: Caselaw corpus record: XIV K 351/16.
- external_id: saos:376228
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:376228/raw/02d929a5fdfbead59442a3e9b5f7a278ff736fe9b53c7cb3062ecc71ed792802/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_376228`

##### `saos_pl:286097` — REASONS XIV K 561/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XIV K 561/13
- summary_1line: Caselaw corpus record: XIV K 561/13.
- external_id: saos:286097
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:286097/raw/96df2b1f4beada3661299988a5f294edaa760c606bd373620de3cd5b6afb7b25/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_286097`

##### `saos_pl:62811` — REASONS XV GC 116/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV GC 116/12
- summary_1line: Caselaw corpus record: XV GC 116/12.
- external_id: saos:62811
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:62811/raw/ba497ee6812931dfdd66c8063f0b5f90c2cd0142e5103153cebcb6b26d3916bd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_62811`

##### `saos_pl:290944` — REASONS XVI C 1330/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI C 1330/15
- summary_1line: Caselaw corpus record: XVI C 1330/15.
- external_id: saos:290944
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:290944/raw/5bade72032a3bc663b3c90b9103e780df82c2c9b76a56ebbcb30192e1ace9a19/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_290944`

##### `saos_pl:231034` — REASONS XVI C 1349/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI C 1349/15
- summary_1line: Caselaw corpus record: XVI C 1349/15.
- external_id: saos:231034
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:231034/raw/7be1b4c6809b43d9e0a4776f8a5fe7eabe76a1dff829d02fa671b8f87790b54e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_231034`

##### `saos_pl:131725` — REASONS XVI GC 416/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI GC 416/13
- summary_1line: Caselaw corpus record: XVI GC 416/13.
- external_id: saos:131725
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:131725/raw/8c3bb7b313faf417b8b9a1d021e72ff290fc93c7bf69c4e64b03b7d2a681da24/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_131725`

##### `saos_pl:150791` — REASONS XVII AmT 78/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 78/12
- summary_1line: Caselaw corpus record: XVII AMT 78/12.
- external_id: saos:150791
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:150791/raw/1ac559f1a68036d2e17900ead4ebb146cb47d249b297aaf2eecb726ad8260207/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_150791`

##### `saos_pl:153518` — REASONS XVIII K 409/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVIII K 409/11
- summary_1line: Caselaw corpus record: XVIII K 409/11.
- external_id: saos:153518
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153518/raw/7dc5e9f9bd1adeeb3e0ae56f6979a9b92a3c3b2b6dc6da718744a16fe157b960/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153518`

##### `saos_pl:148282` — REASONS XX GC 19/10 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 19/10
- summary_1line: Caselaw corpus record: XX GC 19/10.
- external_id: saos:148282
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:148282/raw/7e15bc9fe1618eaa55bb4140017a7276f493274d41dfcb2ca37d2d50e9e63bb7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_148282`

##### `saos_pl:148740` — REASONS XX GC 555/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 555/11
- summary_1line: Caselaw corpus record: XX GC 555/11.
- external_id: saos:148740
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:148740/raw/a883501e9b119d0556b5c7c7dc6fbbd0afde66ca6c825f0995923d895f964873/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_148740`

##### `saos_pl:48937` — REASONS XX GC 66/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 66/11
- summary_1line: Caselaw corpus record: XX GC 66/11.
- external_id: saos:48937
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:48937/raw/bad970f42762a23ff44ffb609d8eb921c07a23e8acbfd6a5ce78b4c4da487003/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_48937`

##### `saos_pl:473445` — REGULATION I C 2330/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2330/20
- summary_1line: Caselaw corpus record: I C 2330/20.
- external_id: saos:473445
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:473445/raw/30647480e1859aeb0f45ed08bbb75367b7b87a8eb676df4c59c2fd2c44fce7d8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_473445`

##### `saos_pl:367591` — REGULATION I C 3034/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 3034/17
- summary_1line: Caselaw corpus record: I C 3034/17.
- external_id: saos:367591
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:367591/raw/c8aad24617e331d4b6853afade7bf2241f4e414994213ff8c90d293ee0856665/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_367591`

##### `saos_pl:266079` — REGULATION I C 38/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 38/15
- summary_1line: Caselaw corpus record: I C 38/15.
- external_id: saos:266079
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:266079/raw/aeef85256254a0d31b85519ae572ec3496b4912610cbf3760b3388335c6ef0f7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_266079`

##### `saos_pl:267647` — REGULATION I C 597/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 597/15
- summary_1line: Caselaw corpus record: I C 597/15.
- external_id: saos:267647
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:267647/raw/0802f36feae3d35c18ecfca3f0c3bdd4fe8d898c2dbb8ada81c66706badb0aca/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_267647`

##### `saos_pl:445728` — REGULATION I C 749/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 749/17
- summary_1line: Caselaw corpus record: I C 749/17.
- external_id: saos:445728
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:445728/raw/6cd299579d7c05959c8611f156564ba1b8984eba0aeb7d275f66514f01925122/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_445728`

##### `saos_pl:251711` — REGULATION I Ns 637/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 637/16
- summary_1line: Caselaw corpus record: I NS 637/16.
- external_id: saos:251711
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:251711/raw/6aad626389c3747e95ad4526f8c99830037c9453231896c9cbecf47e56a5d521/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_251711`

##### `saos_pl:198496` — REGULATION I Ns 9/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I NS 9/15
- summary_1line: Caselaw corpus record: I NS 9/15.
- external_id: saos:198496
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:198496/raw/0043313f54c2ed3f2838c0e6284b2c0083fed1a1a18a5a6133a5efb6b364f44b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_198496`

##### `saos_pl:155675` — REGULATION II C 1832/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 1832/14
- summary_1line: Caselaw corpus record: II C 1832/14.
- external_id: saos:155675
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155675/raw/6fddf7a90b766f887196e56d3047dde4862770cb889fbbb2593930e7c2bd22e8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155675`

##### `saos_pl:501463` — REGULATION II C 2834/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 2834/22
- summary_1line: Caselaw corpus record: II C 2834/22.
- external_id: saos:501463
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:501463/raw/6336620144fa35b1bf95996d614c55591a594a76ac48df64d3a7510e0f6aa515/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_501463`

##### `saos_pl:436110` — REGULATION II C 7108/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 7108/17
- summary_1line: Caselaw corpus record: II C 7108/17.
- external_id: saos:436110
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:436110/raw/545c8ad305be0033652e81a006a376cf8dd464588d1269dff2445c0711ab4847/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_436110`

##### `saos_pl:363370` — REGULATION II Ca 149/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 149/18
- summary_1line: Caselaw corpus record: II CA 149/18.
- external_id: saos:363370
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:363370/raw/76aa8903f409435614945d75f97be8c24efccaf75c6c4439a6a3d97b32bb7800/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_363370`

##### `saos_pl:384187` — REGULATION II Ca 516/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 516/18
- summary_1line: Caselaw corpus record: II CA 516/18.
- external_id: saos:384187
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:384187/raw/826f40f61793d45d3a2796ed20230efebcc37c4581dac09871c6dce839c665d2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_384187`

##### `saos_pl:441251` — REGULATION III Ns 64/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III NS 64/18
- summary_1line: Caselaw corpus record: III NS 64/18.
- external_id: saos:441251
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:441251/raw/f0eba7960613e91c6011e5c3b0abab8c503a23f3cf95728a7e41512c58cf1e6e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_441251`

##### `saos_pl:357141` — REGULATION IX P 684/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX P 684/17
- summary_1line: Caselaw corpus record: IX P 684/17.
- external_id: saos:357141
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:357141/raw/c315453687616a819046efb94cfd7bcaf84c377d82c7790eeac035b1d598a673/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_357141`

##### `saos_pl:366319` — REGULATION VI C 1445/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 1445/17
- summary_1line: Caselaw corpus record: VI C 1445/17.
- external_id: saos:366319
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:366319/raw/741cfe2328c2868767ae545918db64241585f0a380dd2d9c77e38e564648ef90/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_366319`

##### `saos_pl:510736` — REGULATION VI C 2427/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 2427/22
- summary_1line: Caselaw corpus record: VI C 2427/22.
- external_id: saos:510736
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:510736/raw/a96eb21f52ade2060fdf5bb2a25d93d704540de9d016f632b63a1983a1b990ff/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_510736`

##### `saos_pl:526479` — REGULATION VI C 302/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 302/24
- summary_1line: Caselaw corpus record: VI C 302/24.
- external_id: saos:526479
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:526479/raw/397807916f9f5115a6237da8c6b31e7d3b726984b5ed5c9b6f2bf7fa9a71884b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_526479`

##### `saos_pl:389792` — REGULATION VI C 574/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 574/18
- summary_1line: Caselaw corpus record: VI C 574/18.
- external_id: saos:389792
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:389792/raw/0c371431597349c59382cfe9c82e81f0eb671a39dd461108af578e54eb3a84fb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_389792`

##### `saos_pl:219999` — REGULATION VIII GC 402/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 402/14
- summary_1line: Caselaw corpus record: VIII GC 402/14.
- external_id: saos:219999
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:219999/raw/7839e7e51506d795173ad62ca936f6733d8530d21896726d49746c583d21d2ec/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_219999`

##### `saos_pl:356104` — REGULATION VIII Ga 235/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 235/18
- summary_1line: Caselaw corpus record: VIII GA 235/18.
- external_id: saos:356104
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:356104/raw/ce39e2fa334eea68ecf0afa3246e602fe68300c5b33b18abae56dda653f53f92/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_356104`

##### `saos_pl:306762` — REGULATION VIII Ga 237/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 237/17
- summary_1line: Caselaw corpus record: VIII GA 237/17.
- external_id: saos:306762
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:306762/raw/ab7023ea6a0cb43854d5c324645fdbaf479958e9ada52829f58bbfff9987614c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_306762`

##### `saos_pl:223464` — REGULATION X C 1412/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1412/15
- summary_1line: Caselaw corpus record: X C 1412/15.
- external_id: saos:223464
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:223464/raw/1d827ce375ca46d58194ebdd31ac24b194fbf2adf10e89ae5933276a552cd4b1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_223464`

##### `saos_pl:197561` — REGULATION X C 419/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 419/15
- summary_1line: Caselaw corpus record: X C 419/15.
- external_id: saos:197561
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:197561/raw/853879786c9da841c9200cfaca9be58029e77ff31876807448dec451135ab6d0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_197561`

##### `saos_pl:67891` — REGULATION X GC 180/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X GC 180/13
- summary_1line: Caselaw corpus record: X GC 180/13.
- external_id: saos:67891
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:67891/raw/77d15a7b234e41e08ee3743aa2c21fb5ebe276ced5c8b15a017640e2c5ec1825/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_67891`

##### `saos_pl:482659` — REGULATION XI GC 397/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 397/21
- summary_1line: Caselaw corpus record: XI GC 397/21.
- external_id: saos:482659
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:482659/raw/cb030c906c5d5a03cc9cb8f7d2933254c5ee796ff95df2b041f7439922383c9f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_482659`

##### `saos_pl:490417` — REGULATION XI GC 618/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 618/22
- summary_1line: Caselaw corpus record: XI GC 618/22.
- external_id: saos:490417
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:490417/raw/99facf8d71fe84a00c06ec11241d32efe12e9d0418e298f4aa119e8d2adcd38d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_490417`

##### `saos_pl:484323` — REGULATION XVI C 4130/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI C 4130/21
- summary_1line: Caselaw corpus record: XVI C 4130/21.
- external_id: saos:484323
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484323/raw/4ef01aec3bec930cbf2dec06d92eada5fbab9f3b80ab9bb0d3afee961df9eced/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484323`

##### `saos_pl:286115` — REGULATION XVI C 81/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI C 81/16
- summary_1line: Caselaw corpus record: XVI C 81/16.
- external_id: saos:286115
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:286115/raw/4b529921ad28925600073b536d0921af14d992c509751321de1800aa1d9774b9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_286115`

##### `saos_pl:10453` — SENTENCE I ACa 1004/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1004/12
- summary_1line: Caselaw corpus record: I ACA 1004/12.
- external_id: saos:10453
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:10453/raw/9f1e14729621d5ea1e010207b35ee12bd760670b29c372ef8d4f73a6772cbce5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_10453`

##### `saos_pl:294824` — SENTENCE I ACa 1030/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1030/16
- summary_1line: Caselaw corpus record: I ACA 1030/16.
- external_id: saos:294824
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:294824/raw/ae92776fc2566295183fbbbe59f9c729e0a77d05b963c7abd92cda4efcba312d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_294824`

##### `saos_pl:331745` — SENTENCE I ACa 1041/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1041/17
- summary_1line: Caselaw corpus record: I ACA 1041/17.
- external_id: saos:331745
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:331745/raw/21f88a67e9b0fc5d69a5663e3fe4394b86deaf2ebb0ad56e341b3840dae05c31/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_331745`

##### `saos_pl:4846` — SENTENCE I ACa 107/09 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 107/09
- summary_1line: Caselaw corpus record: I ACA 107/09.
- external_id: saos:4846
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:4846/raw/5422534f97b6a06176cc76319a86a03c565331a3546c0ab5e034e6bbf19f112f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_4846`

##### `saos_pl:231075` — SENTENCE I ACa 1151/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1151/15
- summary_1line: Caselaw corpus record: I ACA 1151/15.
- external_id: saos:231075
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:231075/raw/1265e4e436a526a377680d4741904b6d113586097f0e4832da763644922b4c07/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_231075`

##### `saos_pl:8906` — SENTENCE I ACa 1157/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1157/12
- summary_1line: Caselaw corpus record: I ACA 1157/12.
- external_id: saos:8906
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:8906/raw/a1bfbb3fadd856d75ccecef0c8aa7a5536ceddbf1b18945aed0c755bb946134a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_8906`

##### `saos_pl:198388` — SENTENCE I ACa 1161/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1161/14
- summary_1line: Caselaw corpus record: I ACA 1161/14.
- external_id: saos:198388
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:198388/raw/35a4609c582156babc90263cbfea05d6af3737f2cc4706b28673b417d44446d0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_198388`

##### `saos_pl:325862` — SENTENCE I ACa 1162/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1162/16
- summary_1line: Caselaw corpus record: I ACA 1162/16.
- external_id: saos:325862
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:325862/raw/db5613e72a39730c7b48952e4beedd129d98b342e9c0685507d13e9e9c3f4941/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_325862`

##### `saos_pl:153055` — SENTENCE I ACa 1190/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1190/14
- summary_1line: Caselaw corpus record: I ACA 1190/14.
- external_id: saos:153055
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153055/raw/b1d7cf18e20bb0e3e27e0157f7e3dd59ee0a07d809f3d4c1a3601afabc7df148/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153055`

##### `saos_pl:438007` — SENTENCE I ACa 1200/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1200/19
- summary_1line: Caselaw corpus record: I ACA 1200/19.
- external_id: saos:438007
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:438007/raw/e24711da890b00cafbaaef797d9e50b7ee867b0745f826de130a0064ceec79fe/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_438007`

##### `saos_pl:54140` — SENTENCE I ACa 1209/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1209/13
- summary_1line: Caselaw corpus record: I ACA 1209/13.
- external_id: saos:54140
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:54140/raw/5d61192600451daca72eb8b828c7da2ae00a81093f0e6f12b12cf04fbb6a17bc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_54140`

##### `saos_pl:42425` — SENTENCE I ACa 1278/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1278/13
- summary_1line: Caselaw corpus record: I ACA 1278/13.
- external_id: saos:42425
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:42425/raw/51404eb8c422e6cd458c7b168f55b715614790711c06a8d8216a522a747b6afd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_42425`

##### `saos_pl:344229` — SENTENCE I ACa 1304/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1304/17
- summary_1line: Caselaw corpus record: I ACA 1304/17.
- external_id: saos:344229
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:344229/raw/94ad347eed683d4a216ab1059637965af7215011ade8fa453bf8bb4976077953/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_344229`

##### `saos_pl:49425` — SENTENCE I ACa 1311/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1311/13
- summary_1line: Caselaw corpus record: I ACA 1311/13.
- external_id: saos:49425
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:49425/raw/c66c547b94683c1bf92cbefef4403416fff152f2ffb895e8994650c1c8fdd1bf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_49425`

##### `saos_pl:69560` — SENTENCE I ACa 1421/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1421/14
- summary_1line: Caselaw corpus record: I ACA 1421/14.
- external_id: saos:69560
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:69560/raw/de93b3b7c2bc0ce49b62dba44f84e41f187fddb502d37182b78b93d8107d5992/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_69560`

##### `saos_pl:322975` — SENTENCE I ACa 1491/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1491/15
- summary_1line: Caselaw corpus record: I ACA 1491/15.
- external_id: saos:322975
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:322975/raw/c2fd6e21729cc09c0ed6114908eb574ef5115de74f66042d24430c26beebe30f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_322975`

##### `saos_pl:50801` — SENTENCE I ACa 1513/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1513/13
- summary_1line: Caselaw corpus record: I ACA 1513/13.
- external_id: saos:50801
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:50801/raw/845cec4ab57c6cfe85458f20dc8911c990366d36f0a5f1bce04d8b31d449f1a6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_50801`

##### `saos_pl:26017` — SENTENCE I ACa 1516/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1516/12
- summary_1line: Caselaw corpus record: I ACA 1516/12.
- external_id: saos:26017
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:26017/raw/420bca7eaaa4b90ff9a0c674b9a3b8a53eabeda0d91abef1ab00818c79d99d3c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_26017`

##### `saos_pl:268008` — SENTENCE I ACa 1517/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1517/15
- summary_1line: Caselaw corpus record: I ACA 1517/15.
- external_id: saos:268008
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:268008/raw/314390ff149068f00a7147a4c7f1b897a895be0ccf6fef70727a9d2d02081963/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_268008`

##### `saos_pl:169943` — SENTENCE I ACa 1545/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1545/14
- summary_1line: Caselaw corpus record: I ACA 1545/14.
- external_id: saos:169943
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:169943/raw/41818662845bc58b24b4fc6cccb6e5caa6a4f3a942d8f20a9ad021c4d099d688/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_169943`

##### `saos_pl:263281` — SENTENCE I ACa 1622/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1622/15
- summary_1line: Caselaw corpus record: I ACA 1622/15.
- external_id: saos:263281
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:263281/raw/afe786f076814ce8f49149ddc3f77d3a4c2ca0fec662091c1c51862c10bd975d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_263281`

##### `saos_pl:493732` — SENTENCE I ACa 1623/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1623/22
- summary_1line: Caselaw corpus record: I ACA 1623/22.
- external_id: saos:493732
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:493732/raw/048d2aeef9ad1f1c7366dd3ed4b1a6a9c51226360f49215b3fb6f461667549d3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_493732`

##### `saos_pl:238751` — SENTENCE I ACa 1697/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 1697/15
- summary_1line: Caselaw corpus record: I ACA 1697/15.
- external_id: saos:238751
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:238751/raw/6e85cd938d2ef2a2919d143a1e71d0c031b9e9f44421248ef91c528f88040726/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_238751`

##### `saos_pl:37115` — SENTENCE I ACa 219/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 219/13
- summary_1line: Caselaw corpus record: I ACA 219/13.
- external_id: saos:37115
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:37115/raw/6304abab312e3600f94ee3bea71c84fffb5de00667873bae13e233985bcfc2f6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_37115`

##### `saos_pl:465704` — SENTENCE I ACa 223/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 223/21
- summary_1line: Caselaw corpus record: I ACA 223/21.
- external_id: saos:465704
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:465704/raw/3b8ccf9a05ddf005d111810bac2fc216f368d351c7c982741664411d90409b99/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_465704`

##### `saos_pl:273491` — SENTENCE I ACa 2271/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 2271/15
- summary_1line: Caselaw corpus record: I ACA 2271/15.
- external_id: saos:273491
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:273491/raw/b7f2a8beec195a04661d6e6eb31bae4d101ab16a1f26b768b6f6c6c2858e773e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_273491`

##### `saos_pl:231850` — SENTENCE I ACa 239/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 239/16
- summary_1line: Caselaw corpus record: I ACA 239/16.
- external_id: saos:231850
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:231850/raw/968f7db5c2c6e9739a7a7f3d0514b86d82a80b883c96bd68dff2e5d2cf09baea/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_231850`

##### `saos_pl:448135` — SENTENCE I ACa 250/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 250/21
- summary_1line: Caselaw corpus record: I ACA 250/21.
- external_id: saos:448135
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:448135/raw/ca8c5d6077f6934cfeac59a13845bd75e6c5d4e27a21962cae24a58c10afccda/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_448135`

##### `saos_pl:60475` — SENTENCE I ACa 253/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 253/14
- summary_1line: Caselaw corpus record: I ACA 253/14.
- external_id: saos:60475
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:60475/raw/c40436a792b4c1fb833427d13b7ff6c9070b1b0e9be50c8daaf7f5d549cef8db/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_60475`

##### `saos_pl:14234` — SENTENCE I ACa 264/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 264/13
- summary_1line: Caselaw corpus record: I ACA 264/13.
- external_id: saos:14234
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:14234/raw/583d8dc528952cf7e9974ed9c9ceef45a0e352d9c6511fd55ecccfd2eae39b50/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_14234`

##### `saos_pl:460271` — SENTENCE I ACa 267/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 267/21
- summary_1line: Caselaw corpus record: I ACA 267/21.
- external_id: saos:460271
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:460271/raw/833c3a3777ae8a741ac172e7162a42c5b5e235967710fb529f669c6d0a1084ca/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_460271`

##### `saos_pl:14236` — SENTENCE I ACa 274/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 274/13
- summary_1line: Caselaw corpus record: I ACA 274/13.
- external_id: saos:14236
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:14236/raw/c6e971e0573bcb59814b2c5b27f383c1b6f2769ff5e249aa2d49b5a116c2a466/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_14236`

##### `saos_pl:311904` — SENTENCE I ACa 276/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 276/17
- summary_1line: Caselaw corpus record: I ACA 276/17.
- external_id: saos:311904
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:311904/raw/a153aff99f2c541e2c8ae1cbeed48c9c59cab0469f33ca24d15169000297e14d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_311904`

##### `saos_pl:154096` — SENTENCE I ACa 33/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 33/15
- summary_1line: Caselaw corpus record: I ACA 33/15.
- external_id: saos:154096
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:154096/raw/d0ed9ef96ac408a82516d30b0aa39b34d0674e215c3ff7e39506c625b1834427/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_154096`

##### `saos_pl:65728` — SENTENCE I ACa 395/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 395/14
- summary_1line: Caselaw corpus record: I ACA 395/14.
- external_id: saos:65728
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:65728/raw/bf83c467ad342cdabe7de7cc119996dfafc659e61eba9643119511ea7d1e86a8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_65728`

##### `saos_pl:178447` — SENTENCE I ACa 407/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 407/14
- summary_1line: Caselaw corpus record: I ACA 407/14.
- external_id: saos:178447
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:178447/raw/f721a44b7fc1f4d99c2bee28b53427fb20f6499125925b3f7ef166b898388e4d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_178447`

##### `saos_pl:50988` — SENTENCE I ACa 429/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 429/14
- summary_1line: Caselaw corpus record: I ACA 429/14.
- external_id: saos:50988
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:50988/raw/08d166099efda7d3e6136936724dd404494e52ac2cde3f7294335a050952c5f0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_50988`

##### `saos_pl:376436` — SENTENCE I ACa 429/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 429/18
- summary_1line: Caselaw corpus record: I ACA 429/18.
- external_id: saos:376436
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:376436/raw/185f12bd57402f936584d80186d85e0029d3f16f0bdd03fb77b0b37bb61fb202/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_376436`

##### `saos_pl:47078` — SENTENCE I ACa 436/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 436/13
- summary_1line: Caselaw corpus record: I ACA 436/13.
- external_id: saos:47078
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:47078/raw/f8d35b9585b2a48068fef52167eecc0793aa86730a7c601054de48ed986f0b6d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_47078`

##### `saos_pl:225945` — SENTENCE I ACa 436/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 436/15
- summary_1line: Caselaw corpus record: I ACA 436/15.
- external_id: saos:225945
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:225945/raw/3fb16c80afeb3dc07831e9708d3dde20135c11d0c779dfe33c7b16ec61deb96c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_225945`

##### `saos_pl:330` — SENTENCE I ACa 445/09 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 445/09
- summary_1line: Caselaw corpus record: I ACA 445/09.
- external_id: saos:330
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:330/raw/2be2049172b149fa64ea795682ca6b19f2fddc853f4000181854af2395b15420/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_330`

##### `saos_pl:429402` — SENTENCE I ACa 479/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 479/19
- summary_1line: Caselaw corpus record: I ACA 479/19.
- external_id: saos:429402
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:429402/raw/9e6fbfe23169e189c3050ecc25ba6501b3a13ecf02b51a87f4c0187e49d3a5cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_429402`

##### `saos_pl:22414` — SENTENCE I ACa 52/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 52/13
- summary_1line: Caselaw corpus record: I ACA 52/13.
- external_id: saos:22414
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:22414/raw/454be63c282183768614be98e761e92dcba88ac19a3b0922935e4a362bb6f870/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_22414`

##### `saos_pl:177971` — SENTENCE I ACa 547/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 547/15
- summary_1line: Caselaw corpus record: I ACA 547/15.
- external_id: saos:177971
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:177971/raw/7f6f7a8dfb1c63a5f21f7ccf4e2e717b503769057fa03f4b2ab39d37ce8fc410/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_177971`

##### `saos_pl:26883` — SENTENCE I ACa 561/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 561/13
- summary_1line: Caselaw corpus record: I ACA 561/13.
- external_id: saos:26883
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:26883/raw/d921d4e7129ae0df7ed621c267b3066cee0021d12742fcd13d1720e1df9dc452/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_26883`

##### `saos_pl:3575` — SENTENCE I ACa 593/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 593/12
- summary_1line: Caselaw corpus record: I ACA 593/12.
- external_id: saos:3575
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:3575/raw/793e432b0da20058c573e4bce55b3b60fced95605d3a17178451d676592ff1e6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_3575`

##### `saos_pl:280469` — SENTENCE I ACa 593/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 593/16
- summary_1line: Caselaw corpus record: I ACA 593/16.
- external_id: saos:280469
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:280469/raw/0601860eddcd63c63bbc777020bf142573e90fa7077b4ec3e8077f6a521e6155/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_280469`

##### `saos_pl:396831` — SENTENCE I ACa 604/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 604/18
- summary_1line: Caselaw corpus record: I ACA 604/18.
- external_id: saos:396831
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:396831/raw/1cd51c3f0d7d647bb314daddeec488bc39f8b05deee26faffef070acf5a7095b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_396831`

##### `saos_pl:376514` — SENTENCE I ACa 612/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 612/18
- summary_1line: Caselaw corpus record: I ACA 612/18.
- external_id: saos:376514
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:376514/raw/14d26a16cf0e375dca48a993e52c80bd9b8f4636b69ef7ded513b5144bfc268c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_376514`

##### `saos_pl:131228` — SENTENCE I ACa 658/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 658/14
- summary_1line: Caselaw corpus record: I ACA 658/14.
- external_id: saos:131228
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:131228/raw/59eafd96964fc71c482f75a817715908cca728ae614a897d88cef76251eba8f5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_131228`

##### `saos_pl:2637` — SENTENCE I ACa 659/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 659/12
- summary_1line: Caselaw corpus record: I ACA 659/12.
- external_id: saos:2637
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:2637/raw/edc0191a474d83e431005338a38393fd5751b05fdff581b0f91cec91548c95ab/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_2637`

##### `saos_pl:57554` — SENTENCE I ACa 66/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 66/14
- summary_1line: Caselaw corpus record: I ACA 66/14.
- external_id: saos:57554
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:57554/raw/cc2d90badb8c833a697b84dd672f36d0f5d47f01a9b6f7ace7aa2e47192ce265/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_57554`

##### `saos_pl:267599` — SENTENCE I ACa 666/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 666/16
- summary_1line: Caselaw corpus record: I ACA 666/16.
- external_id: saos:267599
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:267599/raw/2db12459823e9ff0ff1bdbe27216ab76d1e875518161e9653f751656b3289ac4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_267599`

##### `saos_pl:58482` — SENTENCE I ACa 674/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 674/14
- summary_1line: Caselaw corpus record: I ACA 674/14.
- external_id: saos:58482
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:58482/raw/0acefacd2e7b7fc79442ca8d20767e471eabfa2bb744907b7ca499f65529ab76/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_58482`

##### `saos_pl:263286` — SENTENCE I ACa 728/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 728/16
- summary_1line: Caselaw corpus record: I ACA 728/16.
- external_id: saos:263286
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:263286/raw/2b1611ddb8f6d02a8ddc2c2ffe72a383149ee46db42f3e289bdce39597ff7b6c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_263286`

##### `saos_pl:395482` — SENTENCE I ACa 767/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 767/18
- summary_1line: Caselaw corpus record: I ACA 767/18.
- external_id: saos:395482
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:395482/raw/33573f4ff3f7e36332f82c8025c6f28cded2cc52b5a8bfae07500cdc1e1cd261/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_395482`

##### `saos_pl:14130` — SENTENCE I ACa 771/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 771/12
- summary_1line: Caselaw corpus record: I ACA 771/12.
- external_id: saos:14130
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:14130/raw/4357e2f884ff5b34be0077f148f9f23f5134dd384eae2784e1ecaea05d68607f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_14130`

##### `saos_pl:270175` — SENTENCE I ACa 776/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 776/16
- summary_1line: Caselaw corpus record: I ACA 776/16.
- external_id: saos:270175
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:270175/raw/642695a25e43d70589c68bf2221e4cfcdf2613cd3bc1a8c183ae865b289469de/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_270175`

##### `saos_pl:31904` — SENTENCE I ACa 790/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 790/13
- summary_1line: Caselaw corpus record: I ACA 790/13.
- external_id: saos:31904
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:31904/raw/0ee5807f751aca902511c6eb5ebb388d9bbe2627c808168068b3839dc14a8f93/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_31904`

##### `saos_pl:133902` — SENTENCE I ACa 822/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 822/14
- summary_1line: Caselaw corpus record: I ACA 822/14.
- external_id: saos:133902
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:133902/raw/ceb606ace66e63410b8be87631639a2627ddb53e80af24d1e2d4bda872e5c095/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_133902`

##### `saos_pl:297285` — SENTENCE I ACa 824/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 824/16
- summary_1line: Caselaw corpus record: I ACA 824/16.
- external_id: saos:297285
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:297285/raw/10a01191b0832436ef073bd6a4e0249dae339e9085e0d490cba1f3e1465544ed/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_297285`

##### `saos_pl:283755` — SENTENCE I ACa 835/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 835/16
- summary_1line: Caselaw corpus record: I ACA 835/16.
- external_id: saos:283755
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:283755/raw/07199eed59fa99e38a270be20bbc401f3b7f6a49375161cf17262bc48c7619ed/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_283755`

##### `saos_pl:43146` — SENTENCE I ACa 864/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 864/13
- summary_1line: Caselaw corpus record: I ACA 864/13.
- external_id: saos:43146
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:43146/raw/83d7ef246fb5bcb2d9dbf70850a45d2af59436dca9b2b9f572d5eedaa2586e2b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_43146`

##### `saos_pl:273589` — SENTENCE I ACa 914/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 914/16
- summary_1line: Caselaw corpus record: I ACA 914/16.
- external_id: saos:273589
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:273589/raw/7e77ae5ca4e986381203927d6ea497e1328e2468414cb08170c559ee2ea0a26a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_273589`

##### `saos_pl:231131` — SENTENCE I ACa 919/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 919/15
- summary_1line: Caselaw corpus record: I ACA 919/15.
- external_id: saos:231131
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:231131/raw/573c6f93e512bc4e0f5fc16c30733c20e771e21a79f8bc565b4943d0bf042cca/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_231131`

##### `saos_pl:343891` — SENTENCE I ACa 934/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 934/17
- summary_1line: Caselaw corpus record: I ACA 934/17.
- external_id: saos:343891
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:343891/raw/93ef1a5a831b4de35a5865937499b44b04a460611e6e4c26b923b5effd3ad45b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_343891`

##### `saos_pl:6477` — SENTENCE I ACa 945/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 945/12
- summary_1line: Caselaw corpus record: I ACA 945/12.
- external_id: saos:6477
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:6477/raw/22af749a455c0989d26c96df1e94093c9e09984434bf4d58e5c95d1d8f456a8e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_6477`

##### `saos_pl:494797` — SENTENCE I ACa 965/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I ACA 965/19
- summary_1line: Caselaw corpus record: I ACA 965/19.
- external_id: saos:494797
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:494797/raw/25fe084066624ddeadb14baabcc0800a5cc1063d38f93fce37d06df38c56d117/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_494797`

##### `saos_pl:464966` — SENTENCE I AGa 130/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I AGA 130/18
- summary_1line: Caselaw corpus record: I AGA 130/18.
- external_id: saos:464966
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:464966/raw/40379d38ff5b56d76c9235ef45d17c4559d399a3bc1e865c8955396298214815/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_464966`

##### `saos_pl:403059` — SENTENCE I AGa 190/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I AGA 190/18
- summary_1line: Caselaw corpus record: I AGA 190/18.
- external_id: saos:403059
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:403059/raw/cb5eee07434632e7ad35821ca40d2240e0fce39a96f1157e44f1c183f23dc7e3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_403059`

##### `saos_pl:345619` — SENTENCE I AGa 38/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I AGA 38/18
- summary_1line: Caselaw corpus record: I AGA 38/18.
- external_id: saos:345619
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:345619/raw/374092a2ca9ef2d8b6715a93526aff75eaadac7b3160a466e1704c003044460b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_345619`

##### `saos_pl:395111` — SENTENCE I AGa 443/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I AGA 443/18
- summary_1line: Caselaw corpus record: I AGA 443/18.
- external_id: saos:395111
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:395111/raw/7794b70e59de82cff28fbe9db6bc0d852c06dfed8e8dc3ac562ece0a03e476d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_395111`

##### `saos_pl:529001` — SENTENCE I AGa 54/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I AGA 54/22
- summary_1line: Caselaw corpus record: I AGA 54/22.
- external_id: saos:529001
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:529001/raw/4159a6d36a12e2b35e1fbbf295b73e150509005c2ac4edef056b322f190fb40d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_529001`

##### `saos_pl:69955` — SENTENCE I C 1004/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1004/14
- summary_1line: Caselaw corpus record: I C 1004/14.
- external_id: saos:69955
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:69955/raw/8ad4948ee86e83473e72a0c658eafd4604d4ca32d8b4ec013c1b7956d4e0386c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_69955`

##### `saos_pl:70750` — SENTENCE I C 1032/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1032/12
- summary_1line: Caselaw corpus record: I C 1032/12.
- external_id: saos:70750
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:70750/raw/f193d4a3a79b7442bd543c85dacb9474ae88df2c6928e9d3fcec7986b541c4d0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_70750`

##### `saos_pl:252933` — SENTENCE I C 1033/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1033/14
- summary_1line: Caselaw corpus record: I C 1033/14.
- external_id: saos:252933
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:252933/raw/c737cc4bbd67dec13d49c5607e348f98e5219477f1d7e6eaaa3415b2f286db62/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_252933`

##### `saos_pl:261932` — SENTENCE I C 1064/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1064/13
- summary_1line: Caselaw corpus record: I C 1064/13.
- external_id: saos:261932
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:261932/raw/4e589d24d668db2a23bbb7fd21fa66489f920208c1498a0831eec4944384b1a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_261932`

##### `saos_pl:69960` — SENTENCE I C 1084/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1084/14
- summary_1line: Caselaw corpus record: I C 1084/14.
- external_id: saos:69960
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:69960/raw/3123b5afed3cbb8f1a398821ec8703bd68c5664ce3fef2e8f61151edafb69beb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_69960`

##### `saos_pl:143562` — SENTENCE I C 1088/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1088/13
- summary_1line: Caselaw corpus record: I C 1088/13.
- external_id: saos:143562
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:143562/raw/6faf9a5a08c253dae57eae9605bb5ea9a6539888bad620d34afc24fd67dc352c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_143562`

##### `saos_pl:375112` — SENTENCE I C 1093/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1093/18
- summary_1line: Caselaw corpus record: I C 1093/18.
- external_id: saos:375112
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:375112/raw/a7c8926490cd0380522be9173d3180a2bacf50cca6f4faf99ac7eb6fcfa45020/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_375112`

##### `saos_pl:216596` — SENTENCE I C 1103/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1103/15
- summary_1line: Caselaw corpus record: I C 1103/15.
- external_id: saos:216596
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:216596/raw/29f901349245fb43f24d2886b5b63e068a0ddceb5da4a07b44b398043b304121/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_216596`

##### `saos_pl:338002` — SENTENCE I C 1107/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1107/17
- summary_1line: Caselaw corpus record: I C 1107/17.
- external_id: saos:338002
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:338002/raw/81174fa4c6f1b3b1f1bd6e325f2a9e30deb063690cb442742969031ffdf3ac76/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_338002`

##### `saos_pl:429424` — SENTENCE I C 1109/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1109/19
- summary_1line: Caselaw corpus record: I C 1109/19.
- external_id: saos:429424
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:429424/raw/7ea5bcacf6d6f8bcca50aa4f001d23f774899bd8a33224ac575042775060c4a8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_429424`

##### `saos_pl:284216` — SENTENCE I C 1112/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1112/16
- summary_1line: Caselaw corpus record: I C 1112/16.
- external_id: saos:284216
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:284216/raw/0a13bd0062651cc0c700a6c9265130469d50c1499284084e851522b09f63811d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_284216`

##### `saos_pl:489466` — SENTENCE I C 113/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 113/21
- summary_1line: Caselaw corpus record: I C 113/21.
- external_id: saos:489466
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:489466/raw/37507582524f22ab5953c28face03c4ec8387e86d3c485d63b99009ebf33bbe8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_489466`

##### `saos_pl:341807` — SENTENCE I C 1139/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1139/17
- summary_1line: Caselaw corpus record: I C 1139/17.
- external_id: saos:341807
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:341807/raw/f5abb98b65e5fd89eb9f13fef7a4f6f71d4fcbcdc6931b7670feb0cddff4bb19/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_341807`

##### `saos_pl:138972` — SENTENCE I C 114/09 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 114/09
- summary_1line: Caselaw corpus record: I C 114/09.
- external_id: saos:138972
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:138972/raw/51180464b8acf25f1aff89d26e8e5d14cb9a2332bd5311129d8d0e6f344b9cfe/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_138972`

##### `saos_pl:256767` — SENTENCE I C 1158/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1158/16
- summary_1line: Caselaw corpus record: I C 1158/16.
- external_id: saos:256767
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:256767/raw/8a4cb86630fa240a84a544371e17dde8772ff61c307ddeae7785b7f9cf80f558/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_256767`

##### `saos_pl:446275` — SENTENCE I C 116/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 116/21
- summary_1line: Caselaw corpus record: I C 116/21.
- external_id: saos:446275
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:446275/raw/a9be0262f7e417a06af13eb2a2d6a157b9f06644fabeae10f999e78751950855/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_446275`

##### `saos_pl:203810` — SENTENCE I C 120/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 120/15
- summary_1line: Caselaw corpus record: I C 120/15.
- external_id: saos:203810
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:203810/raw/541372b5639a35a1d4f3e6a6fa06f763acb41622b9b4731a9e698ce402f9dc82/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_203810`

##### `saos_pl:214233` — SENTENCE I C 1201/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1201/15
- summary_1line: Caselaw corpus record: I C 1201/15.
- external_id: saos:214233
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:214233/raw/1f62124294f711d2854e62eac75c877ee770a0f8c813da820f07cf5a1a01c8ff/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_214233`

##### `saos_pl:263787` — SENTENCE I C 121/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 121/16
- summary_1line: Caselaw corpus record: I C 121/16.
- external_id: saos:263787
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:263787/raw/89c925b430e6debadf8f676e7346b495f7d1a77fa7d02822318bbc7bdcdf071b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_263787`

##### `saos_pl:356687` — SENTENCE I C 1232/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1232/14
- summary_1line: Caselaw corpus record: I C 1232/14.
- external_id: saos:356687
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:356687/raw/dbe7253c0bc08271093e03245490f347c9ccfca715c7bdd7d47b95a223a9d481/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_356687`

##### `saos_pl:495693` — SENTENCE I C 1270/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1270/19
- summary_1line: Caselaw corpus record: I C 1270/19.
- external_id: saos:495693
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:495693/raw/7bbe8af98b846523b0c1a9bbc8db6853995e7ee74615b9cf9a8f482869b5e773/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_495693`

##### `saos_pl:137349` — SENTENCE I C 1321/10 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1321/10
- summary_1line: Caselaw corpus record: I C 1321/10.
- external_id: saos:137349
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:137349/raw/623c6ac5644cecbfc9ebc313193614c8b18b26dc6403139b155ff66ff2167f5e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_137349`

##### `saos_pl:433621` — SENTENCE I C 133/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 133/17
- summary_1line: Caselaw corpus record: I C 133/17.
- external_id: saos:433621
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:433621/raw/adb19751bbee1b4f2c7663a5b9b81f345d6d24e279b5ee347adc9b6c19108b77/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_433621`

##### `saos_pl:325063` — SENTENCE I C 1357/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1357/17
- summary_1line: Caselaw corpus record: I C 1357/17.
- external_id: saos:325063
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:325063/raw/2c7ce933575d801de86325559a237442e82cc07c46469478718dbfdb6f8b535c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_325063`

##### `saos_pl:192936` — SENTENCE I C 1391/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1391/15
- summary_1line: Caselaw corpus record: I C 1391/15.
- external_id: saos:192936
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:192936/raw/3078c7fc2f0492fa04591d7e0a0af3e9e8f6063f537a28971b55bed3ca60bbab/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_192936`

##### `saos_pl:495934` — SENTENCE I C 143/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 143/23
- summary_1line: Caselaw corpus record: I C 143/23.
- external_id: saos:495934
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:495934/raw/19b80c553cd53165cd10a709ac7102676d8d88bc9dfbd09b66e3acc1ef7b54d7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_495934`

##### `saos_pl:284237` — SENTENCE I C 1445/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1445/16
- summary_1line: Caselaw corpus record: I C 1445/16.
- external_id: saos:284237
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:284237/raw/ec0f5717df5e3eae14ee0294cd06afae3260b2f0e37f2eb0fbff87eccefc3e33/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_284237`

##### `saos_pl:495957` — SENTENCE I C 145/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 145/22
- summary_1line: Caselaw corpus record: I C 145/22.
- external_id: saos:495957
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:495957/raw/caaf0973de2c0ed7b057a1a0ba1a606566b4efab843f8198b810410fb75e6c7a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_495957`

##### `saos_pl:376869` — SENTENCE I C 147/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 147/16
- summary_1line: Caselaw corpus record: I C 147/16.
- external_id: saos:376869
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:376869/raw/432f95ad1ae0aeb1145afd5f7073a9fb2600703dcb3fa671ac4ec10b63ebc5b7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_376869`

##### `saos_pl:171323` — SENTENCE I C 1519/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1519/11
- summary_1line: Caselaw corpus record: I C 1519/11.
- external_id: saos:171323
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171323/raw/01811c30ea937673bd13bf33017e8c12ea61febcbffd22fac33091ce31cece78/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171323`

##### `saos_pl:396472` — SENTENCE I C 152/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 152/19
- summary_1line: Caselaw corpus record: I C 152/19.
- external_id: saos:396472
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:396472/raw/413edaede86708dec493385f769ddee584db232350510d9751a6709393788b23/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_396472`

##### `saos_pl:330424` — SENTENCE I C 1521/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1521/16
- summary_1line: Caselaw corpus record: I C 1521/16.
- external_id: saos:330424
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:330424/raw/47d9d04e652655e6a59623c9c7d16c39c1a59c41998f7b618d19520694785c2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_330424`

##### `saos_pl:428193` — SENTENCE I C 157/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 157/18
- summary_1line: Caselaw corpus record: I C 157/18.
- external_id: saos:428193
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:428193/raw/de539d4627e4cf2d1d22ce6ce16d45c4e81754f37d0e5328bffeec7ffc9fd9b7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_428193`

##### `saos_pl:199896` — SENTENCE I C 1623/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1623/14
- summary_1line: Caselaw corpus record: I C 1623/14.
- external_id: saos:199896
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:199896/raw/abcd74aa95b4fc27d8acd93033ceaf63f5018864c82d869419b6fbbaaff4287b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_199896`

##### `saos_pl:245688` — SENTENCE I C 1623/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1623/15
- summary_1line: Caselaw corpus record: I C 1623/15.
- external_id: saos:245688
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:245688/raw/bc0de478f29c8d145124166ef1bf33c2b76790e91c1fd9279da4c69d4102eadd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_245688`

##### `saos_pl:298417` — SENTENCE I C 1706/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1706/16
- summary_1line: Caselaw corpus record: I C 1706/16.
- external_id: saos:298417
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:298417/raw/954dba5565718720d56451e3ddd633f483bca8fdf16c23bf5b7667403e8bf833/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_298417`

##### `saos_pl:125372` — SENTENCE I C 176/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 176/14
- summary_1line: Caselaw corpus record: I C 176/14.
- external_id: saos:125372
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:125372/raw/3bcfbf4dfc5c98415f046567ed879a298d00c2d0ad37b278fb8dbbf8934ba006/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_125372`

##### `saos_pl:215121` — SENTENCE I C 1767/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1767/15
- summary_1line: Caselaw corpus record: I C 1767/15.
- external_id: saos:215121
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:215121/raw/fc30dc3a49f02f08db3c09d1b52decfbbcb751d77c99742ab6136d4a0a4c9fd5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_215121`

##### `saos_pl:344058` — SENTENCE I C 1777/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1777/17
- summary_1line: Caselaw corpus record: I C 1777/17.
- external_id: saos:344058
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:344058/raw/d719e793fac172ed9f60590d75ec84c8f63171fada6dc25f3174dab150bec16b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_344058`

##### `saos_pl:470687` — SENTENCE I C 185/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 185/17
- summary_1line: Caselaw corpus record: I C 185/17.
- external_id: saos:470687
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:470687/raw/e88ded8017f98a6831e738e6e7d5f0e2bdef4eaf138b7fb59d75eb3e7a99826a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_470687`

##### `saos_pl:333150` — SENTENCE I C 1858/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 1858/15
- summary_1line: Caselaw corpus record: I C 1858/15.
- external_id: saos:333150
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:333150/raw/08b228e3d4862886d86e48929021ee9e93420b8f78c3e33bb490b8488730d7a7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_333150`

##### `saos_pl:414788` — SENTENCE I C 2031/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2031/19
- summary_1line: Caselaw corpus record: I C 2031/19.
- external_id: saos:414788
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:414788/raw/23d1983c05667d40bac8e7c0553914633b31c60af216ee977e6c0db6442b2d0f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_414788`

##### `saos_pl:442452` — SENTENCE I C 2066/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2066/20
- summary_1line: Caselaw corpus record: I C 2066/20.
- external_id: saos:442452
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:442452/raw/26a1668af8bbf47021ab96281c46805cb1283c306ae6f98d2b38228dfa755936/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_442452`

##### `saos_pl:489175` — SENTENCE I C 209/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 209/21
- summary_1line: Caselaw corpus record: I C 209/21.
- external_id: saos:489175
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:489175/raw/ab2a948c1c1cca1920948f75f4361f792acad87fced9af2f64732b46a1559536/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_489175`

##### `saos_pl:271489` — SENTENCE I C 21/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 21/16
- summary_1line: Caselaw corpus record: I C 21/16.
- external_id: saos:271489
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:271489/raw/c6616a0066775c16d2dc803f6add877a7db5113be02d10cbd44a302d75a0571f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_271489`

##### `saos_pl:138704` — SENTENCE I C 2117/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2117/12
- summary_1line: Caselaw corpus record: I C 2117/12.
- external_id: saos:138704
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:138704/raw/9c35639d09323e77b50b0231857c8b732d08d5d4a5225eb730c176f1f7c1bf37/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_138704`

##### `saos_pl:277346` — SENTENCE I C 2141/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2141/13
- summary_1line: Caselaw corpus record: I C 2141/13.
- external_id: saos:277346
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:277346/raw/6866bf159af18009cf44f475c5e1b864c475f649605f1cbbb1d629b8fd89d558/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_277346`

##### `saos_pl:363093` — SENTENCE I C 215/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 215/18
- summary_1line: Caselaw corpus record: I C 215/18.
- external_id: saos:363093
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:363093/raw/fd8f39e53ce957cdf6ccc9149dc6ae0a923b77dc8918b52efbce536bcf8bd1cc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_363093`

##### `saos_pl:127785` — SENTENCE I C 2185/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2185/13
- summary_1line: Caselaw corpus record: I C 2185/13.
- external_id: saos:127785
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:127785/raw/c89b72898cfbabb2e477153739fc3a83f7ebccb2c90404c3f6fc08cb128acba9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_127785`

##### `saos_pl:497004` — SENTENCE I C 2408/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2408/22
- summary_1line: Caselaw corpus record: I C 2408/22.
- external_id: saos:497004
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:497004/raw/dc72519b6c4b0ef6a09d6c69e12dd636680152c4c264a9326a08d33e7d510137/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_497004`

##### `saos_pl:182087` — SENTENCE I C 2427/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2427/13
- summary_1line: Caselaw corpus record: I C 2427/13.
- external_id: saos:182087
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:182087/raw/3d127d6cc19f552dc0241820f7e42cd4086214620c3958462fd6ba808932d9e5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_182087`

##### `saos_pl:192960` — SENTENCE I C 246/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 246/14
- summary_1line: Caselaw corpus record: I C 246/14.
- external_id: saos:192960
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:192960/raw/46a48a4fb303fec07cb076388520cf102793d0edadd952b0fc55d03936eaa8ef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_192960`

##### `saos_pl:231880` — SENTENCE I C 2471/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2471/15
- summary_1line: Caselaw corpus record: I C 2471/15.
- external_id: saos:231880
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:231880/raw/6df168cd1c5625cbac5f80bb72cf983e9064278288cce899f659c10b9b4bb4d2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_231880`

##### `saos_pl:369450` — SENTENCE I C 249/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 249/18
- summary_1line: Caselaw corpus record: I C 249/18.
- external_id: saos:369450
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:369450/raw/aa8e0feaa21ee2b012dbc8529c346c120467df3595194a3ed16f37e40082563e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_369450`

##### `saos_pl:535542` — SENTENCE I C 253/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 253/23
- summary_1line: Caselaw corpus record: I C 253/23.
- external_id: saos:535542
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:535542/raw/25957829f305f116cf6df1c368e377cc68ba86a829d4dc4b73a33a2a8dcfcff6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_535542`

##### `saos_pl:487744` — SENTENCE I C 259/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 259/20
- summary_1line: Caselaw corpus record: I C 259/20.
- external_id: saos:487744
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:487744/raw/de6ccd39670d6864ce6aceaecb4f78decd1e7a62b739fc56324c775881649d17/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487744`

##### `saos_pl:263320` — SENTENCE I C 265/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 265/15
- summary_1line: Caselaw corpus record: I C 265/15.
- external_id: saos:263320
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:263320/raw/69f5632d85124887690570d3cb5a29a58acd0c9632242b8f4379be3a379283cb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_263320`

##### `saos_pl:410585` — SENTENCE I C 268/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 268/19
- summary_1line: Caselaw corpus record: I C 268/19.
- external_id: saos:410585
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:410585/raw/0cb5f83696b4e658005924e11a7a80efec43c3f5b4d96dc250a82446d5070484/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_410585`

##### `saos_pl:434565` — SENTENCE I C 27/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 27/20
- summary_1line: Caselaw corpus record: I C 27/20.
- external_id: saos:434565
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:434565/raw/230cf5de79729b8171a471f2feb7cdc5b3970efcfcc6f98bd04005c77610d6e0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_434565`

##### `saos_pl:449952` — SENTENCE I C 274/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 274/21
- summary_1line: Caselaw corpus record: I C 274/21.
- external_id: saos:449952
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:449952/raw/971e4cf835d2bc3422b74a58ea166f919c074db3345eee767f0541cd681df17d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_449952`

##### `saos_pl:156926` — SENTENCE I C 275/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 275/13
- summary_1line: Caselaw corpus record: I C 275/13.
- external_id: saos:156926
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:156926/raw/f832650d61ab5490fd7e2cf9669eac965219566d2ad5c46d170bbd0f024182e7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_156926`

##### `saos_pl:236443` — SENTENCE I C 281/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 281/14
- summary_1line: Caselaw corpus record: I C 281/14.
- external_id: saos:236443
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:236443/raw/e4c4189eb3a446db5b271c241ff2a51ec7bbf204a7f2692574efd860db8bc42a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_236443`

##### `saos_pl:182199` — SENTENCE I C 2844/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 2844/13
- summary_1line: Caselaw corpus record: I C 2844/13.
- external_id: saos:182199
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:182199/raw/a0f852cf4a63836fe8622c2c25f29c2f5133f727179ca524bb5e52e71ecf714d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_182199`

##### `saos_pl:454347` — SENTENCE I C 286/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 286/21
- summary_1line: Caselaw corpus record: I C 286/21.
- external_id: saos:454347
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:454347/raw/6a4a91452e872c8daf187f3bd83970450e4a425981a4bb0f699392049bc26067/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_454347`

##### `saos_pl:497332` — SENTENCE I C 286/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 286/22
- summary_1line: Caselaw corpus record: I C 286/22.
- external_id: saos:497332
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:497332/raw/61218abbe3e544c6d7e87f4b8fe8d28151a4a9ca032630d4b522a191afa15a42/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_497332`

##### `saos_pl:484059` — SENTENCE I C 292/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 292/22
- summary_1line: Caselaw corpus record: I C 292/22.
- external_id: saos:484059
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484059/raw/38b20e585f74b9049867b21ab13de95451613f9fb7aae52758b0aa662e849719/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484059`

##### `saos_pl:309681` — SENTENCE I C 293/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 293/17
- summary_1line: Caselaw corpus record: I C 293/17.
- external_id: saos:309681
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:309681/raw/5014b07e24549c41ccffc4bcb8f2c5f0940812813f6cc38907550853152183b3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_309681`

##### `saos_pl:223505` — SENTENCE I C 3/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 3/16
- summary_1line: Caselaw corpus record: I C 3/16.
- external_id: saos:223505
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:223505/raw/7dae3ac53b686d3ecddc63a8008c5c7b6388402fdf5fe3d630a2ed47cda242dc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_223505`

##### `saos_pl:140685` — SENTENCE I C 30/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 30/13
- summary_1line: Caselaw corpus record: I C 30/13.
- external_id: saos:140685
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:140685/raw/8b7dbc13cc5251e45e58506b5e4e2a6ed6d328383983adbb277902dbe349f344/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_140685`

##### `saos_pl:293234` — SENTENCE I C 305/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 305/14
- summary_1line: Caselaw corpus record: I C 305/14.
- external_id: saos:293234
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:293234/raw/fb2cad6cdd306fb5e4e23f53f14ea53cc62011502ce6d3cee327afc41242cd3c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_293234`

##### `saos_pl:333155` — SENTENCE I C 309/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 309/15
- summary_1line: Caselaw corpus record: I C 309/15.
- external_id: saos:333155
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:333155/raw/c58684a317780720c400bf150d7e010793a8b53d754185c2f3a49bc4dc3e5c83/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_333155`

##### `saos_pl:497494` — SENTENCE I C 310/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 310/21
- summary_1line: Caselaw corpus record: I C 310/21.
- external_id: saos:497494
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:497494/raw/e9c01fd56df9a5a17b575317b418aef4f9a9b15b990f1830d0c362d365514b34/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_497494`

##### `saos_pl:142749` — SENTENCE I C 311/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 311/12
- summary_1line: Caselaw corpus record: I C 311/12.
- external_id: saos:142749
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:142749/raw/8de4ca782aa8ce57b9747cf30e19d96a6f113a6727625d27254f981dddc83ad9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_142749`

##### `saos_pl:431428` — SENTENCE I C 3217/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 3217/19
- summary_1line: Caselaw corpus record: I C 3217/19.
- external_id: saos:431428
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:431428/raw/662f8b1e625f82a1c59a84a8c1695cfa43d6968c5a6c8e8471053bf73f368805/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_431428`

##### `saos_pl:482518` — SENTENCE I C 326/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 326/22
- summary_1line: Caselaw corpus record: I C 326/22.
- external_id: saos:482518
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:482518/raw/f1efb55666f617fadbcda3a5d793e7140544098e637d00bc34180602516a0c60/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_482518`

##### `saos_pl:141002` — SENTENCE I C 33/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 33/13
- summary_1line: Caselaw corpus record: I C 33/13.
- external_id: saos:141002
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:141002/raw/042672f1dcf826340397f64254f900af0368320a43af46f3778233c396ac774c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_141002`

##### `saos_pl:497656` — SENTENCE I C 332/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 332/22
- summary_1line: Caselaw corpus record: I C 332/22.
- external_id: saos:497656
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:497656/raw/5b6f59b6dfeaf197274ddde709141fe5c378e6e5f5142f783b66e6b6b3dba296/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_497656`

##### `saos_pl:170755` — SENTENCE I C 3381/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 3381/14
- summary_1line: Caselaw corpus record: I C 3381/14.
- external_id: saos:170755
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:170755/raw/40525d1b6fe80bea9db5078aec0d02982a2dafe43b24972628cba542d410c1ef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_170755`

##### `saos_pl:197181` — SENTENCE I C 352/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 352/14
- summary_1line: Caselaw corpus record: I C 352/14.
- external_id: saos:197181
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:197181/raw/f324edfcdf1ebf85572a39068a0813af69ba9f2d4197ac2051710ab5c134ac83/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_197181`

##### `saos_pl:538882` — SENTENCE I C 367/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 367/21
- summary_1line: Caselaw corpus record: I C 367/21.
- external_id: saos:538882
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:538882/raw/a38e442e8021868ba63275b2c4bc847572aca263f3db7cfd175eed9963502855/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_538882`

##### `saos_pl:497852` — SENTENCE I C 37/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 37/23
- summary_1line: Caselaw corpus record: I C 37/23.
- external_id: saos:497852
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:497852/raw/f6f57153f20bd673eeefd5ada61adc75d3d4431e059a032530ca3b07abf2aaef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_497852`

##### `saos_pl:240939` — SENTENCE I C 374/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 374/15
- summary_1line: Caselaw corpus record: I C 374/15.
- external_id: saos:240939
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:240939/raw/c15fe8a29ec8ba6c967bcad49021093d33d9a0d6b1663ef930ce8b330712762c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_240939`

##### `saos_pl:146213` — SENTENCE I C 379/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 379/13
- summary_1line: Caselaw corpus record: I C 379/13.
- external_id: saos:146213
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:146213/raw/fb94e8d547cf85ac9189d5e95e919b219caacf5da012f9fce5cd05e5f9d7b099/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_146213`

##### `saos_pl:359485` — SENTENCE I C 380/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 380/18
- summary_1line: Caselaw corpus record: I C 380/18.
- external_id: saos:359485
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:359485/raw/8c796dcaa20dfb49ee67db0ed74f36ac9596edb8360729a525b0aa2e75f51e27/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_359485`

##### `saos_pl:417414` — SENTENCE I C 401/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 401/19
- summary_1line: Caselaw corpus record: I C 401/19.
- external_id: saos:417414
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:417414/raw/9a4a906a4eedbc76ddd87f0765dcef02f3975237536ef704379bd1ad44f67bd7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_417414`

##### `saos_pl:522700` — SENTENCE I C 401/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 401/23
- summary_1line: Caselaw corpus record: I C 401/23.
- external_id: saos:522700
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:522700/raw/80529f8a8d0f74137214bb3707719f4e11a0843a6adace8558d2ac892dbb7897/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_522700`

##### `saos_pl:490701` — SENTENCE I C 407/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 407/21
- summary_1line: Caselaw corpus record: I C 407/21.
- external_id: saos:490701
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:490701/raw/67cf8ef5f4c9b4e7269ae954371f2df54c7f96f8062a00a5a4886ce62f70cfa9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_490701`

##### `saos_pl:60058` — SENTENCE I C 425/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 425/12
- summary_1line: Caselaw corpus record: I C 425/12.
- external_id: saos:60058
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:60058/raw/95b4cc63d79778e1ccf80a7c735af2cd79631ae6db206f3c01bef64a8fb56a46/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_60058`

##### `saos_pl:325498` — SENTENCE I C 45/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 45/16
- summary_1line: Caselaw corpus record: I C 45/16.
- external_id: saos:325498
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:325498/raw/91661603b50d4dea240b8185efaf4df821128768b2030f0a7c7ca38e2b78ee45/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_325498`

##### `saos_pl:430911` — SENTENCE I C 456/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 456/20
- summary_1line: Caselaw corpus record: I C 456/20.
- external_id: saos:430911
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:430911/raw/f62236dbdcf0b03f816a7fd16c89eeb4aec78bfbe2e6ddf66f0fffd624797336/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_430911`

##### `saos_pl:325636` — SENTENCE I C 494/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 494/16
- summary_1line: Caselaw corpus record: I C 494/16.
- external_id: saos:325636
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:325636/raw/7cf13ec872440df7bac821891a3595df175b1f3bb58bad650146b0e42f8f6911/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_325636`

##### `saos_pl:70505` — SENTENCE I C 50/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 50/14
- summary_1line: Caselaw corpus record: I C 50/14.
- external_id: saos:70505
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:70505/raw/1e04f9107882803fe3b1e489e33b1cbc64e2b033e09e8c41dd77a9243daac3f0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_70505`

##### `saos_pl:199015` — SENTENCE I C 504/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 504/15
- summary_1line: Caselaw corpus record: I C 504/15.
- external_id: saos:199015
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:199015/raw/acd093ea8f66af1181bfb28e33434627e2e363b01c19a75d552c5b5f4565dcc6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_199015`

##### `saos_pl:481613` — SENTENCE I C 505/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 505/21
- summary_1line: Caselaw corpus record: I C 505/21.
- external_id: saos:481613
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:481613/raw/34cf8fb9bf85230b84ec6d174aec6d510c8e17c5ecf04f13532bf65a3d4384b6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_481613`

##### `saos_pl:211938` — SENTENCE I C 507/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 507/14
- summary_1line: Caselaw corpus record: I C 507/14.
- external_id: saos:211938
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:211938/raw/7b5c91020141ab20c3857070cb191a66c1f9c0a61c0f84d62329f6b76b2a144f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_211938`

##### `saos_pl:140272` — SENTENCE I C 521/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 521/13
- summary_1line: Caselaw corpus record: I C 521/13.
- external_id: saos:140272
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:140272/raw/786425bb426c4f73ee122f8baf8f6dba7d0cbddd18586707c2d75e87d136ebf9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_140272`

##### `saos_pl:260415` — SENTENCE I C 525/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 525/16
- summary_1line: Caselaw corpus record: I C 525/16.
- external_id: saos:260415
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:260415/raw/34baf1be4266394245ae4cb55ec87f483d400fd56d88594c2f9f4f094272f0c7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_260415`

##### `saos_pl:431447` — SENTENCE I C 559/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 559/20
- summary_1line: Caselaw corpus record: I C 559/20.
- external_id: saos:431447
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:431447/raw/c29aa3e4f3dcb64f3bcbff7712f87b81fa22a3b9a94aa31a922c282fd2765ecd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_431447`

##### `saos_pl:528481` — SENTENCE I C 575/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 575/24
- summary_1line: Caselaw corpus record: I C 575/24.
- external_id: saos:528481
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:528481/raw/51b9e04f7d1840ee86d39681099e20dadc3c924942e1a6b40fbfe0251ba26c2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_528481`

##### `saos_pl:142570` — SENTENCE I C 599/10 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 599/10
- summary_1line: Caselaw corpus record: I C 599/10.
- external_id: saos:142570
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:142570/raw/2669a61bd977ca561a02025e6aa4f26df1dd66be2f74bbdb159d699eac996b86/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_142570`

##### `saos_pl:157439` — SENTENCE I C 614/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 614/14
- summary_1line: Caselaw corpus record: I C 614/14.
- external_id: saos:157439
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:157439/raw/2d901dbc6d956e03b19434f45b7218dea96a03562e392e05fc71d7a742675186/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_157439`

##### `saos_pl:529340` — SENTENCE I C 637/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 637/18
- summary_1line: Caselaw corpus record: I C 637/18.
- external_id: saos:529340
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:529340/raw/da605d6985069dbe5e4965a76d0270c5e1c2f047fa66db80c54dee322006a2b7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_529340`

##### `saos_pl:386816` — SENTENCE I C 641/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 641/17
- summary_1line: Caselaw corpus record: I C 641/17.
- external_id: saos:386816
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:386816/raw/66e88998f13ec3623b95dd88b84680e3d06cc62178f74812c3d8e3bb782fe407/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_386816`

##### `saos_pl:408615` — SENTENCE I C 646/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 646/18
- summary_1line: Caselaw corpus record: I C 646/18.
- external_id: saos:408615
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:408615/raw/17be46a932c82819b60bb2debf5babdccf2ac30f5a0272df0069750ead3fb0d9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_408615`

##### `saos_pl:387896` — SENTENCE I C 651/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 651/17
- summary_1line: Caselaw corpus record: I C 651/17.
- external_id: saos:387896
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:387896/raw/30461c1a27b10dcecad595badc631950926cdc7be05e77290f74c41f585171ee/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_387896`

##### `saos_pl:273804` — SENTENCE I C 675/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 675/15
- summary_1line: Caselaw corpus record: I C 675/15.
- external_id: saos:273804
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:273804/raw/725397a4c6bb7cfc10d46542fa5e883f06ff3b788938b089c82a2b539c6e4cc0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_273804`

##### `saos_pl:408181` — SENTENCE I C 676/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 676/19
- summary_1line: Caselaw corpus record: I C 676/19.
- external_id: saos:408181
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:408181/raw/1f8766caefb08d6075f07ab52bc973dfa56107a3b5ab5235e377c8e684b8899b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_408181`

##### `saos_pl:64286` — SENTENCE I C 694/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 694/13
- summary_1line: Caselaw corpus record: I C 694/13.
- external_id: saos:64286
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:64286/raw/5d8aa1d99d8707680adb672d6f1da27611db55f5bd06617e31b76120528beaa9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_64286`

##### `saos_pl:371192` — SENTENCE I C 694/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 694/18
- summary_1line: Caselaw corpus record: I C 694/18.
- external_id: saos:371192
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:371192/raw/ccc314f398508dff0454d3ac752c58dd5998f237d47a9f079b49122d6d25337b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_371192`

##### `saos_pl:370199` — SENTENCE I C 696/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 696/17
- summary_1line: Caselaw corpus record: I C 696/17.
- external_id: saos:370199
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:370199/raw/3c9a68c3e0eb53d373f3cf098e2a60ed7e6b4f169eb821f46a997c93558a67a0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_370199`

##### `saos_pl:177548` — SENTENCE I C 70/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 70/15
- summary_1line: Caselaw corpus record: I C 70/15.
- external_id: saos:177548
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:177548/raw/e4a6ff4b1d3837c3026a707904a64ba1c19236c28c6b7221a0286d5b25927819/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_177548`

##### `saos_pl:386821` — SENTENCE I C 70/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 70/18
- summary_1line: Caselaw corpus record: I C 70/18.
- external_id: saos:386821
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:386821/raw/cd319f28c4f8afb4d7d85ac7a9e02463671054f5c5f84dae31ed9736f1db6c8d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_386821`

##### `saos_pl:218383` — SENTENCE I C 721/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 721/15
- summary_1line: Caselaw corpus record: I C 721/15.
- external_id: saos:218383
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:218383/raw/efed24a9cc432d58bc4e87f73a493ceb08dbfc6129fb94c15f1d174cc9b0bbc8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_218383`

##### `saos_pl:137018` — SENTENCE I C 745/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 745/11
- summary_1line: Caselaw corpus record: I C 745/11.
- external_id: saos:137018
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:137018/raw/ed5f48f68ddfedc819458f2553e5b76ac6c84a14e16f37b0417ed641ed25f0a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_137018`

##### `saos_pl:499244` — SENTENCE I C 749/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 749/23
- summary_1line: Caselaw corpus record: I C 749/23.
- external_id: saos:499244
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:499244/raw/1ec475cbbd2839d5428dfac3459e33375ea9dde41b25cf1d9b93a725f191829e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_499244`

##### `saos_pl:468504` — SENTENCE I C 762/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 762/17
- summary_1line: Caselaw corpus record: I C 762/17.
- external_id: saos:468504
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:468504/raw/c5c956270fc2ff06d37f98f68c9865d88c36f83f594298dd1465ad6827a61ea4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_468504`

##### `saos_pl:322069` — SENTENCE I C 768/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 768/16
- summary_1line: Caselaw corpus record: I C 768/16.
- external_id: saos:322069
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:322069/raw/360572c961420d15b6c746e336345e8beac1d43f393b593ae954115dfd378cd2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_322069`

##### `saos_pl:350520` — SENTENCE I C 780/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 780/17
- summary_1line: Caselaw corpus record: I C 780/17.
- external_id: saos:350520
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:350520/raw/5258aa7d8c0b67d94df6e65867c3c1f535f6a8891290232ed06e62a92adb98d2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_350520`

##### `saos_pl:484516` — SENTENCE I C 787/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 787/21
- summary_1line: Caselaw corpus record: I C 787/21.
- external_id: saos:484516
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484516/raw/2690114699871e4f67aabb66aa2b0ccf5b0a2f09811866da71f9624a22c3684e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484516`

##### `saos_pl:67765` — SENTENCE I C 788/09 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 788/09
- summary_1line: Caselaw corpus record: I C 788/09.
- external_id: saos:67765
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:67765/raw/7157a017ab06f6902e87c49dda58f6dd812cec9743c103c889c4172c8f71b9dd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_67765`

##### `saos_pl:386042` — SENTENCE I C 826/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 826/18
- summary_1line: Caselaw corpus record: I C 826/18.
- external_id: saos:386042
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:386042/raw/b73609bc87b83af4fa834ce807b45b8c332559116aca1b4495103af9c4ed2335/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_386042`

##### `saos_pl:525226` — SENTENCE I C 834/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 834/21
- summary_1line: Caselaw corpus record: I C 834/21.
- external_id: saos:525226
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:525226/raw/3413fecae5065b06318a82309154a6be71b9553b02117ff9e71011dab94d8d4f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_525226`

##### `saos_pl:335174` — SENTENCE I C 835/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 835/17
- summary_1line: Caselaw corpus record: I C 835/17.
- external_id: saos:335174
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:335174/raw/17d3b308a427a32e36aaed877842323728342982084bf3d629bac58d7bf40929/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_335174`

##### `saos_pl:412195` — SENTENCE I C 839/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 839/18
- summary_1line: Caselaw corpus record: I C 839/18.
- external_id: saos:412195
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:412195/raw/f69ef32fce0283a70185bed9a19207d29bb3841be280d6743d56be3237b3742d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_412195`

##### `saos_pl:371198` — SENTENCE I C 840/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 840/18
- summary_1line: Caselaw corpus record: I C 840/18.
- external_id: saos:371198
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:371198/raw/447d743671c500546b7652168442ecfe4e766d7b04ab66f8eee88f33e547fb16/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_371198`

##### `saos_pl:199915` — SENTENCE I C 851/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 851/13
- summary_1line: Caselaw corpus record: I C 851/13.
- external_id: saos:199915
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:199915/raw/a815eefdfcc767401ffe647284d71e0af8764e0e06b42dde6355917ce8818df7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_199915`

##### `saos_pl:499507` — SENTENCE I C 851/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 851/22
- summary_1line: Caselaw corpus record: I C 851/22.
- external_id: saos:499507
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:499507/raw/7754c157b4b2499c2e2582bb775f7a710e271c9ac33b763d2d054f9ddf6bd776/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_499507`

##### `saos_pl:136652` — SENTENCE I C 856/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 856/12
- summary_1line: Caselaw corpus record: I C 856/12.
- external_id: saos:136652
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:136652/raw/1fed85ee6c1d15f4f709c1d9a687ca18f12447e211116d57cc57fdb70ed3d85b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_136652`

##### `saos_pl:437557` — SENTENCE I C 858/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 858/20
- summary_1line: Caselaw corpus record: I C 858/20.
- external_id: saos:437557
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:437557/raw/c4e5836ccf41016b22266a11dedff6e67b03093d9db3c25b228f7b57e29d24d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_437557`

##### `saos_pl:317286` — SENTENCE I C 86/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 86/17
- summary_1line: Caselaw corpus record: I C 86/17.
- external_id: saos:317286
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:317286/raw/c6a21bab482270c1f0e36c13ef1254e4634ed846352c9052c71635315e7ebd32/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_317286`

##### `saos_pl:422426` — SENTENCE I C 87/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 87/20
- summary_1line: Caselaw corpus record: I C 87/20.
- external_id: saos:422426
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:422426/raw/3577b5bf1c9120142062a6d6550b471478b6f349a0493da7f54d24eb68adc9cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_422426`

##### `saos_pl:438319` — SENTENCE I C 87/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 87/20
- summary_1line: Caselaw corpus record: I C 87/20.
- external_id: saos:438319
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:438319/raw/199637e2dc4d8193b7bc4acb0c33be362fb8366fda8c2db9decc9431b6522d2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_438319`

##### `saos_pl:58743` — SENTENCE I C 877/07 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 877/07
- summary_1line: Caselaw corpus record: I C 877/07.
- external_id: saos:58743
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:58743/raw/c705fb5a4bf18d295ef2782c90a034f23406cb0831f491ef060b0f19992b1090/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_58743`

##### `saos_pl:403171` — SENTENCE I C 890/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 890/16
- summary_1line: Caselaw corpus record: I C 890/16.
- external_id: saos:403171
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:403171/raw/4b3905bb72575c5750e6439502be921bca82a397d6f2b0ded6bdcb9c502c0fcd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_403171`

##### `saos_pl:143569` — SENTENCE I C 893/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 893/12
- summary_1line: Caselaw corpus record: I C 893/12.
- external_id: saos:143569
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:143569/raw/5ab0121235764a5542a534d15dd3ff27f4b721f77d41c8d47ea4566d4ebf04be/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_143569`

##### `saos_pl:137856` — SENTENCE I C 901/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 901/12
- summary_1line: Caselaw corpus record: I C 901/12.
- external_id: saos:137856
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:137856/raw/f4633f166b9445c0439422215072c951621d5adb8beff50c0ce8d314c401d271/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_137856`

##### `saos_pl:145662` — SENTENCE I C 907/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 907/13
- summary_1line: Caselaw corpus record: I C 907/13.
- external_id: saos:145662
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:145662/raw/c2559c29aa3d22581979b69533f5839a2812b1b18a5c9db89300b17ac4b42d31/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_145662`

##### `saos_pl:255904` — SENTENCE I C 932/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 932/15
- summary_1line: Caselaw corpus record: I C 932/15.
- external_id: saos:255904
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:255904/raw/a1c6873f8e2c1a77c0194797ccaeea7365e99921b70274968b6f1f14437fe5d9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_255904`

##### `saos_pl:140574` — SENTENCE I C 936/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 936/12
- summary_1line: Caselaw corpus record: I C 936/12.
- external_id: saos:140574
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:140574/raw/3c9254fe679d8393fb83e45a39bc8e9efbe884ecbd46e375072112e26fb04c33/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_140574`

##### `saos_pl:487774` — SENTENCE I C 95/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 95/21
- summary_1line: Caselaw corpus record: I C 95/21.
- external_id: saos:487774
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:487774/raw/ea969ef8945bd5e0b9e867de0afabdd3e5de637fd6a0b79ff406a27dcf8703d5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487774`

##### `saos_pl:366612` — SENTENCE I C 967/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 967/18
- summary_1line: Caselaw corpus record: I C 967/18.
- external_id: saos:366612
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:366612/raw/e3404a76d7a67d49bbd1c7031a0300a0b58696f7a669f3f66f900eab8ebf54a8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_366612`

##### `saos_pl:364920` — SENTENCE I C 98/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 98/16
- summary_1line: Caselaw corpus record: I C 98/16.
- external_id: saos:364920
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:364920/raw/4bccd03f2e3e27552e48942d1da5ea11875fe5734b5169129fa016d45d81fdd2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_364920`

##### `saos_pl:403346` — SENTENCE I C 989/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I C 989/18
- summary_1line: Caselaw corpus record: I C 989/18.
- external_id: saos:403346
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:403346/raw/90c4011ce52129592279fead2dc04ad0adc2e279726dfa2de4205a3759dee92b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_403346`

##### `saos_pl:333685` — SENTENCE I Ca 1/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 1/18
- summary_1line: Caselaw corpus record: I CA 1/18.
- external_id: saos:333685
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:333685/raw/bcb95b3fe27a5454d884de52482a65d81bc2321aa71675a9399d263137656be1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_333685`

##### `saos_pl:316185` — SENTENCE I Ca 119/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 119/17
- summary_1line: Caselaw corpus record: I CA 119/17.
- external_id: saos:316185
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:316185/raw/7ed45ccdf93dc9b85caf4ea76883e22796f9e65229f7dd9780aebda69dad4927/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_316185`

##### `saos_pl:173995` — SENTENCE I Ca 139/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 139/15
- summary_1line: Caselaw corpus record: I CA 139/15.
- external_id: saos:173995
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:173995/raw/8eebedac5cccb4d8f0b0bd228c929403bc9b4f076444991894d2d8a6718ac3e4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_173995`

##### `saos_pl:144471` — SENTENCE I Ca 24/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 24/14
- summary_1line: Caselaw corpus record: I CA 24/14.
- external_id: saos:144471
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:144471/raw/bcebef6906a1b2e2f3987f0c7dde297275f5157e044c5fc1837f3f194d3283d7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_144471`

##### `saos_pl:327858` — SENTENCE I Ca 488/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 488/17
- summary_1line: Caselaw corpus record: I CA 488/17.
- external_id: saos:327858
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:327858/raw/edf80a81b09dfffd627c2121ce19b3a310acb51000039cf982ae784d7dee8ce7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_327858`

##### `saos_pl:360096` — SENTENCE I Ca 56/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 56/18
- summary_1line: Caselaw corpus record: I CA 56/18.
- external_id: saos:360096
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:360096/raw/a295c932aa4186cf53a72ccf1eb3caa9d49ef18d0595e7e594643561f99a3959/original.bin
- same_case_group_id: `same_case:i_ca_56_18`

##### `saos_pl:377518` — SENTENCE I Ca 75/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: I CA 75/19
- summary_1line: Caselaw corpus record: I CA 75/19.
- external_id: saos:377518
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:377518/raw/cc8357555856fbc2b972945bdf2bcea1a645cbfc5869d4e84a7ea025de84b833/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_377518`

##### `saos_pl:500334` — SENTENCE I1 C 156/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 156/22
- summary_1line: Caselaw corpus record: C 156/22.
- external_id: saos:500334
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:500334/raw/9ad2627865dd01feaaa06ba2ecc69dde74075261fa9295ac068266e50bfd9486/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_500334`

##### `saos_pl:271555` — SENTENCE I1 C 1794/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 1794/15
- summary_1line: Caselaw corpus record: C 1794/15.
- external_id: saos:271555
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:271555/raw/3c11489990ac02688a4448bba9deb6bbb7f7eeb8d730a532e7f4f599a2ce02c2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_271555`

##### `saos_pl:520088` — SENTENCE I1 C 217/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 217/23
- summary_1line: Caselaw corpus record: C 217/23.
- external_id: saos:520088
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:520088/raw/e8ce88ced3b828b720b16c7c6c8c47602034c11f1fbf13dbdb6f759d785ea792/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_520088`

##### `saos_pl:537540` — SENTENCE I1 C 346/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 346/24
- summary_1line: Caselaw corpus record: C 346/24.
- external_id: saos:537540
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:537540/raw/620274384dc6b029cd9cc667938771e7b9ae512ff8112507df1959b1a2014b08/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_537540`

##### `saos_pl:346878` — SENTENCE I1 C 408/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 408/17
- summary_1line: Caselaw corpus record: C 408/17.
- external_id: saos:346878
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:346878/raw/479985ee12f748a23f4eea1ae2ae85e109aae2d752edc2f8930939f89f9d275b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_346878`

##### `saos_pl:382539` — SENTENCE I1 C 43/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 43/18
- summary_1line: Caselaw corpus record: C 43/18.
- external_id: saos:382539
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:382539/raw/dc6533efdf07295940767cf2b7a3d198c004fd9744385ef61df65f0c9000fba8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_382539`

##### `saos_pl:377616` — SENTENCE I1 C 643/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 643/16
- summary_1line: Caselaw corpus record: C 643/16.
- external_id: saos:377616
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:377616/raw/bd7e82827ffff856d35fc05e2e9c174b4c57cb32f3825611beee44e19b2cfd4e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_377616`

##### `saos_pl:500376` — SENTENCE I1 C 670/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 670/23
- summary_1line: Caselaw corpus record: C 670/23.
- external_id: saos:500376
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:500376/raw/016ce7e8b50e6dedf7d8900daa4b74d32a20c4175d6569f2616a6b4398a5d014/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_500376`

##### `saos_pl:372433` — SENTENCE I1 C 785/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: C 785/18
- summary_1line: Caselaw corpus record: C 785/18.
- external_id: saos:372433
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:372433/raw/ff5cad9634e16d30f580d6bda747dfd389b857b1326d16087908c187d0c2d9ab/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_372433`

##### `saos_pl:135731` — SENTENCE II AKa 165/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 165/12
- summary_1line: Caselaw corpus record: II AKA 165/12.
- external_id: saos:135731
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:135731/raw/1d243699fea71534bc355464c38c9f300af2b6d767e2c8bbbf5d10c3d55770c4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_135731`

##### `saos_pl:409350` — SENTENCE II AKa 165/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 165/12
- summary_1line: Caselaw corpus record: II AKA 165/12.
- external_id: saos:409350
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:409350/raw/e7df162c30122f5f734eb4f31d5d6d75bda78c61ce1120b31c88039e7c9c6f45/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_409350`

##### `saos_pl:138076` — SENTENCE II AKa 179/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 179/12
- summary_1line: Caselaw corpus record: II AKA 179/12.
- external_id: saos:138076
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:138076/raw/ea09c651365239f3e69a6dd99a5c3a3ac787fd61f342f6bb0fda2ccbbc6b38c0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_138076`

##### `saos_pl:142858` — SENTENCE II AKa 368/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 368/13
- summary_1line: Caselaw corpus record: II AKA 368/13.
- external_id: saos:142858
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:142858/raw/df5a1863fd0ef523657f9d1e151f32106d4a6fed511fb0f2dd12d0ad32c33a0f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_142858`

##### `saos_pl:487206` — SENTENCE II AKa 37/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II AKA 37/21
- summary_1line: Caselaw corpus record: II AKA 37/21.
- external_id: saos:487206
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:487206/raw/ddcdaf9cb2d1b774626d189dea259b4ac6f117780eaacf4116163acb9c4252fb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487206`

##### `saos_pl:255376` — SENTENCE II C 108/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 108/16
- summary_1line: Caselaw corpus record: II C 108/16.
- external_id: saos:255376
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:255376/raw/948e7846610d7063ac3c6aef8c05ea0e6e4d1d02acbbbd7d4ef8ac78c5675412/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_255376`

##### `saos_pl:204485` — SENTENCE II C 1091/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 1091/13
- summary_1line: Caselaw corpus record: II C 1091/13.
- external_id: saos:204485
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:204485/raw/bca3c55db35220c15e44a0e081da186035acc7c5c8e4b7eec70d7b17ef92ac90/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_204485`

##### `saos_pl:438934` — SENTENCE II C 366/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 366/15
- summary_1line: Caselaw corpus record: II C 366/15.
- external_id: saos:438934
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:438934/raw/c89451175e232328a05d2f820485e2ac2c569724f9abb7b60002d2460ac19178/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_438934`

##### `saos_pl:402206` — SENTENCE II C 485/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 485/17
- summary_1line: Caselaw corpus record: II C 485/17.
- external_id: saos:402206
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:402206/raw/0809fcb1a2d14f55fef677f70f4250fb2db54c57be3b54b8a6631b53eefa38d9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_402206`

##### `saos_pl:183175` — SENTENCE II C 52/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 52/14
- summary_1line: Caselaw corpus record: II C 52/14.
- external_id: saos:183175
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:183175/raw/5f94a573ce3bc1680e82440c06d894c8a95267e89552a1fa3294ade013d6409a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_183175`

##### `saos_pl:247626` — SENTENCE II C 589/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 589/12
- summary_1line: Caselaw corpus record: II C 589/12.
- external_id: saos:247626
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:247626/raw/b0e812e18f74ffccbf02947b9624233c1ab533536ab2d6b1e77ba36c90170f20/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_247626`

##### `saos_pl:175246` — SENTENCE II C 636/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 636/14
- summary_1line: Caselaw corpus record: II C 636/14.
- external_id: saos:175246
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:175246/raw/5276287380b203940f847798a5ec6704d41b74d4d848f2c12626a9051ee1916d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_175246`

##### `saos_pl:501535` — SENTENCE II C 833/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 833/19
- summary_1line: Caselaw corpus record: II C 833/19.
- external_id: saos:501535
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:501535/raw/ce1946123c207ce8f2950d54a13ebd16baab607c243bad0ae97a302fff0d038a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_501535`

##### `saos_pl:347829` — SENTENCE II Ca 1063/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1063/17
- summary_1line: Caselaw corpus record: II CA 1063/17.
- external_id: saos:347829
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:347829/raw/1e1a5e248162b155c4a97577d6228cdff28bc4e6ceb48b1e599fa4afc6ed3148/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_347829`

##### `saos_pl:143011` — SENTENCE II Ca 1137/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1137/13
- summary_1line: Caselaw corpus record: II CA 1137/13.
- external_id: saos:143011
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:143011/raw/3a17fc217805e5d6de132ae7fc4920d928b673fcb44788a0b46b30b3a8441ee8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_143011`

##### `saos_pl:142909` — SENTENCE II Ca 1139/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1139/13
- summary_1line: Caselaw corpus record: II CA 1139/13.
- external_id: saos:142909
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:142909/raw/47bbce8d0e4a17a98b38b6ae888d223eb323adcdf9453d7b5921b845317d2988/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_142909`

##### `saos_pl:147156` — SENTENCE II Ca 1165/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1165/12
- summary_1line: Caselaw corpus record: II CA 1165/12.
- external_id: saos:147156
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:147156/raw/c9df4f914c060e6ae9303da7f81225292de2e2b2db8ca0a7f9e124524365713a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_147156`

##### `saos_pl:305090` — SENTENCE II Ca 1200/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1200/15
- summary_1line: Caselaw corpus record: II CA 1200/15.
- external_id: saos:305090
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305090/raw/92da08f2797f98328445a0b5780105f02af0e8ba296fca4756d7f153d37bfc8d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305090`

##### `saos_pl:202848` — SENTENCE II Ca 1213/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1213/14
- summary_1line: Caselaw corpus record: II CA 1213/14.
- external_id: saos:202848
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:202848/raw/3497cc8c1643de9857fe6cdc4358b45cf3c7ef62090d2412c49d8934aab548b6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_202848`

##### `saos_pl:321246` — SENTENCE II Ca 1222/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1222/13
- summary_1line: Caselaw corpus record: II CA 1222/13.
- external_id: saos:321246
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:321246/raw/93973c691a3174937cafc4a604a2ddca11d6af3fe4caa1bb43e63ebbb9ae9279/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_321246`

##### `saos_pl:324637` — SENTENCE II Ca 1262/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1262/17
- summary_1line: Caselaw corpus record: II CA 1262/17.
- external_id: saos:324637
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:324637/raw/a5d634ffff07865d76939960767d5a6b8d44ec3091a6c8aeb845b028b4476000/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_324637`

##### `saos_pl:125023` — SENTENCE II Ca 1263/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1263/14
- summary_1line: Caselaw corpus record: II CA 1263/14.
- external_id: saos:125023
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:125023/raw/a2251c461c4db791f8aa7d030c06028cec744cb0c6658510014a49efdf3fc6c8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_125023`

##### `saos_pl:501650` — SENTENCE II Ca 1313/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1313/23
- summary_1line: Caselaw corpus record: II CA 1313/23.
- external_id: saos:501650
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:501650/raw/ea7bc81c51329c68b631354bf05160f820f45c2cd556caa6b3b25ea61c9bb88a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_501650`

##### `saos_pl:235836` — SENTENCE II Ca 138/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 138/16
- summary_1line: Caselaw corpus record: II CA 138/16.
- external_id: saos:235836
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:235836/raw/7126f5ba807353a8d9d488054b952219ae96da36992495c24752986c8bb6f861/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_235836`

##### `saos_pl:17124` — SENTENCE II Ca 1414/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1414/12
- summary_1line: Caselaw corpus record: II CA 1414/12.
- external_id: saos:17124
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:17124/raw/7cdd00b86e1266a2019675ce746e39778b83e7dfea0d8ccd99bd1b7b13489a1e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_17124`

##### `saos_pl:36268` — SENTENCE II Ca 1466/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1466/13
- summary_1line: Caselaw corpus record: II CA 1466/13.
- external_id: saos:36268
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:36268/raw/aeae1c411b5a411a809fea19e5235bb15fdf83cd0c4bc6a94f90cf1a264c50b6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_36268`

##### `saos_pl:298512` — SENTENCE II Ca 147/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 147/15
- summary_1line: Caselaw corpus record: II CA 147/15.
- external_id: saos:298512
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:298512/raw/0d4e3d912591952dc4800a5ba189e79f15b3dadac62e98e1676439b35bc59be8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_298512`

##### `saos_pl:305177` — SENTENCE II Ca 1499/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1499/15
- summary_1line: Caselaw corpus record: II CA 1499/15.
- external_id: saos:305177
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305177/raw/14ce6d5ae3ad47eee76d2da47c2aefc0e8d184a4fe20498a4433e49826ca962f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305177`

##### `saos_pl:535713` — SENTENCE II Ca 1527/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1527/23
- summary_1line: Caselaw corpus record: II CA 1527/23.
- external_id: saos:535713
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:535713/raw/7d5d56da283e81a3ef5519d1fef2dea634869f5058563df2d0e721fc91e07473/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_535713`

##### `saos_pl:409597` — SENTENCE II Ca 1563/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1563/18
- summary_1line: Caselaw corpus record: II CA 1563/18.
- external_id: saos:409597
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:409597/raw/cdf23083beac5d916cffda4c95e11d18ee2b781512712c2062132298c37ad543/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_409597`

##### `saos_pl:431039` — SENTENCE II Ca 163/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 163/20
- summary_1line: Caselaw corpus record: II CA 163/20.
- external_id: saos:431039
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:431039/raw/9a8ae8b750797a3d85870fa755997342f7c3fd7c483c83fec5177f06f9eb6431/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_431039`

##### `saos_pl:305227` — SENTENCE II Ca 1687/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1687/15
- summary_1line: Caselaw corpus record: II CA 1687/15.
- external_id: saos:305227
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:305227/raw/8b3a9e5f9b4619c2effe10da3a8203de8e2838cfbd93823f79eec2ca861a7d24/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_305227`

##### `saos_pl:296522` — SENTENCE II Ca 170/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 170/14
- summary_1line: Caselaw corpus record: II CA 170/14.
- external_id: saos:296522
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:296522/raw/5dd635720f4764dec1f6864547bc9ab33260d12e938eee8dd5d98c7245d64648/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_296522`

##### `saos_pl:472252` — SENTENCE II Ca 1766/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1766/21
- summary_1line: Caselaw corpus record: II CA 1766/21.
- external_id: saos:472252
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:472252/raw/a41542b5ad9bc8dbe0f338f2a377c8606215d68ee9ac3431e11d857a39c771b0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_472252`

##### `saos_pl:486033` — SENTENCE II Ca 18/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 18/23
- summary_1line: Caselaw corpus record: II CA 18/23.
- external_id: saos:486033
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:486033/raw/6ebf740406c0445f5de971a399c43808c9514ae288dbcf61c41a3f0713a10579/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_486033`

##### `saos_pl:43968` — SENTENCE II Ca 1824/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1824/13
- summary_1line: Caselaw corpus record: II CA 1824/13.
- external_id: saos:43968
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:43968/raw/7c81fd826ef538577865b4a8f9bac316b2980fbbd4d922765d078ac236ba6283/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_43968`

##### `saos_pl:463012` — SENTENCE II Ca 1960/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 1960/21
- summary_1line: Caselaw corpus record: II CA 1960/21.
- external_id: saos:463012
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:463012/raw/cfced50b7248288b8a726492fba6fca8da98d355ccdd6cd1ba4384d4ab92c5bd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_463012`

##### `saos_pl:183247` — SENTENCE II Ca 207/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 207/15
- summary_1line: Caselaw corpus record: II CA 207/15.
- external_id: saos:183247
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:183247/raw/428a493751084815341059e8ff83a258235d1616aad38c6f5bf3efd59523438c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_183247`

##### `saos_pl:361088` — SENTENCE II Ca 2388/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 2388/17
- summary_1line: Caselaw corpus record: II CA 2388/17.
- external_id: saos:361088
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:361088/raw/dc481a3e82603993d34fbac70e016842bbb1687b4328193b54957777b82c8a58/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_361088`

##### `saos_pl:174115` — SENTENCE II Ca 258/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 258/14
- summary_1line: Caselaw corpus record: II CA 258/14.
- external_id: saos:174115
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:174115/raw/2a3def2df25da58d6123e08a7e444b1f099d80da1d861a5f08267f6c89a2a3b3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_174115`

##### `saos_pl:43983` — SENTENCE II Ca 2602/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 2602/13
- summary_1line: Caselaw corpus record: II CA 2602/13.
- external_id: saos:43983
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:43983/raw/1542b0eaefc7fca1021e1c870a53a19b4984216f85d09854b8689ea23d22edaf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_43983`

##### `saos_pl:50162` — SENTENCE II Ca 2620/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 2620/13
- summary_1line: Caselaw corpus record: II CA 2620/13.
- external_id: saos:50162
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:50162/raw/1ce28b95cad2f8c130ea72d9c81dfa0fd74216dc018ba9cf1d42767fcc84c52d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_50162`

##### `saos_pl:217769` — SENTENCE II Ca 2699/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 2699/15
- summary_1line: Caselaw corpus record: II CA 2699/15.
- external_id: saos:217769
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:217769/raw/560c4272db06478e8b9dfa447493cc3b6bd6acd4fd31e97f1c1d33788f2aa45e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_217769`

##### `saos_pl:315327` — SENTENCE II Ca 302/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 302/17
- summary_1line: Caselaw corpus record: II CA 302/17.
- external_id: saos:315327
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:315327/raw/b33e88168a679145d260dce287ef7241cc21fbb6418303077368c787ca6fd546/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_315327`

##### `saos_pl:293319` — SENTENCE II Ca 307/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 307/13
- summary_1line: Caselaw corpus record: II CA 307/13.
- external_id: saos:293319
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:293319/raw/4252405905312963537776b5d3ebfab801b97784ea8671b5c9a996e9fd6f7bcd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_293319`

##### `saos_pl:298569` — SENTENCE II Ca 338/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 338/15
- summary_1line: Caselaw corpus record: II CA 338/15.
- external_id: saos:298569
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:298569/raw/a04ebc7796e083131fe2924c5947b34d64495860edbe46a49975c7aa9031675f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_298569`

##### `saos_pl:10138` — SENTENCE II Ca 34/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 34/13
- summary_1line: Caselaw corpus record: II CA 34/13.
- external_id: saos:10138
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:10138/raw/7b8145cea6725a28fe131c276b3cb1c3c9100716190889cdfd787a2d3b4b8291/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_10138`

##### `saos_pl:16573` — SENTENCE II Ca 357/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 357/13
- summary_1line: Caselaw corpus record: II CA 357/13.
- external_id: saos:16573
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:16573/raw/e097c6c3648b1edea4f2212ab8172dbc432955c30226c3e0ca66b54917568d28/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_16573`

##### `saos_pl:274063` — SENTENCE II Ca 36/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 36/17
- summary_1line: Caselaw corpus record: II CA 36/17.
- external_id: saos:274063
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:274063/raw/522736e2b3852b654db948fae0d61d947f1bd6d6d1d021c57f17e5db33914ed6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_274063`

##### `saos_pl:296775` — SENTENCE II Ca 401/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 401/14
- summary_1line: Caselaw corpus record: II CA 401/14.
- external_id: saos:296775
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:296775/raw/145e52ab2414c1033bf90adb9be079a862fba9856289ab736ab139cdb5824104/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_296775`

##### `saos_pl:31928` — SENTENCE II Ca 421/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 421/13
- summary_1line: Caselaw corpus record: II CA 421/13.
- external_id: saos:31928
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:31928/raw/b84850dc83c1b350071a11d815c2228c65c69348d450eb0f2ded77293d101c11/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_31928`

##### `saos_pl:318152` — SENTENCE II Ca 463/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 463/17
- summary_1line: Caselaw corpus record: II CA 463/17.
- external_id: saos:318152
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:318152/raw/efd1d7c1a76f6733498597fb6d06b245805dcd4129b882a01c41bc7fa7616046/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_318152`

##### `saos_pl:310439` — SENTENCE II Ca 470/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 470/17
- summary_1line: Caselaw corpus record: II CA 470/17.
- external_id: saos:310439
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:310439/raw/84ac7f63986acd2b6d1a5f5e1eb0db574fd2b6a34ad0969723454d01e421ce23/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_310439`

##### `saos_pl:180581` — SENTENCE II Ca 474/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 474/15
- summary_1line: Caselaw corpus record: II CA 474/15.
- external_id: saos:180581
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:180581/raw/7d556b51780be9285c6f14595924e2412388a00cae9f792890658466eec031ab/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_180581`

##### `saos_pl:35521` — SENTENCE II Ca 562/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 562/13
- summary_1line: Caselaw corpus record: II CA 562/13.
- external_id: saos:35521
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:35521/raw/1956777ceef940bdc43e577ea2219eb1f0e2940f1945215d33c2a6d72d771a84/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_35521`

##### `saos_pl:6905` — SENTENCE II Ca 6/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 6/13
- summary_1line: Caselaw corpus record: II CA 6/13.
- external_id: saos:6905
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:6905/raw/7c4cfb7a3c17e6afed23a75df343a2838d2ca51586820bafb9270f2552963c5f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_6905`

##### `saos_pl:44963` — SENTENCE II Ca 602/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 602/13
- summary_1line: Caselaw corpus record: II CA 602/13.
- external_id: saos:44963
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:44963/raw/4c9cabbfcbe2cf72a707740f93f31504f51a7208697760d04cd6561b3ce78947/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_44963`

##### `saos_pl:71705` — SENTENCE II Ca 603/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 603/14
- summary_1line: Caselaw corpus record: II CA 603/14.
- external_id: saos:71705
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:71705/raw/005732c874bea9ea7e96d77d979a7120a7c83997fadec296a130d52db4575d22/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_71705`

##### `saos_pl:9775` — SENTENCE II Ca 627/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 627/12
- summary_1line: Caselaw corpus record: II CA 627/12.
- external_id: saos:9775
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:9775/raw/de56fa359bf9db7d2e7d9d57bd3105dcd3920966250ace167ff24584eb736fb9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_9775`

##### `saos_pl:155761` — SENTENCE II Ca 64/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 64/13
- summary_1line: Caselaw corpus record: II CA 64/13.
- external_id: saos:155761
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155761/raw/3794ea7a31325015ac700cd3f160e161fa9eaed0daf93f0b3d85b0c39669cfa4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155761`

##### `saos_pl:282778` — SENTENCE II Ca 681/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 681/16
- summary_1line: Caselaw corpus record: II CA 681/16.
- external_id: saos:282778
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:282778/raw/e58f2cb510904f7b97f3e22f8df35e7d779e9ac5edcdbc252693684567ca2323/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_282778`

##### `saos_pl:282779` — SENTENCE II Ca 682/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 682/16
- summary_1line: Caselaw corpus record: II CA 682/16.
- external_id: saos:282779
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:282779/raw/7cdcc8a473537873786a44fe6c86492f5bfc56075505ae68d8d60434abd6412a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_282779`

##### `saos_pl:347838` — SENTENCE II Ca 720/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 720/16
- summary_1line: Caselaw corpus record: II CA 720/16.
- external_id: saos:347838
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:347838/raw/5eb060183f50bb11b5bf8aa712dc749daaea01d310e48175fc2ab0e4ee64e268/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_347838`

##### `saos_pl:299499` — SENTENCE II Ca 723/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 723/15
- summary_1line: Caselaw corpus record: II CA 723/15.
- external_id: saos:299499
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:299499/raw/a91055ce3b588806651b69b0f27db8ef511db5de9b52fb121681629e1ad7221c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_299499`

##### `saos_pl:437590` — SENTENCE II Ca 731/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 731/20
- summary_1line: Caselaw corpus record: II CA 731/20.
- external_id: saos:437590
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:437590/raw/eb4d87b923a45db24f02ebc61b8b4bd12c0bcd4688a9fad62dfa7e12269aaf3d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_437590`

##### `saos_pl:356892` — SENTENCE II Ca 736/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 736/17
- summary_1line: Caselaw corpus record: II CA 736/17.
- external_id: saos:356892
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:356892/raw/a8adc26db52328b011be610aa713ac5d003e4d486bfbbe2c45015576fa54f69f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_356892`

##### `saos_pl:183413` — SENTENCE II Ca 742/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 742/15
- summary_1line: Caselaw corpus record: II CA 742/15.
- external_id: saos:183413
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:183413/raw/a511004a5700f06b748cd8405f0fd5ac0209740f13dc082a4b7eab750788ee15/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_183413`

##### `saos_pl:292737` — SENTENCE II Ca 75/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 75/17
- summary_1line: Caselaw corpus record: II CA 75/17.
- external_id: saos:292737
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:292737/raw/e2ca4c9f704833fe3670c9b9c8d3b189cd18ec12e2c6f142500fe26b99dfd6ae/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_292737`

##### `saos_pl:25890` — SENTENCE II Ca 795/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 795/13
- summary_1line: Caselaw corpus record: II CA 795/13.
- external_id: saos:25890
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:25890/raw/fc23a14cf454bab4f9f1dc9a60a0617387ed83720ac3ffce9b7b461193b2a6c1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_25890`

##### `saos_pl:446365` — SENTENCE II Ca 795/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 795/21
- summary_1line: Caselaw corpus record: II CA 795/21.
- external_id: saos:446365
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:446365/raw/868fa7785ece509bb484f0381ef9d126caf7a55b7d8836424d8ad46d2271cd83/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_446365`

##### `saos_pl:292738` — SENTENCE II Ca 8/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 8/17
- summary_1line: Caselaw corpus record: II CA 8/17.
- external_id: saos:292738
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:292738/raw/a905bb2e0116a76ab51abd288b4bb726ad97d46f66631748f39632bcdc668e13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_292738`

##### `saos_pl:299795` — SENTENCE II Ca 816/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 816/15
- summary_1line: Caselaw corpus record: II CA 816/15.
- external_id: saos:299795
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:299795/raw/14c2198df755deb10b17435d92f2eb0f4b5bbbefaec4e9abc2c187a727116dbb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_299795`

##### `saos_pl:265448` — SENTENCE II Ca 819/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 819/16
- summary_1line: Caselaw corpus record: II CA 819/16.
- external_id: saos:265448
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:265448/raw/a20c8e67049fdfd8862f61783d53bfd3b1e99a563b9b24c5be028b2f2544815b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_265448`

##### `saos_pl:516234` — SENTENCE II Ca 819/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 819/17
- summary_1line: Caselaw corpus record: II CA 819/17.
- external_id: saos:516234
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:516234/raw/8b897a87f303b59b6f8985da4eee2bd9f41bc7968e1b2d538ac0d46e635ffad9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_516234`

##### `saos_pl:32730` — SENTENCE II Ca 853/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 853/13
- summary_1line: Caselaw corpus record: II CA 853/13.
- external_id: saos:32730
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:32730/raw/9a9bced28635e032d63ab3d88dd266c2cf84eb1765ee78b9d5ce34140fc32fdd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_32730`

##### `saos_pl:297380` — SENTENCE II Ca 859/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 859/14
- summary_1line: Caselaw corpus record: II CA 859/14.
- external_id: saos:297380
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:297380/raw/c40f4a373c5a8b5b8758c6d252df57406d2b042b4c47b5b0a3809fd544378119/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_297380`

##### `saos_pl:155794` — SENTENCE II Ca 860/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 860/14
- summary_1line: Caselaw corpus record: II CA 860/14.
- external_id: saos:155794
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155794/raw/61aa9312bb4a0d151d4d5de9a52a2d748870d04d940186c8c5496d4086865fd3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155794`

##### `saos_pl:378074` — SENTENCE II Ca 880/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 880/18
- summary_1line: Caselaw corpus record: II CA 880/18.
- external_id: saos:378074
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:378074/raw/5fda4d78188ba8a926e4be70eb4917cce0f119541f78daef52212eaccb265a2b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_378074`

##### `saos_pl:229124` — SENTENCE II Ca 92/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 92/16
- summary_1line: Caselaw corpus record: II CA 92/16.
- external_id: saos:229124
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:229124/raw/4977cbc5e3bf569adbb24dd2ca73f754bf1a3efda87859160c906cb93e7385fb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_229124`

##### `saos_pl:5421` — SENTENCE II Ca 923/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 923/12
- summary_1line: Caselaw corpus record: II CA 923/12.
- external_id: saos:5421
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:5421/raw/9f8b2b251cd97d6b89a712c333899721e72494cef2bcbb3aca48b093651d4c78/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_5421`

##### `saos_pl:438443` — SENTENCE II Ca 941/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 941/20
- summary_1line: Caselaw corpus record: II CA 941/20.
- external_id: saos:438443
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:438443/raw/be3bba5d8ebdbab72af753a72c470a5c2593f57619d6655dddeb4d00d81609e9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_438443`

##### `saos_pl:309523` — SENTENCE II Ca 960/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 960/16
- summary_1line: Caselaw corpus record: II CA 960/16.
- external_id: saos:309523
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:309523/raw/c436a273177c06682c5cc3e8b30e990bd69477a7e1d6fb331a6ec0d47536041c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_309523`

##### `saos_pl:213836` — SENTENCE II Ca 988/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 988/15
- summary_1line: Caselaw corpus record: II CA 988/15.
- external_id: saos:213836
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:213836/raw/e5d2c1458ad121e4b38cbebe84cf306cbe8aa6c066a072f08bc1ec7624c88895/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_213836`

##### `saos_pl:294137` — SENTENCE II Ca 991/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II CA 991/13
- summary_1line: Caselaw corpus record: II CA 991/13.
- external_id: saos:294137
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:294137/raw/70edcf6faaf6483a28066bdc31e205733ee04941d16fa8dc830b5761c979396b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_294137`

##### `saos_pl:277555` — SENTENCE II K 214/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 214/13
- summary_1line: Caselaw corpus record: II K 214/13.
- external_id: saos:277555
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:277555/raw/b106cff8434246845f9a6272854a9a311a34d953361814d97f83636612ae0cd1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_277555`

##### `saos_pl:207362` — SENTENCE II K 56/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 56/12
- summary_1line: Caselaw corpus record: II K 56/12.
- external_id: saos:207362
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:207362/raw/6852471251932ebe0f994968113864c4db36955c156186a180c54f5b22afbf0a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_207362`

##### `saos_pl:189966` — SENTENCE II K 679/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 679/14
- summary_1line: Caselaw corpus record: II K 679/14.
- external_id: saos:189966
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:189966/raw/192efa7038af3a8614826d9b3336edba048a1454c488db15b8fcf71da4466a55/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_189966`

##### `saos_pl:190783` — SENTENCE II K 729/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 729/12
- summary_1line: Caselaw corpus record: II K 729/12.
- external_id: saos:190783
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:190783/raw/bbc67f113b2725f2ae61bbfc40ccad87aa94c4279a1aa6c78ac2ae7dab8f8f83/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_190783`

##### `saos_pl:28087` — SENTENCE II K 844/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 844/13
- summary_1line: Caselaw corpus record: II K 844/13.
- external_id: saos:28087
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:28087/raw/6a49a14b3095b784417964108feb189218697c86d4d01e5ae98a5d7bf3e0dabf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_28087`

##### `saos_pl:61821` — SENTENCE II K 925/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II K 925/11
- summary_1line: Caselaw corpus record: II K 925/11.
- external_id: saos:61821
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:61821/raw/8b1ab44cd6f31fe3302b36811e9ce153d20b6a53a77f2f7b6c1b6d619f495b73/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_61821`

##### `saos_pl:58626` — SENTENCE III APa 21/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III APA 21/14
- summary_1line: Caselaw corpus record: III APA 21/14.
- external_id: saos:58626
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:58626/raw/95c94a1cb8fdc12d534ffb14071e457506d65dedf2e788baf0782db612672455/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_58626`

##### `saos_pl:126914` — SENTENCE III AUa 19/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III AUA 19/14
- summary_1line: Caselaw corpus record: III AUA 19/14.
- external_id: saos:126914
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:126914/raw/0c66e91ab1eaac1dd12df10324b937a9340d62f0eeca7edf7d7c136669e676f4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_126914`

##### `saos_pl:4323` — SENTENCE III AUa 563/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III AUA 563/12
- summary_1line: Caselaw corpus record: III AUA 563/12.
- external_id: saos:4323
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:4323/raw/f46ae2f2135525403948e40b698ee624c6cb2ef815e40ff53e76eab02726fcba/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_4323`

##### `saos_pl:19421` — SENTENCE III AUa 795/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III AUA 795/12
- summary_1line: Caselaw corpus record: III AUA 795/12.
- external_id: saos:19421
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:19421/raw/636cc6a16a7fc927a145554c7719ffa093086b5205f680dc473ad79f0986839d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_19421`

##### `saos_pl:24913` — SENTENCE III AUa 830/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III AUA 830/12
- summary_1line: Caselaw corpus record: III AUA 830/12.
- external_id: saos:24913
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:24913/raw/b587d4ad98bad48e0a16a8da87a56f903b279f0f4e76a20d8146c55e2772900e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_24913`

##### `saos_pl:253574` — SENTENCE III C 1086/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 1086/15
- summary_1line: Caselaw corpus record: III C 1086/15.
- external_id: saos:253574
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:253574/raw/7f4ab300a638c1ddffe9b81b0d4abeb0fc9661c7364eee4d65794740953c8cf6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_253574`

##### `saos_pl:207400` — SENTENCE III C 127/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 127/14
- summary_1line: Caselaw corpus record: III C 127/14.
- external_id: saos:207400
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:207400/raw/8d2bb18c173a25922943e44009f5e60fda50f03b36b7e195a1dd3ebc841b751e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_207400`

##### `saos_pl:378676` — SENTENCE III C 1284/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 1284/15
- summary_1line: Caselaw corpus record: III C 1284/15.
- external_id: saos:378676
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:378676/raw/f4490c52097b5013e05fd5f64f9ee18ab6cf9894c1b62e1bd1d8ce90febee070/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_378676`

##### `saos_pl:473816` — SENTENCE III C 1291/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 1291/19
- summary_1line: Caselaw corpus record: III C 1291/19.
- external_id: saos:473816
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:473816/raw/bc4e4c8730f3141b409af7625d2ebe5f0aaef210ce1227218974965d00f898ed/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_473816`

##### `saos_pl:252144` — SENTENCE III C 1805/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 1805/13
- summary_1line: Caselaw corpus record: III C 1805/13.
- external_id: saos:252144
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:252144/raw/0dcfaf8fb6382c31959fceb6cb6c920ce53e323d9940bc7e35487f281a4447c7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_252144`

##### `saos_pl:184811` — SENTENCE III C 2610/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 2610/13
- summary_1line: Caselaw corpus record: III C 2610/13.
- external_id: saos:184811
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:184811/raw/162099b3b5ee49bf19f8b65ebbd35630f94726155c32a73166165ad128028d0a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_184811`

##### `saos_pl:478416` — SENTENCE III C 377/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 377/21
- summary_1line: Caselaw corpus record: III C 377/21.
- external_id: saos:478416
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:478416/raw/fa40b72a57f6cef208508b49c6031779b575ba582e500ee4892c5f654a8a848c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_478416`

##### `saos_pl:464880` — SENTENCE III C 404/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 404/21
- summary_1line: Caselaw corpus record: III C 404/21.
- external_id: saos:464880
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:464880/raw/9911be144234520f7b0c3a9011366ef1d422038194d27990fe2be768d4617ca7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_464880`

##### `saos_pl:491803` — SENTENCE III C 513/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 513/22
- summary_1line: Caselaw corpus record: III C 513/22.
- external_id: saos:491803
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:491803/raw/afc918ddfc83b4cc016a6ad964b9a5331f122531a5a44c5afafdcb5a4aa2bd89/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_491803`

##### `saos_pl:505374` — SENTENCE III C 520/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 520/22
- summary_1line: Caselaw corpus record: III C 520/22.
- external_id: saos:505374
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:505374/raw/fda2eae3a0c23fd4e4dfcd869ab562f812949e1719e276580052f6967e369e1e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_505374`

##### `saos_pl:529364` — SENTENCE III C 551/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 551/24
- summary_1line: Caselaw corpus record: III C 551/24.
- external_id: saos:529364
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:529364/raw/15cad8a9303317a4ef3c3a32d7c587dc86e518617bf35396b1e0ff7d7f13fef1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_529364`

##### `saos_pl:190000` — SENTENCE III C 647/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 647/13
- summary_1line: Caselaw corpus record: III C 647/13.
- external_id: saos:190000
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:190000/raw/220535621b36b2e48156d729c57afc7b643c6e59722b6d6fb1e437068f009b0d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_190000`

##### `saos_pl:505413` — SENTENCE III C 75/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 75/23
- summary_1line: Caselaw corpus record: III C 75/23.
- external_id: saos:505413
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:505413/raw/efd99d93cdfa17997ec11ab23d7ca6ae779f13dc5b21f053b7840cc277ca643b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_505413`

##### `saos_pl:491701` — SENTENCE III C 790/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 790/22
- summary_1line: Caselaw corpus record: III C 790/22.
- external_id: saos:491701
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:491701/raw/a7a4a68a02161bddfe29211f68f6cab16d5510262e4e868e2b0e4f8483192ad3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_491701`

##### `saos_pl:311458` — SENTENCE III C 796/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 796/16
- summary_1line: Caselaw corpus record: III C 796/16.
- external_id: saos:311458
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:311458/raw/e9649321eba7f06cb26742ab975d0e7bc7978423e0ad387e6838a87c29ec5643/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_311458`

##### `saos_pl:323675` — SENTENCE III C 813/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 813/15
- summary_1line: Caselaw corpus record: III C 813/15.
- external_id: saos:323675
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:323675/raw/58d76e349bd42cbeb6982fe7b39c718708e0bdc4e167e8e74c509430c4c9d89d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_323675`

##### `saos_pl:468537` — SENTENCE III C 966/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 966/21
- summary_1line: Caselaw corpus record: III C 966/21.
- external_id: saos:468537
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:468537/raw/1f37dcc06ce701004f6abd1770f6168e19fbb32d88db08e3a4f7624d26576c47/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_468537`

##### `saos_pl:242030` — SENTENCE III C 976/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III C 976/12
- summary_1line: Caselaw corpus record: III C 976/12.
- external_id: saos:242030
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:242030/raw/6eb20245d05f50224d318b9c43fcb574784c904f8796ca6f37099c660755a565/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_242030`

##### `saos_pl:156394` — SENTENCE III Ca 1021/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1021/14
- summary_1line: Caselaw corpus record: III CA 1021/14.
- external_id: saos:156394
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:156394/raw/39d2dc429161ee920303c643b9b135a57682209657558f5c7ce7c51019132c35/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_156394`

##### `saos_pl:464889` — SENTENCE III Ca 1036/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1036/20
- summary_1line: Caselaw corpus record: III CA 1036/20.
- external_id: saos:464889
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:464889/raw/187da48c3bb6932e35724de065cf1770f9eda3d40054f92973a3d78771c80f86/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_464889`

##### `saos_pl:216185` — SENTENCE III Ca 1073/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1073/15
- summary_1line: Caselaw corpus record: III CA 1073/15.
- external_id: saos:216185
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:216185/raw/83b4c110d1e2ed9f1fb414329b4c6e0883f799d3cc09fe3a52aefb60f72d144d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_216185`

##### `saos_pl:155931` — SENTENCE III Ca 1087/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1087/14
- summary_1line: Caselaw corpus record: III CA 1087/14.
- external_id: saos:155931
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155931/raw/42b3e338d6a1ce8970d95d80507a37e59d0ce829d66adde0dcd7929ba316abcf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155931`

##### `saos_pl:439013` — SENTENCE III Ca 1105/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1105/19
- summary_1line: Caselaw corpus record: III CA 1105/19.
- external_id: saos:439013
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:439013/raw/818e3ab30af13ea5273b8880dec5141c3e188bd650e663f7beb5e41012b5c5de/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_439013`

##### `saos_pl:464890` — SENTENCE III Ca 1140/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1140/20
- summary_1line: Caselaw corpus record: III CA 1140/20.
- external_id: saos:464890
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:464890/raw/f203d8cbe17b0ca46698c8a0d31417c4bfe3dc8accca51f82a8e5a7616eb9721/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_464890`

##### `saos_pl:262221` — SENTENCE III Ca 1162/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1162/16
- summary_1line: Caselaw corpus record: III CA 1162/16.
- external_id: saos:262221
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:262221/raw/b324f09a4d05ab038f0be2883c226dd983d7f6928328b5d0611ecc0b8ca31986/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_262221`

##### `saos_pl:327956` — SENTENCE III Ca 1206/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1206/17
- summary_1line: Caselaw corpus record: III CA 1206/17.
- external_id: saos:327956
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:327956/raw/e62570bec488c48ae1cfeb0a04adf836724b2a934f333bc69719c86347b57627/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_327956`

##### `saos_pl:194479` — SENTENCE III Ca 1211/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1211/15
- summary_1line: Caselaw corpus record: III CA 1211/15.
- external_id: saos:194479
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194479/raw/e3201fbfb42ba2fe28087e09647cbfa9b9475494dce43d79e474f656a4e060ea/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194479`

##### `saos_pl:158963` — SENTENCE III Ca 1276/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1276/14
- summary_1line: Caselaw corpus record: III CA 1276/14.
- external_id: saos:158963
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:158963/raw/786936f07ee4fc5b2182965346a555ffc0942376cbca18ee7c08f3643bd0c0b4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_158963`

##### `saos_pl:155959` — SENTENCE III Ca 128/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 128/14
- summary_1line: Caselaw corpus record: III CA 128/14.
- external_id: saos:155959
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155959/raw/6efa31cae4644cc0777e38a4baf5aedc985fc5a6d4dcb4e967ddd2323870af76/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155959`

##### `saos_pl:156432` — SENTENCE III Ca 1297/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1297/14
- summary_1line: Caselaw corpus record: III CA 1297/14.
- external_id: saos:156432
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:156432/raw/d59821ebbec5d7505acfb9b3993645424d6db785eef6ad16e3a2e56ec567c456/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_156432`

##### `saos_pl:156433` — SENTENCE III Ca 1298/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1298/14
- summary_1line: Caselaw corpus record: III CA 1298/14.
- external_id: saos:156433
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:156433/raw/781e7ae0176b08807b012bbcdcc9a88f114f1056de7c473e407f19de88a5c459/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_156433`

##### `saos_pl:134735` — SENTENCE III Ca 134/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 134/14
- summary_1line: Caselaw corpus record: III CA 134/14.
- external_id: saos:134735
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:134735/raw/cab5ccf7e0e3f2e77d3be1d884a626d10fc0a8fe94e09600d45346a5f66f9c08/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_134735`

##### `saos_pl:61187` — SENTENCE III Ca 1346/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1346/13
- summary_1line: Caselaw corpus record: III CA 1346/13.
- external_id: saos:61187
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:61187/raw/4e03625e955f5339150f6475f0b4d837f14cf8d33c1e2beda5a33efe72192066/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_61187`

##### `saos_pl:194591` — SENTENCE III Ca 1364/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1364/15
- summary_1line: Caselaw corpus record: III CA 1364/15.
- external_id: saos:194591
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194591/raw/8f679057aed0c9b058005c5c6cf0a805f77dcf0652e08163e5febd32efc3fb06/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194591`

##### `saos_pl:388929` — SENTENCE III Ca 1384/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1384/18
- summary_1line: Caselaw corpus record: III CA 1384/18.
- external_id: saos:388929
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:388929/raw/85242798b4e28c242af6f92c9ce29812549fbeea562ff7e5f7e9212b75b47bc4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_388929`

##### `saos_pl:230875` — SENTENCE III Ca 1401/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1401/15
- summary_1line: Caselaw corpus record: III CA 1401/15.
- external_id: saos:230875
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:230875/raw/00a9a1a89cc7a80ccd14d6ce33843baa902fafec93525c8fb1bab15ec29307a1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_230875`

##### `saos_pl:203170` — SENTENCE III Ca 1441/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1441/15
- summary_1line: Caselaw corpus record: III CA 1441/15.
- external_id: saos:203170
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:203170/raw/6d8b219d55589ac7b2763c9cdfef6f1eceef658aa1e48f8645ac5b1def3035a4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_203170`

##### `saos_pl:207987` — SENTENCE III Ca 1442/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1442/15
- summary_1line: Caselaw corpus record: III CA 1442/15.
- external_id: saos:207987
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:207987/raw/d54f5affb98f1219af3bbe4f9732e43185424b84c73f0c4d5dfe6d3150d793d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_207987`

##### `saos_pl:246478` — SENTENCE III Ca 1445/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1445/13
- summary_1line: Caselaw corpus record: III CA 1445/13.
- external_id: saos:246478
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:246478/raw/82a79f20448dea5f6faec5b25aabe7add9da6d91165021d220f5b3f35241cfa2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_246478`

##### `saos_pl:268582` — SENTENCE III Ca 1509/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1509/16
- summary_1line: Caselaw corpus record: III CA 1509/16.
- external_id: saos:268582
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:268582/raw/69b6b4db642cfb5d6b3f67961a858d17f83f099a8982c9d83525d9f471db43a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_268582`

##### `saos_pl:216188` — SENTENCE III Ca 1516/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1516/15
- summary_1line: Caselaw corpus record: III CA 1516/15.
- external_id: saos:216188
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:216188/raw/eb479fa69cae722abb436c1a247d5142596f320d02ea0bc26a5c1391f1bdfac9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_216188`

##### `saos_pl:215367` — SENTENCE III Ca 1517/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1517/15
- summary_1line: Caselaw corpus record: III CA 1517/15.
- external_id: saos:215367
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:215367/raw/e5184a1930dd786e13af5953f527e62be511330ed56c90ead6c70a5611529297/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_215367`

##### `saos_pl:129842` — SENTENCE III Ca 152/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 152/14
- summary_1line: Caselaw corpus record: III CA 152/14.
- external_id: saos:129842
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:129842/raw/7e57e67a52f20e46361c8a49465e1db23bf3bab9d24383fae001952b641b522e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_129842`

##### `saos_pl:159499` — SENTENCE III Ca 1530/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1530/14
- summary_1line: Caselaw corpus record: III CA 1530/14.
- external_id: saos:159499
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:159499/raw/db7d360a01025389c670c53e3a0624c12f5c3d11b5b75e5b622cb623add888c9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_159499`

##### `saos_pl:382680` — SENTENCE III Ca 1535/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1535/18
- summary_1line: Caselaw corpus record: III CA 1535/18.
- external_id: saos:382680
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:382680/raw/6a83f3cff8445d8792de12754ffcd74996b156b30ad68445a6bd2e8d8564e8cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_382680`

##### `saos_pl:57195` — SENTENCE III Ca 1552/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1552/13
- summary_1line: Caselaw corpus record: III CA 1552/13.
- external_id: saos:57195
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:57195/raw/d9eb3cdf77160aeb211b6220cb8b5b497153894cc31429dbd9a5d959da19b2e5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_57195`

##### `saos_pl:207992` — SENTENCE III Ca 1578/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1578/15
- summary_1line: Caselaw corpus record: III CA 1578/15.
- external_id: saos:207992
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:207992/raw/d37e1efe66af43d1934696d20d04711d39657d86797e1967e6c4f4a7254a7fc2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_207992`

##### `saos_pl:208241` — SENTENCE III Ca 1583/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1583/15
- summary_1line: Caselaw corpus record: III CA 1583/15.
- external_id: saos:208241
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:208241/raw/c8348e4f5ccbc2bd8726ca84ade7785e5d3c189a14ecffd400ef146843faf834/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_208241`

##### `saos_pl:210324` — SENTENCE III Ca 1606/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1606/15
- summary_1line: Caselaw corpus record: III CA 1606/15.
- external_id: saos:210324
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:210324/raw/7b42e3b29b0dd71323179b94b52adff714d14393e45f37d55af991913ca5b942/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_210324`

##### `saos_pl:56254` — SENTENCE III Ca 1633/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1633/13
- summary_1line: Caselaw corpus record: III CA 1633/13.
- external_id: saos:56254
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:56254/raw/1350201e416684f05a94fc2cebed04125fd4726c2936509952c2f4d8b95c2a08/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_56254`

##### `saos_pl:230880` — SENTENCE III Ca 164/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 164/16
- summary_1line: Caselaw corpus record: III CA 164/16.
- external_id: saos:230880
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:230880/raw/5c27ee5b50e78a1acaf0030f3fa19fe84cdd18d9d849640c641625f666e1485f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_230880`

##### `saos_pl:215373` — SENTENCE III Ca 1748/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1748/15
- summary_1line: Caselaw corpus record: III CA 1748/15.
- external_id: saos:215373
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:215373/raw/adcf88bc6064f225188a61d98f3e84c4d043549d0c3bbfcdd6e1f8449c58f96c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_215373`

##### `saos_pl:210326` — SENTENCE III Ca 1755/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1755/15
- summary_1line: Caselaw corpus record: III CA 1755/15.
- external_id: saos:210326
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:210326/raw/20f2e799bafe07130e75f5c4b3cd4d663a191b2600d98cd22925abb5845b4b1b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_210326`

##### `saos_pl:279059` — SENTENCE III Ca 1789/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1789/16
- summary_1line: Caselaw corpus record: III CA 1789/16.
- external_id: saos:279059
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:279059/raw/55a1bba46298446e679fc9b6b2d50acb3fdc70ab68ae7c22db79875e6e99e482/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_279059`

##### `saos_pl:277775` — SENTENCE III Ca 1955/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 1955/16
- summary_1line: Caselaw corpus record: III CA 1955/16.
- external_id: saos:277775
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:277775/raw/4fabc49faabfe21a299a2840be71670b1bbacffa065fe710777e488d1ec8b518/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_277775`

##### `saos_pl:125770` — SENTENCE III Ca 200/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 200/14
- summary_1line: Caselaw corpus record: III CA 200/14.
- external_id: saos:125770
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:125770/raw/eae404fed5f9a224b3c9b3f77c95c85894a802b1abe03b7c7d2c32284d1e78f5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_125770`

##### `saos_pl:484884` — SENTENCE III Ca 204/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 204/22
- summary_1line: Caselaw corpus record: III CA 204/22.
- external_id: saos:484884
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:484884/raw/23df7a7f5408af7a3d1e4bc3ca368f45b3100b348048fade45bc71b2ce00a0eb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_484884`

##### `saos_pl:219349` — SENTENCE III Ca 205/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 205/16
- summary_1line: Caselaw corpus record: III CA 205/16.
- external_id: saos:219349
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:219349/raw/2ca8e29957f26f1650060e809f92f04e8154fb14a3734091bc03f483ff56ffb6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_219349`

##### `saos_pl:61311` — SENTENCE III Ca 226/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 226/14
- summary_1line: Caselaw corpus record: III CA 226/14.
- external_id: saos:61311
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:61311/raw/5eaa58815d5c308432878d5e7b352a95224b1b2e189db3a937aa3669503f2155/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_61311`

##### `saos_pl:184997` — SENTENCE III Ca 325/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 325/15
- summary_1line: Caselaw corpus record: III CA 325/15.
- external_id: saos:184997
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:184997/raw/db1773e233c2a553082c775496dabad12a06a0880f94e7bd5350f35d8135d5eb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_184997`

##### `saos_pl:230927` — SENTENCE III Ca 350/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 350/16
- summary_1line: Caselaw corpus record: III CA 350/16.
- external_id: saos:230927
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:230927/raw/ddecaa4fb360b34b5c1406c2d49f31bf97d2039f022c448974bc8857bbb22b24/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_230927`

##### `saos_pl:227272` — SENTENCE III Ca 351/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 351/16
- summary_1line: Caselaw corpus record: III CA 351/16.
- external_id: saos:227272
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:227272/raw/4449e5349e8c7dd2ff58c5cd3689c98c5c0600d887d9ca73f3c2551bdfc43435/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_227272`

##### `saos_pl:225643` — SENTENCE III Ca 352/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 352/16
- summary_1line: Caselaw corpus record: III CA 352/16.
- external_id: saos:225643
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:225643/raw/21f11414b55c5c7eaf51f63f802504aa7729ea2941f263ba17e6ef7654721c7a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_225643`

##### `saos_pl:67487` — SENTENCE III Ca 353/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 353/14
- summary_1line: Caselaw corpus record: III CA 353/14.
- external_id: saos:67487
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:67487/raw/3965e80996b55476bb7abab4a9f9da9125d2fe70510c53094f226d0d7fd7c05c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_67487`

##### `saos_pl:159539` — SENTENCE III Ca 393/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 393/14
- summary_1line: Caselaw corpus record: III CA 393/14.
- external_id: saos:159539
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:159539/raw/5ad3425ac4041262eb7d97eef572f3f0ea34b77fa510e83524f87502225e8fbc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_159539`

##### `saos_pl:232225` — SENTENCE III Ca 393/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 393/16
- summary_1line: Caselaw corpus record: III CA 393/16.
- external_id: saos:232225
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:232225/raw/8ebe707859b39bc6d444d06919cc47632d85df097116904d7e706300e3ac1d1d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_232225`

##### `saos_pl:225645` — SENTENCE III Ca 409/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 409/16
- summary_1line: Caselaw corpus record: III CA 409/16.
- external_id: saos:225645
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:225645/raw/b4598de5448de3998b4af330c14752d48c8e2f695b301ecdbb8fc7ba55f7be25/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_225645`

##### `saos_pl:172220` — SENTENCE III Ca 424/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 424/15
- summary_1line: Caselaw corpus record: III CA 424/15.
- external_id: saos:172220
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:172220/raw/41157fd7d0c26d3fcf966e4512176482a0527d562beac6161e5a74b47e0e53f0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_172220`

##### `saos_pl:370010` — SENTENCE III Ca 429/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 429/18
- summary_1line: Caselaw corpus record: III CA 429/18.
- external_id: saos:370010
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:370010/raw/be1ca5ec1ca0d7a5486abcafd3be015c5cbc3d75930a29f4b20594bf752666de/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_370010`

##### `saos_pl:64613` — SENTENCE III Ca 454/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 454/14
- summary_1line: Caselaw corpus record: III CA 454/14.
- external_id: saos:64613
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:64613/raw/2b414a9e364dd73309ccae812c46eb97730b083e14656adf0aabd7c3569f956c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_64613`

##### `saos_pl:237558` — SENTENCE III Ca 480/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 480/16
- summary_1line: Caselaw corpus record: III CA 480/16.
- external_id: saos:237558
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:237558/raw/c3ae9c9c9906c13b7738dad11a32b54422e2c43083f20c7158326ebb425a698f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_237558`

##### `saos_pl:134750` — SENTENCE III Ca 483/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 483/14
- summary_1line: Caselaw corpus record: III CA 483/14.
- external_id: saos:134750
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:134750/raw/29a51b2d8a5c0249906acecb49ad98e73af602eee2b5d1f50107be702b4b61fb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_134750`

##### `saos_pl:185174` — SENTENCE III Ca 484/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 484/15
- summary_1line: Caselaw corpus record: III CA 484/15.
- external_id: saos:185174
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:185174/raw/55393138cefa5d1d54d309bc18ce140875b65c8beffe6121246de42d627ec12a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_185174`

##### `saos_pl:246497` — SENTENCE III Ca 491/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 491/16
- summary_1line: Caselaw corpus record: III CA 491/16.
- external_id: saos:246497
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:246497/raw/e386f185b19fbc12b6aef8a90a663548867ce7f05660877429df4e660b1bd982/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_246497`

##### `saos_pl:439782` — SENTENCE III Ca 511/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 511/19
- summary_1line: Caselaw corpus record: III CA 511/19.
- external_id: saos:439782
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:439782/raw/d736909d404af7f215a96b0117ce7a6c5b16d45975104dc1e1f8ee9bb123cc60/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_439782`

##### `saos_pl:68023` — SENTENCE III Ca 528/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 528/14
- summary_1line: Caselaw corpus record: III CA 528/14.
- external_id: saos:68023
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:68023/raw/a92d4520454efa0b4f94cffa0bc59d0aee89243c345c2b438225770ea34159ad/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_68023`

##### `saos_pl:368361` — SENTENCE III Ca 528/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 528/18
- summary_1line: Caselaw corpus record: III CA 528/18.
- external_id: saos:368361
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:368361/raw/772c11f5e5137c776a1b69dc3d0db82063f43d4fc677678a9b5f794b1e208a5c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_368361`

##### `saos_pl:61317` — SENTENCE III Ca 547/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 547/14
- summary_1line: Caselaw corpus record: III CA 547/14.
- external_id: saos:61317
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:61317/raw/e50b8f70de06aca4446da0f1a1a941c191049c64ead8d2bc52a2b4a350697bcd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_61317`

##### `saos_pl:134431` — SENTENCE III Ca 570/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 570/14
- summary_1line: Caselaw corpus record: III CA 570/14.
- external_id: saos:134431
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:134431/raw/74f2de5b56d6acf4fd8bf55576c3dcd926863ddf93a053c8bd22b254e5037e7a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_134431`

##### `saos_pl:246982` — SENTENCE III Ca 592/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 592/16
- summary_1line: Caselaw corpus record: III CA 592/16.
- external_id: saos:246982
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:246982/raw/3ae27e9ec3899cf74832c1ed25b770f35fa0d91a105b2699f43cc60330c6dd00/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_246982`

##### `saos_pl:125778` — SENTENCE III Ca 646/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 646/14
- summary_1line: Caselaw corpus record: III CA 646/14.
- external_id: saos:125778
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:125778/raw/1f686ad81738756ab8e777ba9bd93e38ba2502ce318109713d835ad6f84daeac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_125778`

##### `saos_pl:233544` — SENTENCE III Ca 655/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 655/16
- summary_1line: Caselaw corpus record: III CA 655/16.
- external_id: saos:233544
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:233544/raw/4b839b0cca09d6aa5d2991f24d69173dc3c9c45ea5e5957a692117a027f0668a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_233544`

##### `saos_pl:156523` — SENTENCE III Ca 782/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 782/14
- summary_1line: Caselaw corpus record: III CA 782/14.
- external_id: saos:156523
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:156523/raw/4208dab8d96bcf16a3f8fff65b61dd7e26448481e42506e90328505eb685c9ef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_156523`

##### `saos_pl:67856` — SENTENCE III Ca 786/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 786/14
- summary_1line: Caselaw corpus record: III CA 786/14.
- external_id: saos:67856
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:67856/raw/8a11616fbbda888c457dcc80f86626a2ab922949a729fe19bb024b367a281130/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_67856`

##### `saos_pl:242360` — SENTENCE III Ca 789/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 789/16
- summary_1line: Caselaw corpus record: III CA 789/16.
- external_id: saos:242360
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:242360/raw/8bf09c2013db4a0231afb0dbd5a7fe149b0472b7514fcd69d6d836181a335659/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_242360`

##### `saos_pl:415222` — SENTENCE III Ca 808/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 808/19
- summary_1line: Caselaw corpus record: III CA 808/19.
- external_id: saos:415222
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:415222/raw/e75ffb83eba81596bfaac161b048b87e0dff34d71f1effbffb765602e5eccd8b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_415222`

##### `saos_pl:185517` — SENTENCE III Ca 915/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 915/14
- summary_1line: Caselaw corpus record: III CA 915/14.
- external_id: saos:185517
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:185517/raw/ca39aef462f895aa04c09c91652d95912864501875d83fb5be106af1086a0270/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_185517`

##### `saos_pl:255491` — SENTENCE III Ca 916/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 916/16
- summary_1line: Caselaw corpus record: III CA 916/16.
- external_id: saos:255491
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:255491/raw/3250dc9f3f3fc172c91cfacbd3350082761c72c33215b1b811a558280af124ac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_255491`

##### `saos_pl:159540` — SENTENCE III Ca 959/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 959/14
- summary_1line: Caselaw corpus record: III CA 959/14.
- external_id: saos:159540
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:159540/raw/29ac8edbc585cc4f1f02518a5e7be44032a122586c49de973b3e45b27bbaec7f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_159540`

##### `saos_pl:210342` — SENTENCE III Ca 998/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III CA 998/15
- summary_1line: Caselaw corpus record: III CA 998/15.
- external_id: saos:210342
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:210342/raw/edd6d782a011bc705b652b367167a82cccce9c60526d58b3b6e2dd169e21e03c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_210342`

##### `saos_pl:328283` — SENTENCE III K 238/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III K 238/16
- summary_1line: Caselaw corpus record: III K 238/16.
- external_id: saos:328283
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:328283/raw/5d450ba693511a8d4f61c6c2ca9578e081357a21572f18d146535eca4eed3d2e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_328283`

##### `saos_pl:371082` — SENTENCE III K 303/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III K 303/16
- summary_1line: Caselaw corpus record: III K 303/16.
- external_id: saos:371082
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:371082/raw/e36261e357ff99f2f8bde0d70fe5d26a2c45444630d0a8876f68e905bb26d3a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_371082`

##### `saos_pl:341170` — SENTENCE III K 350/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III K 350/12
- summary_1line: Caselaw corpus record: III K 350/12.
- external_id: saos:341170
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:341170/raw/d922f834e0fde178e50ebac1ab99916c22c65158fc2d7915f17c18da904d0ba2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_341170`

##### `saos_pl:532595` — SENTENCE III K 78/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III K 78/15
- summary_1line: Caselaw corpus record: III K 78/15.
- external_id: saos:532595
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:532595/raw/b3a8920d4b77a811ee5827b45d1401787ce00568b5b9b25c19d8f4cab7687572/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_532595`

##### `saos_pl:375440` — SENTENCE III RC 1054/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 1054/17
- summary_1line: Caselaw corpus record: III RC 1054/17.
- external_id: saos:375440
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:375440/raw/4711f750b60742974a737adf8ec06c871d7f06ffd37a89390893eaebe38dad5b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_375440`

##### `saos_pl:44219` — SENTENCE III RC 107/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 107/14
- summary_1line: Caselaw corpus record: III RC 107/14.
- external_id: saos:44219
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:44219/raw/239feaf344817f8258a5ec02d9782a65451358b19e5292469326138a80b59395/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_44219`

##### `saos_pl:237247` — SENTENCE III RC 12/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 12/16
- summary_1line: Caselaw corpus record: III RC 12/16.
- external_id: saos:237247
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:237247/raw/f14637bcb0614be3ef910e3dcaf4cf690b4d133dff0619731ed84716e76f6479/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_237247`

##### `saos_pl:517749` — SENTENCE III RC 12/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 12/24
- summary_1line: Caselaw corpus record: III RC 12/24.
- external_id: saos:517749
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:517749/raw/40c1dd09b32593cd88dfb90f8b3a7ae27744eb02400657be55dec120cfcd77ae/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_517749`

##### `saos_pl:445589` — SENTENCE III RC 138/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 138/20
- summary_1line: Caselaw corpus record: III RC 138/20.
- external_id: saos:445589
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:445589/raw/0a1e9c44676f483920ba4c64a3f3d441a3b87ec225fe02f3c4c4a53e10fc704d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_445589`

##### `saos_pl:7825` — SENTENCE III RC 140/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 140/12
- summary_1line: Caselaw corpus record: III RC 140/12.
- external_id: saos:7825
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:7825/raw/af5724aed4cf199b63772df9120210eddbcacdd4dd29c75c6826df2a126346b4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_7825`

##### `saos_pl:57723` — SENTENCE III RC 161/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 161/14
- summary_1line: Caselaw corpus record: III RC 161/14.
- external_id: saos:57723
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:57723/raw/1b3dcd4b0f2e3fabdc8164aab6a5edd4a221baea544fc12be110f2b9a054b50d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_57723`

##### `saos_pl:468309` — SENTENCE III RC 163/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 163/21
- summary_1line: Caselaw corpus record: III RC 163/21.
- external_id: saos:468309
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:468309/raw/774bc7add0376b14023a04c1c233135446ce564bdc47b2e1ec3fa71fb2bd75d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_468309`

##### `saos_pl:153633` — SENTENCE III RC 179/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 179/14
- summary_1line: Caselaw corpus record: III RC 179/14.
- external_id: saos:153633
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153633/raw/835425a4221447520c74dd552e8caa45a99f279ea124827201ffaa01d1353358/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153633`

##### `saos_pl:197972` — SENTENCE III RC 229/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 229/15
- summary_1line: Caselaw corpus record: III RC 229/15.
- external_id: saos:197972
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:197972/raw/94c0349078f5f08eb455a778452c4f70097cc82852dbaced3e394f23bcc54b7d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_197972`

##### `saos_pl:58967` — SENTENCE III RC 231/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 231/13
- summary_1line: Caselaw corpus record: III RC 231/13.
- external_id: saos:58967
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:58967/raw/08e9fc4a78e6e5e0dc4917258bffad6348da835462dcb0d3e029174fdc37ee13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_58967`

##### `saos_pl:336764` — SENTENCE III RC 264/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 264/17
- summary_1line: Caselaw corpus record: III RC 264/17.
- external_id: saos:336764
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:336764/raw/418bf85dfa3e161c74d2f9fb40686d22a9d9c1c29ccdcaff1d915463c0018f2a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_336764`

##### `saos_pl:470793` — SENTENCE III RC 28/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 28/22
- summary_1line: Caselaw corpus record: III RC 28/22.
- external_id: saos:470793
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:470793/raw/16d24d5988aff4e2aa2498a0ca48a89e934dc42b33a7edb3298a2ed98693c40e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_470793`

##### `saos_pl:489829` — SENTENCE III RC 290/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 290/20
- summary_1line: Caselaw corpus record: III RC 290/20.
- external_id: saos:489829
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:489829/raw/f10096709e8ca1a47d656774a64e4b4afd7d6b0c73447ab4aec1f7d30c0ab427/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_489829`

##### `saos_pl:131660` — SENTENCE III RC 310/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 310/14
- summary_1line: Caselaw corpus record: III RC 310/14.
- external_id: saos:131660
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:131660/raw/b3e1cd3bff0a8d362d5f2e656656b680418b7fe9d5e4bb52caa00f8dccd5e551/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_131660`

##### `saos_pl:198685` — SENTENCE III RC 355/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 355/15
- summary_1line: Caselaw corpus record: III RC 355/15.
- external_id: saos:198685
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:198685/raw/a05b82fb6b4f18b79bdcfa2585ac9a0943ea5fcb8ae24e566c0fc66ff974fc75/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_198685`

##### `saos_pl:192204` — SENTENCE III RC 391/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 391/15
- summary_1line: Caselaw corpus record: III RC 391/15.
- external_id: saos:192204
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:192204/raw/48051e75ae454667cd2ec407a2c12272dad9dfa978208eacbd01b9acf358b8da/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_192204`

##### `saos_pl:33495` — SENTENCE III RC 392/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 392/13
- summary_1line: Caselaw corpus record: III RC 392/13.
- external_id: saos:33495
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:33495/raw/10c4ff04c5566da1241b6744d81bd6fdd0d7910f22a073d8eba13f702a250e7d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_33495`

##### `saos_pl:71800` — SENTENCE III RC 415/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 415/14
- summary_1line: Caselaw corpus record: III RC 415/14.
- external_id: saos:71800
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:71800/raw/5e74f373b0e27a7767ddc66dc702a36ee5c72ece7b8625bd6b69a116c7c908a2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_71800`

##### `saos_pl:127869` — SENTENCE III RC 425/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 425/14
- summary_1line: Caselaw corpus record: III RC 425/14.
- external_id: saos:127869
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:127869/raw/1122f85f0b612edacd613ddf6b4257b097bce163048f3dcecfabef674ad2e4a3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_127869`

##### `saos_pl:70359` — SENTENCE III RC 442/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 442/14
- summary_1line: Caselaw corpus record: III RC 442/14.
- external_id: saos:70359
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:70359/raw/a54b3b987e3ced11af9df368c689937d95955f151d48adda5a8a7a4c71ee5103/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_70359`

##### `saos_pl:450309` — SENTENCE III RC 45/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 45/21
- summary_1line: Caselaw corpus record: III RC 45/21.
- external_id: saos:450309
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:450309/raw/b0f47db459bc8b41c151d388d983d23a4f61f235b6ed2bf37408f24c213daa57/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_450309`

##### `saos_pl:372946` — SENTENCE III RC 454/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 454/18
- summary_1line: Caselaw corpus record: III RC 454/18.
- external_id: saos:372946
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:372946/raw/6393ccb3decae4adc28978d55e040fedf3f313eea96d1b93e77a9d3a6e1ad298/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_372946`

##### `saos_pl:339089` — SENTENCE III RC 479/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 479/17
- summary_1line: Caselaw corpus record: III RC 479/17.
- external_id: saos:339089
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:339089/raw/c4c1ce187f419173288196ed9213344dc9c01e5a60af64344fe0e7b757f2a5cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_339089`

##### `saos_pl:230945` — SENTENCE III RC 48/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 48/16
- summary_1line: Caselaw corpus record: III RC 48/16.
- external_id: saos:230945
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:230945/raw/5d817fd14f7660c119e0f354cf94ad068f33e94b6ec1559c82874cd62c78da4d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_230945`

##### `saos_pl:54695` — SENTENCE III RC 496/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 496/13
- summary_1line: Caselaw corpus record: III RC 496/13.
- external_id: saos:54695
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:54695/raw/663e92b7a40eaa21ea57524b3da6525660b34676220dd7805f0a855071f6c63c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_54695`

##### `saos_pl:291949` — SENTENCE III RC 52/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 52/16
- summary_1line: Caselaw corpus record: III RC 52/16.
- external_id: saos:291949
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:291949/raw/943b5e23606783992dfd4eddaeabcdd1e5b1ad7c431f3e8e0926ad72ef281884/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_291949`

##### `saos_pl:28093` — SENTENCE III RC 53/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 53/13
- summary_1line: Caselaw corpus record: III RC 53/13.
- external_id: saos:28093
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:28093/raw/447db08faa1b6f21141a52e717af04fa127af1a4630d037b2a8b02c12d0ed0cd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_28093`

##### `saos_pl:42289` — SENTENCE III RC 598/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 598/13
- summary_1line: Caselaw corpus record: III RC 598/13.
- external_id: saos:42289
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:42289/raw/a794bf984efeee3403ef99d2129f1099158e81087c1bb6fdfed35cbe8fc4df55/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_42289`

##### `saos_pl:361681` — SENTENCE III RC 606/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 606/17
- summary_1line: Caselaw corpus record: III RC 606/17.
- external_id: saos:361681
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:361681/raw/d0e50ce17fee61767e0de95fe980cd8d16625b5bc4c5607ba3ae4a7f3b314373/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_361681`

##### `saos_pl:28094` — SENTENCE III RC 65/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 65/13
- summary_1line: Caselaw corpus record: III RC 65/13.
- external_id: saos:28094
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:28094/raw/1a6de0413ab27472463f5ccde68997a238eae4851e58d5d63949053e8623c9d6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_28094`

##### `saos_pl:393299` — SENTENCE III RC 735/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 735/17
- summary_1line: Caselaw corpus record: III RC 735/17.
- external_id: saos:393299
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:393299/raw/035f8a2a5ebc43508fddea53aee20c80a6833fc00d7c5b6f8318673689827227/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_393299`

##### `saos_pl:368040` — SENTENCE III RC 79/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 79/16
- summary_1line: Caselaw corpus record: III RC 79/16.
- external_id: saos:368040
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:368040/raw/36416623118d6263a0add1a62fbeb3bbff047676a2a29142f2ee65058b1fa65d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_368040`

##### `saos_pl:275658` — SENTENCE III RC 99/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: III RC 99/16
- summary_1line: Caselaw corpus record: III RC 99/16.
- external_id: saos:275658
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:275658/raw/75309df6a480d754826e492beb2a7b485932723a936bdf8a4b333a137c4f3ec1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_275658`

##### `saos_pl:428048` — SENTENCE IV Ca 1009/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV CA 1009/19
- summary_1line: Caselaw corpus record: IV CA 1009/19.
- external_id: saos:428048
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:428048/raw/f1d480356351d62eae3db24050f19082b319f1782a69beb56fa2a713c01b0d29/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_428048`

##### `saos_pl:18764` — SENTENCE IV Ca 355/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV CA 355/13
- summary_1line: Caselaw corpus record: IV CA 355/13.
- external_id: saos:18764
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:18764/raw/d2dba7e2f3f6ec289533ca898b6a8e00e8ad6d4eb6114d6ee550f8f832e03257/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_18764`

##### `saos_pl:20732` — SENTENCE IV Ca 404/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV CA 404/13
- summary_1line: Caselaw corpus record: IV CA 404/13.
- external_id: saos:20732
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:20732/raw/b57bf1bd039b17c61ea6687bc99f795e79e28401606cbfaa917b7a1093ec6d88/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_20732`

##### `saos_pl:307475` — SENTENCE IV K 10/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV K 10/13
- summary_1line: Caselaw corpus record: IV K 10/13.
- external_id: saos:307475
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:307475/raw/78723a17e386f0cd0abea9e7abd55ed98772fd701dfc748fc30b7c232e490e0d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_307475`

##### `saos_pl:186277` — SENTENCE IV K 774/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV K 774/13
- summary_1line: Caselaw corpus record: IV K 774/13.
- external_id: saos:186277
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:186277/raw/23d5149f478d505cfc5431595a2efdc7136c877be46afe595500299055cb3d2d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_186277`

##### `saos_pl:334464` — SENTENCE IV K 972/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV K 972/13
- summary_1line: Caselaw corpus record: IV K 972/13.
- external_id: saos:334464
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:334464/raw/e703b11d5b9124535dc91b391d843e8eb72591e36c9d8f1130e148577015cd5a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_334464`

##### `saos_pl:171228` — SENTENCE IV Ka 391/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV KA 391/15
- summary_1line: Caselaw corpus record: IV KA 391/15.
- external_id: saos:171228
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171228/raw/6e807859e21d617d7fcba5e836e88655d0e5512543c719e9319c4fd7beb43c53/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171228`

##### `saos_pl:508936` — SENTENCE IV RC 272/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV RC 272/21
- summary_1line: Caselaw corpus record: IV RC 272/21.
- external_id: saos:508936
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:508936/raw/a084d7468ef95098465c11fe861ed75c951638dc38e21578804a44ad5e5ef7de/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_508936`

##### `saos_pl:472567` — SENTENCE IV RC 441/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV RC 441/20
- summary_1line: Caselaw corpus record: IV RC 441/20.
- external_id: saos:472567
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:472567/raw/83197001fb2eff95007db6da2d93813e66a1abac77a53bdf853f6b9509aa1d8c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_472567`

##### `saos_pl:423951` — SENTENCE IV RC 742/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV RC 742/18
- summary_1line: Caselaw corpus record: IV RC 742/18.
- external_id: saos:423951
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:423951/raw/1caeb95062c4dd77cf0d2fbcbb8a75a723eaa06689b8231b9f7a58aaf9acfe9b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_423951`

##### `saos_pl:391684` — SENTENCE IV RC 748/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IV RC 748/18
- summary_1line: Caselaw corpus record: IV RC 748/18.
- external_id: saos:391684
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:391684/raw/e8bbb1f4bfb74d624b6b763490e386d18777cd54c62c74f7c243da628cae8829/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_391684`

##### `saos_pl:266512` — SENTENCE IX C 630/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX C 630/14
- summary_1line: Caselaw corpus record: IX C 630/14.
- external_id: saos:266512
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:266512/raw/3f2248ca7099298b04caf98975a1ec91f326f2b1ddb54c1adbae646ff6f5f9d8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_266512`

##### `saos_pl:26484` — SENTENCE IX C 8/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX C 8/11
- summary_1line: Caselaw corpus record: IX C 8/11.
- external_id: saos:26484
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:26484/raw/abf969b002ed88b643e49af0fbfec56e4fddd2d72074c007e18014179f48dbdc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_26484`

##### `saos_pl:384745` — SENTENCE IX Ca 1460/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 1460/18
- summary_1line: Caselaw corpus record: IX CA 1460/18.
- external_id: saos:384745
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:384745/raw/aaa876c86ce636bf3a8526f2170d0c5e77ce3fef857f61373b010da163d7541a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_384745`

##### `saos_pl:154950` — SENTENCE IX Ca 159/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 159/15
- summary_1line: Caselaw corpus record: IX CA 159/15.
- external_id: saos:154950
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:154950/raw/c3aabe8265d6e6cb51bf331fe5df546b2f2370487f98d4e0a0a2daf3d1c56807/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_154950`

##### `saos_pl:360877` — SENTENCE IX Ca 490/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 490/18
- summary_1line: Caselaw corpus record: IX CA 490/18.
- external_id: saos:360877
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:360877/raw/2816cda55d3fc4abd7df9056b81f0bc5ef71710e20ad041b9c32ea3e95dc2930/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_360877`

##### `saos_pl:34501` — SENTENCE IX Ca 619/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 619/13
- summary_1line: Caselaw corpus record: IX CA 619/13.
- external_id: saos:34501
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:34501/raw/f5a9e60c6b792caa6a90d8e8415c17159b6e45ecafac97ef1dd7986b92784b18/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_34501`

##### `saos_pl:36564` — SENTENCE IX Ca 719/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 719/13
- summary_1line: Caselaw corpus record: IX CA 719/13.
- external_id: saos:36564
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:36564/raw/55f6222f11877763ebad740305f7d8c001eafe6cd183f115fc1729a7bbc650c6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_36564`

##### `saos_pl:203370` — SENTENCE IX Ca 805/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: IX CA 805/15
- summary_1line: Caselaw corpus record: IX CA 805/15.
- external_id: saos:203370
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:203370/raw/0de5f0a987b943037c9b318950a0677b31e20174ca11f58b7c9d7e4173768d4c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_203370`

##### `saos_pl:10097` — SENTENCE V ACa 141/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 141/12
- summary_1line: Caselaw corpus record: V ACA 141/12.
- external_id: saos:10097
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:10097/raw/70a968758255f494e0be1290e25a8fd6c5151b825ae4823f8e02072556761d50/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_10097`

##### `saos_pl:405058` — SENTENCE V ACa 149/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 149/19
- summary_1line: Caselaw corpus record: V ACA 149/19.
- external_id: saos:405058
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:405058/raw/606394e20b8399bfadd4699a33935d5d54f4243ac2015f0d6ce9cf199a63733c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_405058`

##### `saos_pl:20029` — SENTENCE V ACa 304/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 304/13
- summary_1line: Caselaw corpus record: V ACA 304/13.
- external_id: saos:20029
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:20029/raw/7ce65abbc820ca6397a5a302ffd3a4ef4bdb4fd7b3900dbe026d23e0afb01f4e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_20029`

##### `saos_pl:23940` — SENTENCE V ACa 347/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 347/13
- summary_1line: Caselaw corpus record: V ACA 347/13.
- external_id: saos:23940
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:23940/raw/a7376d7fb36a6b7f6586b668b748da723263bbbb47ad3b999a36e4d4b1f20071/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_23940`

##### `saos_pl:31293` — SENTENCE V ACa 567/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 567/13
- summary_1line: Caselaw corpus record: V ACA 567/13.
- external_id: saos:31293
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:31293/raw/27de27beeb36ed2265c629998cf1348a8fd92fa5191242daf75e157596365966/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_31293`

##### `saos_pl:35799` — SENTENCE V ACa 586/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 586/13
- summary_1line: Caselaw corpus record: V ACA 586/13.
- external_id: saos:35799
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:35799/raw/d748574fbcb3edfc8c837e632be7f43d3f9a25a7a9785b485e1516c33d88c5fd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_35799`

##### `saos_pl:132635` — SENTENCE V ACa 599/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 599/14
- summary_1line: Caselaw corpus record: V ACA 599/14.
- external_id: saos:132635
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:132635/raw/6f97e662b7a6c65932103570f4ae2079b3e572cfb79c3d0843aaddfa9b4c8bd5/original.bin
- same_case_group_id: `same_case:v_aca_599_14`

##### `saos_pl:150502` — SENTENCE V ACa 704/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 704/14
- summary_1line: Caselaw corpus record: V ACA 704/14.
- external_id: saos:150502
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:150502/raw/70d748bc077cfbc111948ad197b08a8e07d841c261542cdf1fbf9f3f87c2b7e7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_150502`

##### `saos_pl:417902` — SENTENCE V ACa 731/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V ACA 731/19
- summary_1line: Caselaw corpus record: V ACA 731/19.
- external_id: saos:417902
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:417902/raw/67390a3e397d6ed447b8ca0329274541a915ae71685d801cc6ecd4951bbc9f2a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_417902`

##### `saos_pl:521039` — SENTENCE V C 1212/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V C 1212/19
- summary_1line: Caselaw corpus record: V C 1212/19.
- external_id: saos:521039
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:521039/raw/fc59252e18d7ee4e2cb1704d4f1f282188b8cb0e0b6f9c2fda4c00ae16af595b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_521039`

##### `saos_pl:285767` — SENTENCE V Ca 1616/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V CA 1616/16
- summary_1line: Caselaw corpus record: V CA 1616/16.
- external_id: saos:285767
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:285767/raw/0c874f120ef888dc499f164095e4d5f46dcdc3d90d0736ff2c79f794b7439cac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_285767`

##### `saos_pl:226058` — SENTENCE V Ca 1770/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V CA 1770/13
- summary_1line: Caselaw corpus record: V CA 1770/13.
- external_id: saos:226058
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:226058/raw/b98f8da242d8e7975499ba76d67c4b351cb88e14e9f694ce7a8d815d2f37cba9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_226058`

##### `saos_pl:19765` — SENTENCE V Ca 2856/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V CA 2856/12
- summary_1line: Caselaw corpus record: V CA 2856/12.
- external_id: saos:19765
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:19765/raw/cdb1870c8560add48d80766dec260c81f60fd63586c61652ff3b164ceb114625/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_19765`

##### `saos_pl:275713` — SENTENCE V Ca 4343/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V CA 4343/15
- summary_1line: Caselaw corpus record: V CA 4343/15.
- external_id: saos:275713
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:275713/raw/5b18c5d0b10a103f7b72d474c2b84b284c7ead9d69159b2ee525fedcf65e68ff/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_275713`

##### `saos_pl:510116` — SENTENCE V GC 1333/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GC 1333/22
- summary_1line: Caselaw corpus record: V GC 1333/22.
- external_id: saos:510116
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:510116/raw/f77955fdcdde5768da8affb6336b95c0e5bec06de0d46431a44d35620a0b5045/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_510116`

##### `saos_pl:480777` — SENTENCE V GC 238/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GC 238/22
- summary_1line: Caselaw corpus record: V GC 238/22.
- external_id: saos:480777
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:480777/raw/4fdb11a561e1864917f82a1c599570e31ab7805553003a0502ba31fde758e91b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_480777`

##### `saos_pl:461034` — SENTENCE V GC 3004/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GC 3004/18
- summary_1line: Caselaw corpus record: V GC 3004/18.
- external_id: saos:461034
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:461034/raw/8375f75c25cf2f0f8cbc4081fc383c5e1e4f099e6f15ac06c7dcc33b71d2ff3c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_461034`

##### `saos_pl:334315` — SENTENCE V GC 449/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GC 449/17
- summary_1line: Caselaw corpus record: V GC 449/17.
- external_id: saos:334315
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:334315/raw/e389bb4847f3b6e4a0204334411c01da4699f5ca68f9a8837a24741651812bf9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_334315`

##### `saos_pl:481938` — SENTENCE V GC 531/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GC 531/19
- summary_1line: Caselaw corpus record: V GC 531/19.
- external_id: saos:481938
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:481938/raw/6fb648090cdc3d0d37d5beaae19bd4d3a0910b3eba2536db9bcae409632ac6d3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_481938`

##### `saos_pl:306258` — SENTENCE V Ga 94/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: V GA 94/17
- summary_1line: Caselaw corpus record: V GA 94/17.
- external_id: saos:306258
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:306258/raw/af4fa78ca13c9060acfa939eecdabe4a37e8a88f3beb28f6d6813c31d85ff6ba/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_306258`

##### `saos_pl:187465` — SENTENCE VI ACa 1006/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1006/14
- summary_1line: Caselaw corpus record: VI ACA 1006/14.
- external_id: saos:187465
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:187465/raw/e07b73515548c9825e00b00b14aaea046462a334a3e434931456c6e3f4f755f4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_187465`

##### `saos_pl:22869` — SENTENCE VI ACa 1078/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1078/12
- summary_1line: Caselaw corpus record: VI ACA 1078/12.
- external_id: saos:22869
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:22869/raw/09726696aa85aa03f12bbf5b3e277f82f6061de3e29e68178353c9c68ea32c6c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_22869`

##### `saos_pl:56425` — SENTENCE VI ACa 1117/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1117/13
- summary_1line: Caselaw corpus record: VI ACA 1117/13.
- external_id: saos:56425
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:56425/raw/b28890dbfe621dc9b6d7293a88f3fb6ae28be156a1f1f0a6369affdbf43029b8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_56425`

##### `saos_pl:200328` — SENTENCE VI ACa 1300/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1300/14
- summary_1line: Caselaw corpus record: VI ACA 1300/14.
- external_id: saos:200328
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:200328/raw/afa5a1b7de8a5d86c378f44062419dee5727b5006c9d9639619df0cb2b5fd1a5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_200328`

##### `saos_pl:187511` — SENTENCE VI ACa 1338/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1338/14
- summary_1line: Caselaw corpus record: VI ACA 1338/14.
- external_id: saos:187511
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:187511/raw/ec21298128af8eb6be822b4a5e63260995092b4eea2a5955717c2a408c32987b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_187511`

##### `saos_pl:251131` — SENTENCE VI ACa 1379/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1379/15
- summary_1line: Caselaw corpus record: VI ACA 1379/15.
- external_id: saos:251131
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:251131/raw/30d939952412696b721b227325bd86fad87b141ef2405a818288ac0bdf236d6e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_251131`

##### `saos_pl:56426` — SENTENCE VI ACa 1512/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1512/13
- summary_1line: Caselaw corpus record: VI ACA 1512/13.
- external_id: saos:56426
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:56426/raw/2fb5ae476904290f3c335584fdca16cdc7927ce48872ac57172d3e97b3b2871a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_56426`

##### `saos_pl:408131` — SENTENCE VI ACa 188/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 188/19
- summary_1line: Caselaw corpus record: VI ACA 188/19.
- external_id: saos:408131
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:408131/raw/a5366ac4d94d26762f433cde55d2017eec4a86a8bb4f41d428bfe79aa4602e13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_408131`

##### `saos_pl:222158` — SENTENCE VI ACa 1918/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 1918/14
- summary_1line: Caselaw corpus record: VI ACA 1918/14.
- external_id: saos:222158
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222158/raw/3419a858db8d2cbf580cde4088ddd9547ce5ed05ca2fcde5571e61d6a3d703ec/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222158`

##### `saos_pl:365132` — SENTENCE VI ACa 354/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 354/16
- summary_1line: Caselaw corpus record: VI ACA 354/16.
- external_id: saos:365132
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:365132/raw/3d85e8f199a6fa59ae4616df6263da3f5cdcc61696c2b4bceae0f89ca040e7bb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_365132`

##### `saos_pl:41340` — SENTENCE VI ACa 409/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 409/13
- summary_1line: Caselaw corpus record: VI ACA 409/13.
- external_id: saos:41340
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:41340/raw/96bd7bf39888585bb55af356ef58124b1fd25d9a0578ffc1cf56a36840527959/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_41340`

##### `saos_pl:254054` — SENTENCE VI ACa 503/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 503/14
- summary_1line: Caselaw corpus record: VI ACA 503/14.
- external_id: saos:254054
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:254054/raw/a26505a5b4ba89904455f7d587caa741a9a366cff91270ecd2f05cbc5c2217db/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_254054`

##### `saos_pl:265686` — SENTENCE VI ACa 563/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 563/15
- summary_1line: Caselaw corpus record: VI ACA 563/15.
- external_id: saos:265686
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:265686/raw/f8be42cf202483ff83cf58fe04ef233c78590866509773fc09fc0eef99affe66/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_265686`

##### `saos_pl:153327` — SENTENCE VI ACa 675/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 675/14
- summary_1line: Caselaw corpus record: VI ACA 675/14.
- external_id: saos:153327
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:153327/raw/ecb11a184da4500188e6fc5060bc124782b1b18ce61d6f04724ceeacdbdd7779/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_153327`

##### `saos_pl:321395` — SENTENCE VI ACa 771/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 771/16
- summary_1line: Caselaw corpus record: VI ACA 771/16.
- external_id: saos:321395
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:321395/raw/a3c999c632e430462a4861587a6d03e71a8dff8e8e761bca767c7e9f9873a5e2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_321395`

##### `saos_pl:431781` — SENTENCE VI ACa 884/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 884/19
- summary_1line: Caselaw corpus record: VI ACA 884/19.
- external_id: saos:431781
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:431781/raw/87a88ea6456659dc13bb7faee477e2e9ad4480dcca9e82d2a88055d9b86273d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_431781`

##### `saos_pl:169890` — SENTENCE VI ACa 904/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI ACA 904/14
- summary_1line: Caselaw corpus record: VI ACA 904/14.
- external_id: saos:169890
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:169890/raw/615a37d63f87e3f8d2a950cdecd5122c4f9fd58475549254fdb99ac46dd577c2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_169890`

##### `saos_pl:472811` — SENTENCE VI C 837/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI C 837/21
- summary_1line: Caselaw corpus record: VI C 837/21.
- external_id: saos:472811
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:472811/raw/2997527fc22d9a31da0961dfd13a69bf19e5af098fe804766025d3e644cb8c82/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_472811`

##### `saos_pl:254062` — SENTENCE VI Ca 528/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI CA 528/16
- summary_1line: Caselaw corpus record: VI CA 528/16.
- external_id: saos:254062
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:254062/raw/4b31bf0a5a2c2276dba663066ecccb04e2aaa33db309baf60e756c0237fbf30b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_254062`

##### `saos_pl:253359` — SENTENCE VI Ca 738/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI CA 738/16
- summary_1line: Caselaw corpus record: VI CA 738/16.
- external_id: saos:253359
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:253359/raw/e6c9c1bbd8b970a8cb8fe59a8f6056de0625f4140ebe521365223ffd86e2f807/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_253359`

##### `saos_pl:232962` — SENTENCE VI GC 137/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GC 137/14
- summary_1line: Caselaw corpus record: VI GC 137/14.
- external_id: saos:232962
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:232962/raw/7e53c3559ceca4ad51c8f018d9b2b3d50c5b4637fa4b2a84e96156d89814b295/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_232962`

##### `saos_pl:67881` — SENTENCE VI GC 165/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GC 165/14
- summary_1line: Caselaw corpus record: VI GC 165/14.
- external_id: saos:67881
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:67881/raw/0268ce6191912cc5caf12eefbebaeac4a817996a1a103dfc86eb17c27ac9f0b7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_67881`

##### `saos_pl:261557` — SENTENCE VI GC 218/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GC 218/13
- summary_1line: Caselaw corpus record: VI GC 218/13.
- external_id: saos:261557
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:261557/raw/80f8b66f5ed6c6a3629a47af7b712e478a0a5cb95865e2f557f88f42507aba2f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_261557`

##### `saos_pl:155192` — SENTENCE VI GC 66/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GC 66/14
- summary_1line: Caselaw corpus record: VI GC 66/14.
- external_id: saos:155192
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:155192/raw/a061e7717178a41bc1c9602531dd556ac649f9c59592cdc674f1ad1b82aa8a38/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_155192`

##### `saos_pl:299036` — SENTENCE VI Ga 413/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI GA 413/15
- summary_1line: Caselaw corpus record: VI GA 413/15.
- external_id: saos:299036
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:299036/raw/8ee42d784bd2934c9cefd49b065989163106354dbc8ce1cc6086db61317ed7da/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_299036`

##### `saos_pl:318738` — SENTENCE VI Ka 540/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI KA 540/17
- summary_1line: Caselaw corpus record: VI KA 540/17.
- external_id: saos:318738
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:318738/raw/4a08a2e3ebecf8a57ed4a3bf550d5a3277435ba4f62ed3f91782fdf24f5cc50c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_318738`

##### `saos_pl:180126` — SENTENCE VI P 24/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI P 24/15
- summary_1line: Caselaw corpus record: VI P 24/15.
- external_id: saos:180126
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:180126/raw/82684d1eaa2347f449c638554da990657752704ef44de7e3c61104aa385b0008/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_180126`

##### `saos_pl:336634` — SENTENCE VI RCa 57/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI RCA 57/18
- summary_1line: Caselaw corpus record: VI RCA 57/18.
- external_id: saos:336634
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:336634/raw/a723e04431216e8f7f9d144937f980c6c0211dc26e0c703d225bcff1ea2ec048/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_336634`

##### `saos_pl:187992` — SENTENCE VI U 607/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VI U 607/15
- summary_1line: Caselaw corpus record: VI U 607/15.
- external_id: saos:187992
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:187992/raw/06f60ffdcaba6e9d726a1d7c248e68f0d1018cc5baf364bbdf86443e687a9ec6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_187992`

##### `saos_pl:334669` — SENTENCE VII ACa 916/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII ACA 916/17
- summary_1line: Caselaw corpus record: VII ACA 916/17.
- external_id: saos:334669
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:334669/raw/0653582890e90baf2dbc933315146c3842d896c444cc8d8d60f8909fd431bf3e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_334669`

##### `saos_pl:446029` — SENTENCE VII AGa 26/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII AGA 26/19
- summary_1line: Caselaw corpus record: VII AGA 26/19.
- external_id: saos:446029
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:446029/raw/f54e8970d9464000d1a9c6273b7bc12994f40bb83f2458b2b78d74a18635a499/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_446029`

##### `saos_pl:445560` — SENTENCE VII AGa 452/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII AGA 452/20
- summary_1line: Caselaw corpus record: VII AGA 452/20.
- external_id: saos:445560
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:445560/raw/1ae258a15a61279c52f782c978c24e7f96027b26a7f89ac4244f0e58060674f7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_445560`

##### `saos_pl:461074` — SENTENCE VII AGa 527/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII AGA 527/21
- summary_1line: Caselaw corpus record: VII AGA 527/21.
- external_id: saos:461074
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:461074/raw/691071acd9310e5f3e90302c6cc7da36e22c31b8c4bb1afe516072d70c9c2943/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_461074`

##### `saos_pl:336643` — SENTENCE VII AGa 857/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII AGA 857/18
- summary_1line: Caselaw corpus record: VII AGA 857/18.
- external_id: saos:336643
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:336643/raw/03ad50bec4c32edeeef9951c7fa99ddbf49d1a2271e36de0c7657ac6b57abfee/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_336643`

##### `saos_pl:340108` — SENTENCE VII AGa 872/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VII AGA 872/18
- summary_1line: Caselaw corpus record: VII AGA 872/18.
- external_id: saos:340108
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:340108/raw/5eb5fe60e9f225d946d9db88a439d69c1b8b312a99aa3b1adb77fd98914ddf83/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_340108`

##### `saos_pl:276769` — SENTENCE VIII C 102/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 102/16
- summary_1line: Caselaw corpus record: VIII C 102/16.
- external_id: saos:276769
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:276769/raw/e1a0bae13a7d54532e8a5019f933be4b66f52b9f70454bc8b52f99355594bb81/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_276769`

##### `saos_pl:311508` — SENTENCE VIII C 1203/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1203/17
- summary_1line: Caselaw corpus record: VIII C 1203/17.
- external_id: saos:311508
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:311508/raw/0acd1839cc49f2317f3ae5ffbd1a4b1e67b137f770d778a28a18d0a49fede5a5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_311508`

##### `saos_pl:366533` — SENTENCE VIII C 1226/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1226/18
- summary_1line: Caselaw corpus record: VIII C 1226/18.
- external_id: saos:366533
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:366533/raw/b991cefa445f4fccf95c211473a339bfefdebb1efac3187275762fbacce082b4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_366533`

##### `saos_pl:450725` — SENTENCE VIII C 1250/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1250/20
- summary_1line: Caselaw corpus record: VIII C 1250/20.
- external_id: saos:450725
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:450725/raw/81a3e23a2b65487d03a168028cebfafdfefa3bade9c5ede85e69b17bbdd911f0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_450725`

##### `saos_pl:290764` — SENTENCE VIII C 1311/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1311/16
- summary_1line: Caselaw corpus record: VIII C 1311/16.
- external_id: saos:290764
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:290764/raw/1a2b9260d5acbe72cc8b85bf22dc870d35087db1066a6b5db35e6e04b22257cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_290764`

##### `saos_pl:354988` — SENTENCE VIII C 1335/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1335/16
- summary_1line: Caselaw corpus record: VIII C 1335/16.
- external_id: saos:354988
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:354988/raw/db1806d27b951bbf2860fc2571b5e00d074512dff3cef6cd73eca51800493f1d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_354988`

##### `saos_pl:222223` — SENTENCE VIII C 1378/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1378/15
- summary_1line: Caselaw corpus record: VIII C 1378/15.
- external_id: saos:222223
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222223/raw/4a30d69f03bcf429d1c5dbe4af935ec566f6b7037b5b7d6ba300d6e6bba073fc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222223`

##### `saos_pl:360729` — SENTENCE VIII C 1617/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1617/17
- summary_1line: Caselaw corpus record: VIII C 1617/17.
- external_id: saos:360729
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:360729/raw/9fe4dbdafbba49e204d146282c4a6b0a95ee6424a3fb88fd5343a94bcefe7391/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_360729`

##### `saos_pl:222224` — SENTENCE VIII C 1678/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1678/15
- summary_1line: Caselaw corpus record: VIII C 1678/15.
- external_id: saos:222224
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222224/raw/10ae3c63c4e5013864ae5759e61fef7471daa6981df7f7e6cae79144e3491947/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222224`

##### `saos_pl:512410` — SENTENCE VIII C 168/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 168/22
- summary_1line: Caselaw corpus record: VIII C 168/22.
- external_id: saos:512410
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:512410/raw/a2ff213a2705843c8fc95a77f60514b66773495ed5a73c3204889398f54ea21f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_512410`

##### `saos_pl:268189` — SENTENCE VIII C 1773/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1773/16
- summary_1line: Caselaw corpus record: VIII C 1773/16.
- external_id: saos:268189
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:268189/raw/6523727156114370d935f256610ff9adfa0d68d954884b586503559765ee857c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_268189`

##### `saos_pl:382831` — SENTENCE VIII C 1799/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1799/18
- summary_1line: Caselaw corpus record: VIII C 1799/18.
- external_id: saos:382831
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:382831/raw/dff44169ba2f8bf28d4a88ca13caf8a370000a37caa12e076711999092a22ba9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_382831`

##### `saos_pl:331918` — SENTENCE VIII C 1811/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1811/17
- summary_1line: Caselaw corpus record: VIII C 1811/17.
- external_id: saos:331918
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:331918/raw/df28e3022b798823f0c7b38d848709aa44039f7b8289482da6c9948943e44083/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_331918`

##### `saos_pl:217640` — SENTENCE VIII C 1837/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1837/15
- summary_1line: Caselaw corpus record: VIII C 1837/15.
- external_id: saos:217640
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:217640/raw/21b570fec1f8cd992fad50a83cb1ea3964070284ac33159d2591e6818fa5afd1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_217640`

##### `saos_pl:53197` — SENTENCE VIII C 1853/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1853/13
- summary_1line: Caselaw corpus record: VIII C 1853/13.
- external_id: saos:53197
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:53197/raw/66cf3f087e0af114465e4c57784d12264ec59fb4c240ba534348007338ea1003/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_53197`

##### `saos_pl:149463` — SENTENCE VIII C 1866/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1866/13
- summary_1line: Caselaw corpus record: VIII C 1866/13.
- external_id: saos:149463
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:149463/raw/dba415d6395eedc3249b6271ef7fdfa8b10fdf024bca971904dc84c6da070004/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_149463`

##### `saos_pl:360946` — SENTENCE VIII C 1926/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1926/17
- summary_1line: Caselaw corpus record: VIII C 1926/17.
- external_id: saos:360946
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:360946/raw/7c4f14169504eac937fe9324cad57d31df760269ed6623de7d3160fd17e06629/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_360946`

##### `saos_pl:22260` — SENTENCE VIII C 194/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 194/11
- summary_1line: Caselaw corpus record: VIII C 194/11.
- external_id: saos:22260
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:22260/raw/f387d612ac80937a30fea6eca009b115e1bd7b18e137822680e6857531002cfa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_22260`

##### `saos_pl:224695` — SENTENCE VIII C 1960/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 1960/14
- summary_1line: Caselaw corpus record: VIII C 1960/14.
- external_id: saos:224695
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:224695/raw/acb4e002d691f5807f5560be357ef147ec5e05cf622e9b0386b6af9ab77eee82/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_224695`

##### `saos_pl:299700` — SENTENCE VIII C 2343/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2343/16
- summary_1line: Caselaw corpus record: VIII C 2343/16.
- external_id: saos:299700
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:299700/raw/42eaa543f777098952d7cf2ef9a222df80a08c1ef19e8cad4c7234c8e62276a3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_299700`

##### `saos_pl:346664` — SENTENCE VIII C 2402/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2402/17
- summary_1line: Caselaw corpus record: VIII C 2402/17.
- external_id: saos:346664
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:346664/raw/a7ea3e244dfa70c59abfb765a35c25a3a10a89753f08fcd4fe6c183c952f2984/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_346664`

##### `saos_pl:342037` — SENTENCE VIII C 2411/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2411/17
- summary_1line: Caselaw corpus record: VIII C 2411/17.
- external_id: saos:342037
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:342037/raw/d9606525be52221a434275965187bd2533f45dc93d44077b9a2181d5f89dca8b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_342037`

##### `saos_pl:354999` — SENTENCE VIII C 2419/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2419/17
- summary_1line: Caselaw corpus record: VIII C 2419/17.
- external_id: saos:354999
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:354999/raw/befc46e3153b0d7fce0fc379b813115c0d27a92209da4c4c237c147c16162e2b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_354999`

##### `saos_pl:193556` — SENTENCE VIII C 2475/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2475/15
- summary_1line: Caselaw corpus record: VIII C 2475/15.
- external_id: saos:193556
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:193556/raw/5e4a6db9bc45a7670e4e4d8e4fa1360c9dd330a354b7abe5966b144e6b13f937/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_193556`

##### `saos_pl:222225` — SENTENCE VIII C 2529/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2529/15
- summary_1line: Caselaw corpus record: VIII C 2529/15.
- external_id: saos:222225
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222225/raw/eff599a0100c3106ff07e5e0fdc54d7ee8292d66e214fd0f7df21e0e24bfef09/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222225`

##### `saos_pl:287308` — SENTENCE VIII C 2637/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2637/16
- summary_1line: Caselaw corpus record: VIII C 2637/16.
- external_id: saos:287308
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:287308/raw/a837e2b21def72d765f3a1c660e092bd3e8f0423c9b875b567f3cf796fa2a435/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_287308`

##### `saos_pl:462615` — SENTENCE VIII C 265/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 265/21
- summary_1line: Caselaw corpus record: VIII C 265/21.
- external_id: saos:462615
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:462615/raw/3afd371560bbf9dbbad10210dace58a5c8ef13a9f852d0d4f705e8bc072f96d5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_462615`

##### `saos_pl:306737` — SENTENCE VIII C 2739/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2739/16
- summary_1line: Caselaw corpus record: VIII C 2739/16.
- external_id: saos:306737
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:306737/raw/215296f470a1fab9d6e59831bb074b676f788012c7623187731590a498add6e3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_306737`

##### `saos_pl:226902` — SENTENCE VIII C 2789/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2789/15
- summary_1line: Caselaw corpus record: VIII C 2789/15.
- external_id: saos:226902
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:226902/raw/f7c65fd3b8a19af8a7304df6f8523ba55c1efbba2b05fc5d422430854e153ff5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_226902`

##### `saos_pl:400101` — SENTENCE VIII C 2869/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 2869/18
- summary_1line: Caselaw corpus record: VIII C 2869/18.
- external_id: saos:400101
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:400101/raw/62049bc270cc8bfed2de506fe7edf65f9212bfb23d21cf88d4d9d855ac4e5829/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_400101`

##### `saos_pl:188484` — SENTENCE VIII C 3569/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 3569/14
- summary_1line: Caselaw corpus record: VIII C 3569/14.
- external_id: saos:188484
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:188484/raw/72d6b0d65d967f936fab70383f2b561800adf05746e6ca41ac73f12426f9eb6b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_188484`

##### `saos_pl:299703` — SENTENCE VIII C 37/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 37/17
- summary_1line: Caselaw corpus record: VIII C 37/17.
- external_id: saos:299703
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:299703/raw/2596e6459f3e638a0cd35b5f2ddd02d9c83471e12df609d4f36bd7c24c76ab9d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_299703`

##### `saos_pl:237883` — SENTENCE VIII C 375/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 375/16
- summary_1line: Caselaw corpus record: VIII C 375/16.
- external_id: saos:237883
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:237883/raw/13c5ea3059621b33d8f85313e6be886d95b38d39da0b9540d56b20e848d42581/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_237883`

##### `saos_pl:518510` — SENTENCE VIII C 445/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 445/23
- summary_1line: Caselaw corpus record: VIII C 445/23.
- external_id: saos:518510
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:518510/raw/61a73ef4ec27bbab6d23ba1baff33617c1c49562353cac9cead6c780037fb3ce/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_518510`

##### `saos_pl:450531` — SENTENCE VIII C 46/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 46/21
- summary_1line: Caselaw corpus record: VIII C 46/21.
- external_id: saos:450531
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:450531/raw/ffbbf7ab76a2c26f4d54b4cde860999dd36a7149bd299ac5a182513070cf6e6c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_450531`

##### `saos_pl:382884` — SENTENCE VIII C 579/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 579/18
- summary_1line: Caselaw corpus record: VIII C 579/18.
- external_id: saos:382884
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:382884/raw/305de92e15a067b9f301679050a1b2c4bab3ad530287ae2d47fe3bbbeb868b54/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_382884`

##### `saos_pl:317765` — SENTENCE VIII C 682/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 682/17
- summary_1line: Caselaw corpus record: VIII C 682/17.
- external_id: saos:317765
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:317765/raw/b2179b58d1c3ad0b6ef740f44e0740eb37219082dd4a416e18d47bd72f8c8b0a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_317765`

##### `saos_pl:392216` — SENTENCE VIII C 760/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 760/19
- summary_1line: Caselaw corpus record: VIII C 760/19.
- external_id: saos:392216
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:392216/raw/f1f28f25a5be71486c09f86a9548da751f776de996ba4b489dbd976680d48032/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_392216`

##### `saos_pl:237884` — SENTENCE VIII C 776/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 776/15
- summary_1line: Caselaw corpus record: VIII C 776/15.
- external_id: saos:237884
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:237884/raw/7ef6c4d2c2bcf21a2a2b110404f6218ccc710853f8b02c10d0059fd8817d9ede/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_237884`

##### `saos_pl:334523` — SENTENCE VIII C 911/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 911/17
- summary_1line: Caselaw corpus record: VIII C 911/17.
- external_id: saos:334523
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:334523/raw/e13ce60ac7c812e86e6553e05c610f70f540989c72dd421407f38e68ac9c6654/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_334523`

##### `saos_pl:393782` — SENTENCE VIII C 912/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII C 912/19
- summary_1line: Caselaw corpus record: VIII C 912/19.
- external_id: saos:393782
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:393782/raw/8805d179c4f10a1f61fd07ff337a0a13dde399991e66e918e27d8213f46daed8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_393782`

##### `saos_pl:18995` — SENTENCE VIII Ca 323/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII CA 323/13
- summary_1line: Caselaw corpus record: VIII CA 323/13.
- external_id: saos:18995
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:18995/raw/5b78cb656ad02d31447d79096eec57d6e4909eec3186cd55957671b91a088dd2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_18995`

##### `saos_pl:43023` — SENTENCE VIII Ca 45/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII CA 45/14
- summary_1line: Caselaw corpus record: VIII CA 45/14.
- external_id: saos:43023
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:43023/raw/ae2528c1ae3e73d0961ba7dd1849ae76dacebaeee3164952790068831f251595/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_43023`

##### `saos_pl:27591` — SENTENCE VIII Ca 453/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII CA 453/13
- summary_1line: Caselaw corpus record: VIII CA 453/13.
- external_id: saos:27591
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:27591/raw/7a04a4b4ba874bc189e51afe6447c2d523cfa25e1b1057deeddef887d3db6be1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_27591`

##### `saos_pl:312719` — SENTENCE VIII GC 163/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 163/16
- summary_1line: Caselaw corpus record: VIII GC 163/16.
- external_id: saos:312719
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:312719/raw/ce1dfcd7f6c263271ebceaf027e43d2a7cc5b7f5650a959c5165060d082e1df9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_312719`

##### `saos_pl:69062` — SENTENCE VIII GC 208/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 208/14
- summary_1line: Caselaw corpus record: VIII GC 208/14.
- external_id: saos:69062
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:69062/raw/d477c89fe5faee9b532fa4035065d2eee417e48b95e5c9581eab2816e750b621/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_69062`

##### `saos_pl:334698` — SENTENCE VIII GC 249/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GC 249/17
- summary_1line: Caselaw corpus record: VIII GC 249/17.
- external_id: saos:334698
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:334698/raw/f72ae3d9756f1d32ff5cd2bb1da5e83bcbeac5d61bc7493d8a417a426926c5e8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_334698`

##### `saos_pl:51327` — SENTENCE VIII Ga 132/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 132/14
- summary_1line: Caselaw corpus record: VIII GA 132/14.
- external_id: saos:51327
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:51327/raw/141b0cc591ca41c73df304cc7b0adc26b290451be3377e3c35af3edc9578656e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_51327`

##### `saos_pl:291855` — SENTENCE VIII Ga 173/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 173/17
- summary_1line: Caselaw corpus record: VIII GA 173/17.
- external_id: saos:291855
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:291855/raw/3307c9055054bf2f183b6952ee607c08c1dbc37f5d7531577dc8252274be41ba/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_291855`

##### `saos_pl:171780` — SENTENCE VIII Ga 177/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 177/15
- summary_1line: Caselaw corpus record: VIII GA 177/15.
- external_id: saos:171780
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171780/raw/595f8c0098ff006d2f101067703d81e58c3ca38e627971083c01ab5a64084ed7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171780`

##### `saos_pl:178408` — SENTENCE VIII Ga 198/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 198/15
- summary_1line: Caselaw corpus record: VIII GA 198/15.
- external_id: saos:178408
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:178408/raw/6a86b9a18a8f6490c25111d6060e1fb11148d2c95171cc721f14380cb169c027/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_178408`

##### `saos_pl:247549` — SENTENCE VIII Ga 212/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 212/16
- summary_1line: Caselaw corpus record: VIII GA 212/16.
- external_id: saos:247549
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:247549/raw/6ac53c9fa12a3c8e7080dd47bc44c98c0ccd8bab618ac70a56197f305cf54c00/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_247549`

##### `saos_pl:24412` — SENTENCE VIII Ga 213/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 213/13
- summary_1line: Caselaw corpus record: VIII GA 213/13.
- external_id: saos:24412
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:24412/raw/6d6c14cd119df241aeb07f2fe20d05eacf9a5f62cd45df0965d265a90ebe5144/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_24412`

##### `saos_pl:178412` — SENTENCE VIII Ga 23/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 23/15
- summary_1line: Caselaw corpus record: VIII GA 23/15.
- external_id: saos:178412
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:178412/raw/4580f3f78765bc521f5ad2030d0583bb363080b689935094e46f274e15732851/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_178412`

##### `saos_pl:127922` — SENTENCE VIII Ga 249/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII GA 249/14
- summary_1line: Caselaw corpus record: VIII GA 249/14.
- external_id: saos:127922
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:127922/raw/c64e2382e59e8ae45caf82d943a36f8dfcdf73fafff5ae6b42da230f0d4f44e4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_127922`

##### `saos_pl:246801` — SENTENCE VIII RC 173/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII RC 173/15
- summary_1line: Caselaw corpus record: VIII RC 173/15.
- external_id: saos:246801
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:246801/raw/846d4f506308fc7a0df00916b4c4dcb8cf172f12cbed07eb9b577092b27c6cd2/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_246801`

##### `saos_pl:393497` — SENTENCE VIII RC 674/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: VIII RC 674/17
- summary_1line: Caselaw corpus record: VIII RC 674/17.
- external_id: saos:393497
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:393497/raw/1fb6eeaa30332a212cd4e8d2c51397bfa66fd9c20a6389e0a8fe4b629e3c20b0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_393497`

##### `saos_pl:308595` — SENTENCE X C 1/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1/17
- summary_1line: Caselaw corpus record: X C 1/17.
- external_id: saos:308595
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:308595/raw/25d11d53d8390d6d7c8b2098af7d9e1b89f01a7004d840b1ebee279bc5bc9e12/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_308595`

##### `saos_pl:514367` — SENTENCE X C 1038/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1038/23
- summary_1line: Caselaw corpus record: X C 1038/23.
- external_id: saos:514367
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:514367/raw/c27ecf1b0f5f6297f0ab904675a00fd66cbeeb878be46ea28a4395d404d1f1cf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_514367`

##### `saos_pl:340301` — SENTENCE X C 1128/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1128/17
- summary_1line: Caselaw corpus record: X C 1128/17.
- external_id: saos:340301
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:340301/raw/3eb81a93a7bde66ad362bf04273bbd6c4bb9e52b0addc571135f0159a7cca1e1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_340301`

##### `saos_pl:534996` — SENTENCE X C 1911/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1911/22
- summary_1line: Caselaw corpus record: X C 1911/22.
- external_id: saos:534996
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:534996/raw/6a7802af8c445bdb8c0686f81eab19324b65e1237407be097a92fb24dc9d01fa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_534996`

##### `saos_pl:228440` — SENTENCE X C 1943/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 1943/15
- summary_1line: Caselaw corpus record: X C 1943/15.
- external_id: saos:228440
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:228440/raw/2ecba59d7e1f821d53432b87c3db5dcb81345dd981a013d27070d6645b8693fc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_228440`

##### `saos_pl:278169` — SENTENCE X C 2066/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 2066/16
- summary_1line: Caselaw corpus record: X C 2066/16.
- external_id: saos:278169
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:278169/raw/809df7150b1a645a0780642dac0a286b5d227d1ea5ea9430802d2c443eacabe3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_278169`

##### `saos_pl:283100` — SENTENCE X C 2068/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 2068/16
- summary_1line: Caselaw corpus record: X C 2068/16.
- external_id: saos:283100
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:283100/raw/2e047961d1c7183173fd9f2e87196fa7d254b068c84277e9f9871f0b8a2fe4ac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_283100`

##### `saos_pl:340794` — SENTENCE X C 209/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 209/17
- summary_1line: Caselaw corpus record: X C 209/17.
- external_id: saos:340794
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:340794/raw/283514f07bbe1e95a4bfae30e70e5a266af5f5b026abf57aa0c38566ce6c7910/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_340794`

##### `saos_pl:278634` — SENTENCE X C 2745/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 2745/16
- summary_1line: Caselaw corpus record: X C 2745/16.
- external_id: saos:278634
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:278634/raw/dd4173153bab4358f92aa670880354e164fde876928f2b0b25235a8f85f5931a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_278634`

##### `saos_pl:342647` — SENTENCE X C 4550/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X C 4550/17
- summary_1line: Caselaw corpus record: X C 4550/17.
- external_id: saos:342647
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:342647/raw/ca74f5c98a5a3a7aaa940830a3978e58168223e775f6224751382ff316c9ef67/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_342647`

##### `saos_pl:27726` — SENTENCE X Ca 80/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X CA 80/13
- summary_1line: Caselaw corpus record: X CA 80/13.
- external_id: saos:27726
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:27726/raw/1074bcfc59ad7e6997b52cb52c6f4259fa37e95b99ca04140de677e1083fe13b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_27726`

##### `saos_pl:65630` — SENTENCE X Ga 476/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: X GA 476/14
- summary_1line: Caselaw corpus record: X GA 476/14.
- external_id: saos:65630
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:65630/raw/af81884e1931ef7603fc0bef3c3fb4918b3e2b018e92dc7f2ef1a0e086a71aa8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_65630`

##### `saos_pl:223190` — SENTENCE XI C 120/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI C 120/14
- summary_1line: Caselaw corpus record: XI C 120/14.
- external_id: saos:223190
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:223190/raw/c3cda24c4f24b9bd8003a9e48e78c44cc53a95defdecbbf6dd0003226bda423a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_223190`

##### `saos_pl:280352` — SENTENCE XI GC 1065/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 1065/16
- summary_1line: Caselaw corpus record: XI GC 1065/16.
- external_id: saos:280352
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:280352/raw/1500104ac1d31bfead2c79f052f95a1ba5b36d73bb5c8b20f8200c62b96a4993/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_280352`

##### `saos_pl:190705` — SENTENCE XI GC 1082/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 1082/15
- summary_1line: Caselaw corpus record: XI GC 1082/15.
- external_id: saos:190705
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:190705/raw/dfeb75aa0ad4f89906d1ee9eb0ed7424e9da04c145fa962cd599f830bbcff7c5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_190705`

##### `saos_pl:208097` — SENTENCE XI GC 1098/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 1098/15
- summary_1line: Caselaw corpus record: XI GC 1098/15.
- external_id: saos:208097
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:208097/raw/39a2bcec5181bf702f77873a6e2eb9b2f336d68583750361f4b381bc342c758d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_208097`

##### `saos_pl:222310` — SENTENCE XI GC 225/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 225/16
- summary_1line: Caselaw corpus record: XI GC 225/16.
- external_id: saos:222310
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:222310/raw/2cb6f33f0b5a9ec183657de6157b8c7eb95899f0110ad6c83b95e5d8cfcb215a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_222310`

##### `saos_pl:205133` — SENTENCE XI GC 953/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XI GC 953/15
- summary_1line: Caselaw corpus record: XI GC 953/15.
- external_id: saos:205133
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:205133/raw/6b31af4139f744917deabeafbde5d9aa82e2f89a38d5ff10562966099cd84a58/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_205133`

##### `saos_pl:194087` — SENTENCE XII C 309/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII C 309/13
- summary_1line: Caselaw corpus record: XII C 309/13.
- external_id: saos:194087
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:194087/raw/80890241aeb9f8df019ad1fb3e8889e08dfc395b39a34e24d5aa2c3b92d6dfe3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_194087`

##### `saos_pl:250127` — SENTENCE XII C 327/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII C 327/11
- summary_1line: Caselaw corpus record: XII C 327/11.
- external_id: saos:250127
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:250127/raw/20f857afb8c458fe559cdc65ca2c71f7a11f67edeade3940ee509f8d4d3c56dc/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_250127`

##### `saos_pl:171522` — SENTENCE XII C 882/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII C 882/14
- summary_1line: Caselaw corpus record: XII C 882/14.
- external_id: saos:171522
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171522/raw/079ea5c5762e104942b7792a359643348e29ce76b462e29af6c5f552b39dea9a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171522`

##### `saos_pl:247840` — SENTENCE XII C 916/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII C 916/15
- summary_1line: Caselaw corpus record: XII C 916/15.
- external_id: saos:247840
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:247840/raw/c0f3cd4c2cabf5af8a9f0908127e09b3b245a8ff49f36d1c8241c316d9d8ab8a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_247840`

##### `saos_pl:514594` — SENTENCE XII K 168/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII K 168/22
- summary_1line: Caselaw corpus record: XII K 168/22.
- external_id: saos:514594
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:514594/raw/574a096f5193296bdb9dbce3220d6785e60537a0a4cd7092884a3e42b587fa88/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_514594`

##### `saos_pl:514620` — SENTENCE XII K 273/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII K 273/12
- summary_1line: Caselaw corpus record: XII K 273/12.
- external_id: saos:514620
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:514620/raw/d2017db97220842289d87e1a119d137f8da03a7a9d74cea8fd18c84d2ecdd5b4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_514620`

##### `saos_pl:491239` — SENTENCE XII K 36/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XII K 36/14
- summary_1line: Caselaw corpus record: XII K 36/14.
- external_id: saos:491239
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:491239/raw/897e7fcef46ff53b28451713da00ee309f9f108271a2e0ac8b63f79de97140be/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_491239`

##### `saos_pl:241837` — SENTENCE XIII Ca 218/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XIII CA 218/16
- summary_1line: Caselaw corpus record: XIII CA 218/16.
- external_id: saos:241837
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:241837/raw/9934d8e6ad73b924314a3a0ecab469c2eeb4fb387c04b3f0913ef4b5c6088367/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_241837`

##### `saos_pl:252037` — SENTENCE XIII Ca 519/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XIII CA 519/15
- summary_1line: Caselaw corpus record: XIII CA 519/15.
- external_id: saos:252037
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:252037/raw/c12f9919eb624d92f00a923c9228be24657bb8b3cf7d1f710bdf3ce4a11f903c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_252037`

##### `saos_pl:227995` — SENTENCE XV C 14/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV C 14/15
- summary_1line: Caselaw corpus record: XV C 14/15.
- external_id: saos:227995
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:227995/raw/e074634395b191faa3c5e867588caef770a39d770ff012fbad592948c4c22fac/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_227995`

##### `saos_pl:332915` — SENTENCE XV C 413/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV C 413/12
- summary_1line: Caselaw corpus record: XV C 413/12.
- external_id: saos:332915
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:332915/raw/dfbbe5bdd30c69d642f15453753d31ea06e6c74cea4e759b52c04ee0ea93dbe4/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_332915`

##### `saos_pl:283315` — SENTENCE XV Ca 1038/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 1038/16
- summary_1line: Caselaw corpus record: XV CA 1038/16.
- external_id: saos:283315
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:283315/raw/eefdaa066ebef668b77e0e1350fae1f1d166a1e608aaefa209afd245b07526d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_283315`

##### `saos_pl:200280` — SENTENCE XV Ca 1366/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 1366/15
- summary_1line: Caselaw corpus record: XV CA 1366/15.
- external_id: saos:200280
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:200280/raw/c66a187c230f05f588eac5cb9f9a020d77c1cd534fd23fe78a50ab5e3ec34c50/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_200280`

##### `saos_pl:171523` — SENTENCE XV Ca 1501/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 1501/13
- summary_1line: Caselaw corpus record: XV CA 1501/13.
- external_id: saos:171523
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171523/raw/c655b3e7505450512baf055d12699e14b2a2b907bb123fe69c83285858a27a0b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171523`

##### `saos_pl:171524` — SENTENCE XV Ca 172/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 172/14
- summary_1line: Caselaw corpus record: XV CA 172/14.
- external_id: saos:171524
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:171524/raw/edde7f88267fcdcf23432a8ba2c1571db2ad32d19042816c8edac34f8dd4fc13/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_171524`

##### `saos_pl:53191` — SENTENCE XV Ca 1805/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 1805/13
- summary_1line: Caselaw corpus record: XV CA 1805/13.
- external_id: saos:53191
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:53191/raw/a0c779d125c78bf256ab9d1c6a1283463ebdb76f6461e029e9f4b09be0d67307/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_53191`

##### `saos_pl:125336` — SENTENCE XV Ca 217/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 217/14
- summary_1line: Caselaw corpus record: XV CA 217/14.
- external_id: saos:125336
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:125336/raw/c552bcec6b08632eedfd8d8c337c0680cd4b777d85dd0a0a6765d0a732be8b78/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_125336`

##### `saos_pl:308477` — SENTENCE XV Ca 337/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 337/17
- summary_1line: Caselaw corpus record: XV CA 337/17.
- external_id: saos:308477
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:308477/raw/d299b0e9c3c79d7e490ad568babb640e94b0c9ca2b2d1c302a40b3cdcd37a655/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_308477`

##### `saos_pl:213675` — SENTENCE XV Ca 494/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 494/15
- summary_1line: Caselaw corpus record: XV CA 494/15.
- external_id: saos:213675
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:213675/raw/d26cfc53eeda9b5217c384557887fae6aa7a12718e742ed0d6deadb9ab415f26/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_213675`

##### `saos_pl:53249` — SENTENCE XV Ca 95/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV CA 95/14
- summary_1line: Caselaw corpus record: XV CA 95/14.
- external_id: saos:53249
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:53249/raw/85cdaa06f000dd116af22a8f6eb1bbb28eef0ab9df1ec162ccb716dfc00df530/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_53249`

##### `saos_pl:152348` — SENTENCE XV GC 745/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XV GC 745/13
- summary_1line: Caselaw corpus record: XV GC 745/13.
- external_id: saos:152348
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:152348/raw/d2d6870dce78aeeb0127bba56a60b7d1ad3b66d137b626e920da0f9bca2547d1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_152348`

##### `saos_pl:252039` — SENTENCE XVI Ca 399/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI CA 399/16
- summary_1line: Caselaw corpus record: XVI CA 399/16.
- external_id: saos:252039
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:252039/raw/194cb3e9d59c24298a8e51ff9d97b31ac57d94ee6434aeae68611044486279f9/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_252039`

##### `saos_pl:269089` — SENTENCE XVI GC 553/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI GC 553/12
- summary_1line: Caselaw corpus record: XVI GC 553/12.
- external_id: saos:269089
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:269089/raw/9c0b74cc9e0ba761b38a0a5570fefb85de7db535fb248a5829eb6e26289ac2cb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_269089`

##### `saos_pl:260338` — SENTENCE XVI K 99/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVI K 99/15
- summary_1line: Caselaw corpus record: XVI K 99/15.
- external_id: saos:260338
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:260338/raw/c32b4712899c6d2783248f94f1cb7468c03f8bb0b6a2c55ac5b12e8feba75f28/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_260338`

##### `saos_pl:253184` — SENTENCE XVII AmA 61/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMA 61/14
- summary_1line: Caselaw corpus record: XVII AMA 61/14.
- external_id: saos:253184
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:253184/raw/c3c2f912a8c2baa00bda387529c24ee235c5fbe2c4db5e572fa4c65272560eee/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_253184`

##### `saos_pl:253185` — SENTENCE XVII AmA 63/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMA 63/15
- summary_1line: Caselaw corpus record: XVII AMA 63/15.
- external_id: saos:253185
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:253185/raw/2fd44d7eaf24b69c472728eb8096c88cec5cbc06fb56823e5e13c7c15e03fa6c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_253185`

##### `saos_pl:437963` — SENTENCE XVII AmA 9/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMA 9/19
- summary_1line: Caselaw corpus record: XVII AMA 9/19.
- external_id: saos:437963
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:437963/raw/8a36e54601ac48f73c90d52f52f5de4fc1df6047b98c0a73dbf67d765ee8694a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_437963`

##### `saos_pl:471297` — SENTENCE XVII AmT 1/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 1/18
- summary_1line: Caselaw corpus record: XVII AMT 1/18.
- external_id: saos:471297
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:471297/raw/11f22b557c6619e6a171f31a8e996ddcd240116cda824bb6f73c9f358bc979dd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_471297`

##### `saos_pl:460009` — SENTENCE XVII AmT 106/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 106/19
- summary_1line: Caselaw corpus record: XVII AMT 106/19.
- external_id: saos:460009
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:460009/raw/c686e67c381b83279f03d5a12ebc3d935b83994265c9ba5de5558638cfdae2be/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_460009`

##### `saos_pl:467156` — SENTENCE XVII AmT 108/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 108/18
- summary_1line: Caselaw corpus record: XVII AMT 108/18.
- external_id: saos:467156
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:467156/raw/22e1390fc315e82062a312c54f25282f98552398e1bc010b9abc9269c54b63a5/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_467156`

##### `saos_pl:515211` — SENTENCE XVII AmT 112/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 112/19
- summary_1line: Caselaw corpus record: XVII AMT 112/19.
- external_id: saos:515211
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:515211/raw/356e7d70b5fc686ce94d819947f907b8342a8f6e9235f896374cd80cc031ed01/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_515211`

##### `saos_pl:478029` — SENTENCE XVII AmT 119/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 119/20
- summary_1line: Caselaw corpus record: XVII AMT 119/20.
- external_id: saos:478029
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:478029/raw/843a4af226cf417c9461fd93121675c1015fd1c3d2f5cbcbede310cde69bec8f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_478029`

##### `saos_pl:473202` — SENTENCE XVII AmT 13/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 13/21
- summary_1line: Caselaw corpus record: XVII AMT 13/21.
- external_id: saos:473202
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:473202/raw/cc5e37a4c6d2f4fdf416729f3721628548b057a81ad57e2f22ff831b80d109f1/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_473202`

##### `saos_pl:446141` — SENTENCE XVII AmT 135/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 135/18
- summary_1line: Caselaw corpus record: XVII AMT 135/18.
- external_id: saos:446141
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:446141/raw/431db20014c9b3406b31ccbe5fc9af6e28c650998a71b81f05270c1ee19cdae6/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_446141`

##### `saos_pl:535631` — SENTENCE XVII AmT 15/24 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 15/24
- summary_1line: Caselaw corpus record: XVII AMT 15/24.
- external_id: saos:535631
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:535631/raw/86246e8216122fabbf77128294b443a0d8263ae2f2ae48062af0884cf1a14269/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_535631`

##### `saos_pl:432265` — SENTENCE XVII AmT 150/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 150/18
- summary_1line: Caselaw corpus record: XVII AMT 150/18.
- external_id: saos:432265
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:432265/raw/f8a42550a29db84b1c4c9bd39d72d161edaefbaf027687806d8ffe31c71bdd21/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_432265`

##### `saos_pl:387131` — SENTENCE XVII AmT 16/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 16/17
- summary_1line: Caselaw corpus record: XVII AMT 16/17.
- external_id: saos:387131
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:387131/raw/6e1c24b1e42c482acd2dbd5e128727cb54441e775018afa30984e3228f1aa378/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_387131`

##### `saos_pl:456909` — SENTENCE XVII AmT 169/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 169/19
- summary_1line: Caselaw corpus record: XVII AMT 169/19.
- external_id: saos:456909
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:456909/raw/3b232babc26e1ffbdc100bf69cf6e9049c7f15486a0c7c825668690c27a4b8a0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_456909`

##### `saos_pl:493222` — SENTENCE XVII AmT 176/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 176/19
- summary_1line: Caselaw corpus record: XVII AMT 176/19.
- external_id: saos:493222
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:493222/raw/cd77a2743ffed0336bc5907316498245c57a518bfc098720f8057cd6890526c3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_493222`

##### `saos_pl:220075` — SENTENCE XVII AmT 19/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 19/12
- summary_1line: Caselaw corpus record: XVII AMT 19/12.
- external_id: saos:220075
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:220075/raw/4f51a3be85245a21edd19ad75c091c0ed78b518a16e0c1637a3d312dee407a15/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_220075`

##### `saos_pl:367303` — SENTENCE XVII AmT 20/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 20/16
- summary_1line: Caselaw corpus record: XVII AMT 20/16.
- external_id: saos:367303
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:367303/raw/111cb747bf907e22cc8a13b28d38aee17f325d80045f57e3833037f3b80f1764/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_367303`

##### `saos_pl:462155` — SENTENCE XVII AmT 20/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 20/18
- summary_1line: Caselaw corpus record: XVII AMT 20/18.
- external_id: saos:462155
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:462155/raw/80a4f791de55e11c033a2a337c24bcf9ee1dc63a50890bfaa1db437c98574aca/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_462155`

##### `saos_pl:483847` — SENTENCE XVII AmT 209/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 209/19
- summary_1line: Caselaw corpus record: XVII AMT 209/19.
- external_id: saos:483847
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:483847/raw/77f572cf4d01f030f7c0602f3829ce8862dc69cbe60f95372d4b96d1e9fa0dbe/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_483847`

##### `saos_pl:449350` — SENTENCE XVII AmT 22/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 22/17
- summary_1line: Caselaw corpus record: XVII AMT 22/17.
- external_id: saos:449350
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:449350/raw/e613067c1284de8d287dd96fdd4732700d25c2421e211b04d24b2fb9bfec66b3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_449350`

##### `saos_pl:449445` — SENTENCE XVII AmT 235/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 235/19
- summary_1line: Caselaw corpus record: XVII AMT 235/19.
- external_id: saos:449445
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:449445/raw/0b584d51d43c37ca5dabd191519c1c8aba43ac04a1cdcb597b92d8a98e4b9f39/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_449445`

##### `saos_pl:381296` — SENTENCE XVII AmT 26/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 26/16
- summary_1line: Caselaw corpus record: XVII AMT 26/16.
- external_id: saos:381296
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:381296/raw/0747f0b0f96cdfaff84dbe203ff4f6e3054648f4fd0b29413bd9c9d6d5a84edf/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_381296`

##### `saos_pl:515217` — SENTENCE XVII AmT 27/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 27/22
- summary_1line: Caselaw corpus record: XVII AMT 27/22.
- external_id: saos:515217
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:515217/raw/d3d6268085e75d3a04007f5a446aed01331d7009d9216af72c44eb7a60b02a60/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_515217`

##### `saos_pl:423809` — SENTENCE XVII AmT 28/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 28/18
- summary_1line: Caselaw corpus record: XVII AMT 28/18.
- external_id: saos:423809
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:423809/raw/237d6b655109eb21c068deab262e2d63b6550112f379a5fa59b9cf06453e60aa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_423809`

##### `saos_pl:515218` — SENTENCE XVII AmT 28/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 28/22
- summary_1line: Caselaw corpus record: XVII AMT 28/22.
- external_id: saos:515218
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:515218/raw/270f242911efdbe8ea222d31671675a8e0e2ed135c9b71d626cf803e6aa9036a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_515218`

##### `saos_pl:447845` — SENTENCE XVII AmT 3/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 3/17
- summary_1line: Caselaw corpus record: XVII AMT 3/17.
- external_id: saos:447845
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:447845/raw/0429586f54c1d1da2855d8af32bcd6ac23c18d96fe0778273bf47ae81ea43180/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_447845`

##### `saos_pl:459436` — SENTENCE XVII AmT 35/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 35/16
- summary_1line: Caselaw corpus record: XVII AMT 35/16.
- external_id: saos:459436
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:459436/raw/5da8d4d5289a7a821ebe57386e60d77fe7eb4dbed4f4bd94a91048b875fb418e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_459436`

##### `saos_pl:374392` — SENTENCE XVII AmT 36/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 36/15
- summary_1line: Caselaw corpus record: XVII AMT 36/15.
- external_id: saos:374392
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:374392/raw/b4401dd56e74bff02341a59c03968da0b1a7a99d75983a9688b63affcbea6b89/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_374392`

##### `saos_pl:518869` — SENTENCE XVII AmT 4/23 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 4/23
- summary_1line: Caselaw corpus record: XVII AMT 4/23.
- external_id: saos:518869
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:518869/raw/cfc941481847f01cad83fd4d9f34f43add9861e8a634782d654e7bfbd86d8c3a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_518869`

##### `saos_pl:437859` — SENTENCE XVII AmT 40/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 40/18
- summary_1line: Caselaw corpus record: XVII AMT 40/18.
- external_id: saos:437859
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:437859/raw/f1d33bb1fa205e9af10841768cf009878a7e2a33bf02a2656b55e79499aefdfa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_437859`

##### `saos_pl:459437` — SENTENCE XVII AmT 41/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 41/18
- summary_1line: Caselaw corpus record: XVII AMT 41/18.
- external_id: saos:459437
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:459437/raw/0a89a76927391dc0428b738f0ee1ea35fb783e1bc80d727b1e7b9d214c545add/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_459437`

##### `saos_pl:435653` — SENTENCE XVII AmT 44/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 44/18
- summary_1line: Caselaw corpus record: XVII AMT 44/18.
- external_id: saos:435653
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:435653/raw/a1948e5bf0270fba39d7e3f54891a2632f73e9161b1594f02484ec5986f7c0eb/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_435653`

##### `saos_pl:521398` — SENTENCE XVII AmT 45/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 45/19
- summary_1line: Caselaw corpus record: XVII AMT 45/19.
- external_id: saos:521398
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:521398/raw/4e01dc1ea2c3ebd1afb607eccb40f3eb63d53493b181c324ae1d08d08e128e78/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_521398`

##### `saos_pl:381724` — SENTENCE XVII AmT 49/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 49/16
- summary_1line: Caselaw corpus record: XVII AMT 49/16.
- external_id: saos:381724
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:381724/raw/4052ddea3ff218c8150d3b093e9c1c0be5de9a1a2c0fa462445ccdce3d1b4043/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_381724`

##### `saos_pl:434399` — SENTENCE XVII AmT 54/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 54/16
- summary_1line: Caselaw corpus record: XVII AMT 54/16.
- external_id: saos:434399
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:434399/raw/9c464299d8140cf24e5ac29771a97bad4e5534ca6d7c9689cb219e5fcb015058/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_434399`

##### `saos_pl:446258` — SENTENCE XVII AmT 57/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 57/16
- summary_1line: Caselaw corpus record: XVII AMT 57/16.
- external_id: saos:446258
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:446258/raw/77bcc6fa80fd675b8a43b4a96b49b15e611ba070bc65908028a53f12a5ab6985/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_446258`

##### `saos_pl:515235` — SENTENCE XVII AmT 57/21 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 57/21
- summary_1line: Caselaw corpus record: XVII AMT 57/21.
- external_id: saos:515235
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:515235/raw/269a9483ea3c2f4d2cc1cdd10e2acdf5c9a3c80530c71456e6af01b56fc9c80e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_515235`

##### `saos_pl:468705` — SENTENCE XVII AmT 58/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 58/18
- summary_1line: Caselaw corpus record: XVII AMT 58/18.
- external_id: saos:468705
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:468705/raw/3ed7e23f80df33a395ad858e14d120b06cb0c84ebb57195b07bc1df0a47aeb75/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_468705`

##### `saos_pl:429677` — SENTENCE XVII AmT 69/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 69/18
- summary_1line: Caselaw corpus record: XVII AMT 69/18.
- external_id: saos:429677
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:429677/raw/73a17cf66c5bd16eea7671961d6889fbf28ab229e4d4105624340128dca041bd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_429677`

##### `saos_pl:431986` — SENTENCE XVII AmT 8/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 8/17
- summary_1line: Caselaw corpus record: XVII AMT 8/17.
- external_id: saos:431986
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:431986/raw/807cc2689fb3815c00ca3165c22f7754f04509a954e4bff7695915bb10248682/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_431986`

##### `saos_pl:444281` — SENTENCE XVII AmT 8/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 8/19
- summary_1line: Caselaw corpus record: XVII AMT 8/19.
- external_id: saos:444281
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:444281/raw/11e49f62ee1cd02602d43663924583546acf3a8877542fc2f505634954a5af47/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_444281`

##### `saos_pl:515237` — SENTENCE XVII AmT 8/22 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 8/22
- summary_1line: Caselaw corpus record: XVII AMT 8/22.
- external_id: saos:515237
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:515237/raw/7b4a9e80ad0b2b2bef7aa45c2d71e95d056390bc67261962d3772700a313ede0/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_515237`

##### `saos_pl:433839` — SENTENCE XVII AmT 82/18 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 82/18
- summary_1line: Caselaw corpus record: XVII AMT 82/18.
- external_id: saos:433839
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:433839/raw/bf6c8284bab5b01f8063b27a844dd2dd21a10091b0b48913531af0a6bfe70c6d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_433839`

##### `saos_pl:462285` — SENTENCE XVII AmT 86/20 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 86/20
- summary_1line: Caselaw corpus record: XVII AMT 86/20.
- external_id: saos:462285
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:462285/raw/7aff62d785cb7f9928ab08e201e3ecfceec965a3309e5c9a8b2b41e6e8007bd7/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_462285`

##### `saos_pl:445850` — SENTENCE XVII AmT 9/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 9/16
- summary_1line: Caselaw corpus record: XVII AMT 9/16.
- external_id: saos:445850
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:445850/raw/fc5159924a776d0e2f62cb0b9d8e6e6c0fdb11898fe1acf587f480cb6713256e/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_445850`

##### `saos_pl:443031` — SENTENCE XVII AmT 9/19 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVII AMT 9/19
- summary_1line: Caselaw corpus record: XVII AMT 9/19.
- external_id: saos:443031
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:443031/raw/cfd11f89af900dc0f6662d478824b7662da44d021461090cc6806771cc1d5406/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_443031`

##### `saos_pl:291743` — SENTENCE XVIII C 1594/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XVIII C 1594/15
- summary_1line: Caselaw corpus record: XVIII C 1594/15.
- external_id: saos:291743
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:291743/raw/ed8139545c24a6c6a5d8c77a53298f3d1177a740c197617725ca09f93ad9ee15/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_291743`

##### `saos_pl:382616` — SENTENCE XX GC 1071/16 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 1071/16
- summary_1line: Caselaw corpus record: XX GC 1071/16.
- external_id: saos:382616
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:382616/raw/6180187a0c652d8943bc54e6198882af5765a2e6f4a87d793c1897ff03b26baa/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_382616`

##### `saos_pl:320023` — SENTENCE XX GC 164/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 164/11
- summary_1line: Caselaw corpus record: XX GC 164/11.
- external_id: saos:320023
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:320023/raw/d67e322a8066ce5f10f692d5528e3a4c077c717d3108117df8eea4c1d400ee5d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_320023`

##### `saos_pl:540619` — SENTENCE XX GC 202/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 202/17
- summary_1line: Caselaw corpus record: XX GC 202/17.
- external_id: saos:540619
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:540619/raw/4f40aa1b31d52852fbf816d8d709240dcddb01784c6387869ef6539901a1709a/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_540619`

##### `saos_pl:383111` — SENTENCE XX GC 543/11 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 543/11
- summary_1line: Caselaw corpus record: XX GC 543/11.
- external_id: saos:383111
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:383111/raw/4c6dc74453596424f677c07ca16561d61d425d7ef0deccc73d5708306d37c303/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_383111`

##### `saos_pl:472693` — SENTENCE XX GC 726/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 726/17
- summary_1line: Caselaw corpus record: XX GC 726/17.
- external_id: saos:472693
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:472693/raw/1d1f7290e08ab827ed1763dc9d6a2dc5805fcb10567b379735a85f465775bebd/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_472693`

##### `saos_pl:315238` — SENTENCE XX GC 828/10 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XX GC 828/10
- summary_1line: Caselaw corpus record: XX GC 828/10.
- external_id: saos:315238
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:315238/raw/7b0c5d0b534ef3bbdd354cf4fcc5f437745a7d1e7ee625e219494fcf45e74592/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_315238`

##### `saos_pl:189740` — SENTENCE XXIII Ga 1603/12 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXIII GA 1603/12
- summary_1line: Caselaw corpus record: XXIII GA 1603/12.
- external_id: saos:189740
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:189740/raw/eb6303655290e8fb2ea1881660347bbe294a9b696b3cdb727b6e3e48c1d06c8f/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_189740`

##### `saos_pl:52159` — SENTENCE XXIII Ga 678/13 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXIII GA 678/13
- summary_1line: Caselaw corpus record: XXIII GA 678/13.
- external_id: saos:52159
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:52159/raw/304f76b23158ab2c886ded9986dbd22894eb8b463820255d258c76407dd3c83c/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_52159`

##### `saos_pl:237638` — SENTENCE XXIV C 1111/15 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXIV C 1111/15
- summary_1line: Caselaw corpus record: XXIV C 1111/15.
- external_id: saos:237638
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:237638/raw/5c7e22920a977315fa0148f73d8e53ef22ea096c4acf488ae97545a7573e1551/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_237638`

##### `saos_pl:385263` — SENTENCE XXV C 1018/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXV C 1018/17
- summary_1line: Caselaw corpus record: XXV C 1018/17.
- external_id: saos:385263
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:385263/raw/b1a48e65db40e2ae0f40b9d805002cb09fa6d76821ecfc32091c980227cf2387/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_385263`

##### `saos_pl:407096` — SENTENCE XXV C 1046/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXV C 1046/17
- summary_1line: Caselaw corpus record: XXV C 1046/17.
- external_id: saos:407096
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:407096/raw/61416e85a6b80caf22f24a83b448ec0313b6fdb762256e65cc7ddc1cab59c38d/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_407096`

##### `saos_pl:421104` — SENTENCE XXV C 1234/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXV C 1234/17
- summary_1line: Caselaw corpus record: XXV C 1234/17.
- external_id: saos:421104
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:421104/raw/b6b3fbff2e2c7c3329cf0f1b5ba2c413a0ca9505da51cee08a4b9a83ac852609/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_421104`

##### `saos_pl:398118` — SENTENCE XXV C 265/17 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXV C 265/17
- summary_1line: Caselaw corpus record: XXV C 265/17.
- external_id: saos:398118
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:398118/raw/159ea3e1ec89cb9a4dc200c81b50e3a61783e4a5e89ae73106548de9ccdbea72/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_398118`

##### `saos_pl:223773` — SENTENCE XXVI GC 1048/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXVI GC 1048/14
- summary_1line: Caselaw corpus record: XXVI GC 1048/14.
- external_id: saos:223773
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:223773/raw/772af75d51d584f82978d95809e1da194bff0d913c52b08727279dc889bf8eef/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_223773`

##### `saos_pl:251097` — SENTENCE XXVI GC 330/14 (COMMON)

- status: `active`
- document_kind: `CASELAW`
- legal_role: `GENERAL_CASELAW`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: XXVI GC 330/14
- summary_1line: Caselaw corpus record: XXVI GC 330/14.
- external_id: saos:251097
- source_url: https://www.saos.org.pl/
- normalized_source_url: https://www.saos.org.pl/
- storage_uri: ./artifacts_iter5_3/docs/saos_pl:251097/raw/b95de1e161e4ead3f005d83fa3c74822a0b3a76a8eaae7848f539c8f3139a2d3/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_251097`

##### `saos_pl:330695` — Wyrok II C 442/16

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `SUPPORTING_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: II C 442/16
- summary_1line: Caselaw corpus record: II C 442/16.
- external_id: saos:330695
- source_url: https://www.saos.org.pl/judgments/330695
- normalized_source_url: https://www.saos.org.pl/judgments/330695
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:330695/raw/015342b0bfd78127d5f3b865b539da0fef519a2f3bc18cf316ac6aeb9b8e77d8/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_330695`

##### `saos_pl:486542` — Wyrok dotyczacy foreign-law / German BGB deposit issue

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `OPTIONAL_EU`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: Wyrok dotyczacy foreign-law / German BGB deposit issue
- summary_1line: Caselaw corpus record: Wyrok dotyczacy foreign-law / German BGB deposit issue.
- external_id: saos:486542
- source_url: https://www.saos.org.pl/judgments/486542
- normalized_source_url: https://www.saos.org.pl/judgments/486542
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:486542/raw/0c6f071ca3183f7fa72c5fb7b0984b11b0fec516ff0d0681fef51199de4b39ad/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_486542`

##### `saos_pl:487012` — Wyrok dotyczacy rozliczen najmu i limitation

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `SUPPORTING_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: Wyrok dotyczacy rozliczen najmu i limitation
- summary_1line: Caselaw corpus record: Wyrok dotyczacy rozliczen najmu i limitation.
- external_id: saos:487012
- source_url: https://www.saos.org.pl/judgments/487012
- normalized_source_url: https://www.saos.org.pl/judgments/487012
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:487012/raw/4efafe80202281429d9f26dc9473d44c62c3e91927ce21b800f3a19c7270e750/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_487012`

##### `saos_pl:521555` — Wyrok niebedacy klasycznym zwrotem kaucji

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `SUPPORTING_CASE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: Wyrok niebedacy klasycznym zwrotem kaucji
- summary_1line: Caselaw corpus record: Wyrok niebedacy klasycznym zwrotem kaucji.
- external_id: saos:521555
- source_url: https://www.saos.org.pl/judgments/521555
- normalized_source_url: https://www.saos.org.pl/judgments/521555
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:521555/raw/923d387e3884ef65ddbf53496a714be00c0420b0bfd1bddbdf5dbc72efab149b/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_521555`

##### `saos_pl:urlsha:c9e2fcff50755b83` — SAOS search seed for kaucja mieszkaniowa

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `SEARCH_PAGE`
- source_system: `saos_pl`
- source_tier: `saos`
- title_short: SAOS search seed for kaucja mieszkaniowa
- summary_1line: Caselaw corpus record: SAOS search seed for kaucja mieszkaniowa.
- external_id: saos-search:kaucja-mieszkaniowa
- source_url: https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa
- normalized_source_url: https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja mieszkaniowa
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/saos_pl:urlsha:c9e2fcff50755b83/raw/93874d6375d518bd76812d3ebd47b250040aa57a69fc708453eb5b535bbb7423/original.bin
- same_case_group_id: `same_case:singleton:saos_pl_urlsha_c9e2fcff50755b83`
- superseded_by: `search_page`
- exclusion_reason: Search pages can never be canonical runtime documents.

#### `sn_pl` (10)

##### `sn_pl:III_CZP_58-02` — Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `LEADING_CASE`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: III CZP 58/02
- summary_1line: Caselaw corpus record: III CZP 58/02.
- external_id: sn:III CZP 58/02
- source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf
- storage_uri: artifacts_dev/docs/sn_pl:III_CZP_58-02/raw/d3709c570b1e67ad0a6e89074b1a977e8633737459eeaf77fcede775ffb01699/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_iii_czp_58_02`
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `sn_pl:III_CZP_58-02`

##### `sn_pl:I_CSK_292-12` — Wyrok SN I CSK 292/12

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `SUPPORTING_CASE`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: I CSK 292/12
- summary_1line: Caselaw corpus record: I CSK 292/12.
- external_id: sn:I CSK 292/12
- source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf
- storage_uri: artifacts_dev/docs/sn_pl:I_CSK_292-12/raw/71120129d54f581a66eb19fbb638dae19d751f21f53f06350e5e91820f0002ae/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_i_csk_292_12`
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `sn_pl:I_CSK_292-12`

##### `sn_pl:II_CSK_862-14` — Wyrok SN II CSK 862/14

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `SUPPORTING_CASE`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: II CSK 862/14
- summary_1line: Caselaw corpus record: II CSK 862/14.
- external_id: sn:II CSK 862/14
- source_url: https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf
- storage_uri: artifacts_dev/docs/sn_pl:II_CSK_862-14/raw/2be5896587cf33f4548426b4cc9b2c0956d5f0b855f9eebe83247040ae492879/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_ii_csk_862_14`
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `sn_pl:II_CSK_862-14`

##### `sn_pl:urlsha:c37d660f070b6362` — Uchwala SN z dnia 26 wrzesnia 2002 r., III CZP 58/02

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `DUPLICATE_ALIAS`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: III CZP 58/02
- summary_1line: Alias record for III CZP 58/02; refer to sn_pl:III_CZP_58-02 for operational use.
- external_id: sn:III CZP 58/02
- source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/sn_pl:urlsha:c37d660f070b6362/raw/d3709c570b1e67ad0a6e89074b1a977e8633737459eeaf77fcede775ffb01699/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_urlsha_c37d660f070b6362`
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `sn_pl:III_CZP_58-02`
- canonical_doc_uid: `sn_pl:III_CZP_58-02`
- superseded_by: `sn_pl:III_CZP_58-02`

##### `sn_pl:urlsha:6c531a2c07ebe6d8` — Wyrok SN I CSK 292/12

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `DUPLICATE_ALIAS`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: I CSK 292/12
- summary_1line: Alias record for I CSK 292/12; refer to sn_pl:I_CSK_292-12 for operational use.
- external_id: sn:I CSK 292/12
- source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/sn_pl:urlsha:6c531a2c07ebe6d8/raw/71120129d54f581a66eb19fbb638dae19d751f21f53f06350e5e91820f0002ae/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_urlsha_6c531a2c07ebe6d8`
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `sn_pl:I_CSK_292-12`
- canonical_doc_uid: `sn_pl:I_CSK_292-12`
- superseded_by: `sn_pl:I_CSK_292-12`

##### `sn_pl:urlsha:7da32fd244aa72ab` — Wyrok SN II CSK 862/14

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `DUPLICATE_ALIAS`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: II CSK 862/14
- summary_1line: Alias record for II CSK 862/14; refer to sn_pl:II_CSK_862-14 for operational use.
- external_id: sn:II CSK 862/14
- source_url: https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/sn_pl:urlsha:7da32fd244aa72ab/raw/2be5896587cf33f4548426b4cc9b2c0956d5f0b855f9eebe83247040ae492879/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_urlsha_7da32fd244aa72ab`
- duplicate_role: `alias`
- duplicate_owner_doc_uid: `sn_pl:II_CSK_862-14`
- canonical_doc_uid: `sn_pl:II_CSK_862-14`
- superseded_by: `sn_pl:II_CSK_862-14`

##### `sn_pl:I_CNP_31-13` — Postanowienie SN I CNP 31/13

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `EXCLUDED`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: I CNP 31/13
- summary_1line: Caselaw corpus record: I CNP 31/13.
- external_id: sn:I CNP 31/13
- source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html
- storage_uri: artifacts_dev/docs/sn_pl:I_CNP_31-13/raw/c378b7f9c4d6a224cb9745bd566de6aace45588c6e08c5c93bd913b136bb26b1/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_i_cnp_31_13`
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `sn_pl:I_CNP_31-13`
- superseded_by: `sn_pl:I_CNP_31-13`
- exclusion_reason: Commercial dispute outside tenant-vs-landlord scope.

##### `sn_pl:urlsha:961104dfb49b592b` — Postanowienie SN I CNP 31/13

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: I CNP 31/13
- summary_1line: Excluded inventory record retained for traceability: I CNP 31/13.
- external_id: sn:I CNP 31/13
- source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/sn_pl:urlsha:961104dfb49b592b/raw/79fdaec99d08773b9a234cb885f2c71b4bfc301ca7bb3f159fcd8e9c4e2d26b5/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_urlsha_961104dfb49b592b`
- duplicate_role: `excluded`
- duplicate_owner_doc_uid: `sn_pl:I_CNP_31-13`
- canonical_doc_uid: `sn_pl:I_CNP_31-13`
- superseded_by: `sn_pl:I_CNP_31-13`
- exclusion_reason: Duplicate representation retained for inventory only.

##### `sn_pl:V_CSK_480-18` — Postanowienie SN V CSK 480/18

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `EXCLUDED`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: V CSK 480/18
- summary_1line: Caselaw corpus record: V CSK 480/18.
- external_id: sn:V CSK 480/18
- source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html
- storage_uri: artifacts_dev/docs/sn_pl:V_CSK_480-18/raw/48d77adc5be755e58d9a48ea620d853f98672571a758cdc85b8b5e8371858648/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_v_csk_480_18`
- duplicate_role: `owner`
- duplicate_owner_doc_uid: `sn_pl:V_CSK_480-18`
- superseded_by: `sn_pl:V_CSK_480-18`
- exclusion_reason: Commercial dispute outside tenant-vs-landlord scope.

##### `sn_pl:urlsha:5a30a43aa6a12b31` — Postanowienie SN V CSK 480/18

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `sn_pl`
- source_tier: `official`
- title_short: V CSK 480/18
- summary_1line: Excluded inventory record retained for traceability: V CSK 480/18.
- external_id: sn:V CSK 480/18
- source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html
- normalized_source_url: https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/sn_pl:urlsha:5a30a43aa6a12b31/raw/b20dadba0cb5ffeb8aada00eb0e9884cf087de6575e1b86edd869f3977232775/original.bin
- same_case_group_id: `same_case:singleton:sn_pl_urlsha_5a30a43aa6a12b31`
- duplicate_role: `excluded`
- duplicate_owner_doc_uid: `sn_pl:V_CSK_480-18`
- canonical_doc_uid: `sn_pl:V_CSK_480-18`
- superseded_by: `sn_pl:V_CSK_480-18`
- exclusion_reason: Duplicate representation retained for inventory only.

#### `courts_pl` (3)

##### `courts_pl:urlsha:20c9c82554a6e7f2` — Wyrok I Ca 56/18

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `PORTAL_MIRROR`
- source_system: `courts_pl`
- source_tier: `court_portal`
- title_short: I CA 56/18
- summary_1line: Alias record for I CA 56/18; refer to saos_pl:360096 for operational use.
- external_id: case:I Ca 56/18
- source_url: https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001
- normalized_source_url: https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/courts_pl:urlsha:20c9c82554a6e7f2/raw/8fe24438069f1fdca3040e993b6ca204a85834e873b5f906be7cb28859d0e80d/original.bin
- same_case_group_id: `same_case:i_ca_56_18`
- canonical_doc_uid: `saos_pl:360096`
- superseded_by: `saos_pl:360096`

##### `courts_pl:urlsha:74cfe0dfc8b4592a` — Wyrok III Ca 1707/18

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `PORTAL_MIRROR`
- source_system: `courts_pl`
- source_tier: `court_portal`
- title_short: III CA 1707/18
- summary_1line: Alias record for III CA 1707/18; refer to saos_pl:385394 for operational use.
- external_id: case:III Ca 1707/18
- source_url: https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001
- normalized_source_url: https://orzeczenia.ms.gov.pl/content/$N/152510000001503_III_Ca_001707_2018_Uz_2019-02-28_001
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/courts_pl:urlsha:74cfe0dfc8b4592a/raw/a8a4e4fec6445f453c296c8e3a4c824596dca81f238650c397ca43369b97e1dd/original.bin
- same_case_group_id: `same_case:iii_ca_1707_18`
- canonical_doc_uid: `saos_pl:385394`
- superseded_by: `saos_pl:385394`

##### `courts_pl:urlsha:9ea678728691b52e` — Wyrok V ACa 599/14

- status: `alias`
- document_kind: `CASELAW`
- legal_role: `PORTAL_MIRROR`
- source_system: `courts_pl`
- source_tier: `court_portal`
- title_short: V ACA 599/14
- summary_1line: Alias record for V ACA 599/14; refer to saos_pl:132635 for operational use.
- external_id: case:V ACa 599/14
- source_url: https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001
- normalized_source_url: https://orzeczenia.katowice.sa.gov.pl/content/$N/151500000002503_V_ACa_000599_2014_Uz_2015-02-18_001
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/courts_pl:urlsha:9ea678728691b52e/raw/e6cb162707c35cf13d0fa87ab8fbcb058cd033733bceff6df50d12ae548f4b52/original.bin
- same_case_group_id: `same_case:v_aca_599_14`
- canonical_doc_uid: `saos_pl:132635`
- superseded_by: `saos_pl:132635`

#### `curia_eu` (3)

##### `curia_eu:urlsha:ef65918198e5ffee` — C-243/08 Pannon GSM

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `curia_eu`
- source_tier: `official`
- title_short: C-243/08
- summary_1line: Caselaw corpus record: C-243/08.
- external_id: curia:74812
- source_url: https://curia.europa.eu/juris/document/document.jsf?docid=74812&doclang=EN
- normalized_source_url: https://curia.europa.eu/juris/document/document.jsf?docid=74812&doclang=EN
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/curia_eu:urlsha:ef65918198e5ffee/raw/5b87994be9e299cf16a72fcc7742ded10e784f9e28015d193f49b42591223b6b/original.bin
- same_case_group_id: `same_case:singleton:curia_eu_urlsha_ef65918198e5ffee`

##### `curia_eu:urlsha:54acc341b17f3a57` — C-488/11 Asbeek Brusse and Katarina de Man Garabito

- status: `canonical`
- document_kind: `CASELAW`
- legal_role: `EU_CONSUMER_LAYER`
- source_system: `curia_eu`
- source_tier: `official`
- title_short: C-488/11
- summary_1line: Caselaw corpus record: C-488/11.
- external_id: curia:137830
- source_url: https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN
- normalized_source_url: https://curia.europa.eu/juris/document/document.jsf?docid=137830&doclang=EN
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/curia_eu:urlsha:54acc341b17f3a57/raw/5b87994be9e299cf16a72fcc7742ded10e784f9e28015d193f49b42591223b6b/original.bin
- same_case_group_id: `same_case:singleton:curia_eu_urlsha_54acc341b17f3a57`

##### `curia_eu:urlsha:71b42cdf7ec305a3` — C-229/19 Dexia Nederland

- status: `optional`
- document_kind: `CASELAW`
- legal_role: `OPTIONAL_EU`
- source_system: `curia_eu`
- source_tier: `official`
- title_short: C-229/19
- summary_1line: Caselaw corpus record: C-229/19.
- external_id: curia:237043
- source_url: https://curia.europa.eu/juris/document/document.jsf?docid=237043&doclang=en
- normalized_source_url: https://curia.europa.eu/juris/document/document.jsf?docid=237043&doclang=en
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/curia_eu:urlsha:71b42cdf7ec305a3/raw/5b87994be9e299cf16a72fcc7742ded10e784f9e28015d193f49b42591223b6b/original.bin
- same_case_group_id: `same_case:singleton:curia_eu_urlsha_71b42cdf7ec305a3`

#### `eurlex_eu` (3)

##### `eurlex_eu:urlsha:86a3a115b4b0e267` — EUR-Lex document celex:62008CJ0243

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: C-243/08
- summary_1line: Excluded inventory record retained for traceability: C-243/08.
- external_id: celex:62008CJ0243
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62008CJ0243
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62008CJ0243
- storage_uri: docs/eurlex_eu:urlsha:86a3a115b4b0e267/raw/ERROR/original.bin
- same_case_group_id: `same_case:singleton:eurlex_eu_urlsha_86a3a115b4b0e267`
- superseded_by: `inventory_only`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

##### `eurlex_eu:urlsha:3cc91aee0436279b` — EUR-Lex document celex:62011CJ0415

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: C-415/11
- summary_1line: Excluded inventory record retained for traceability: C-415/11.
- external_id: celex:62011CJ0415
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62011CJ0415
- storage_uri: docs/eurlex_eu:urlsha:3cc91aee0436279b/raw/ERROR/original.bin
- same_case_group_id: `same_case:singleton:eurlex_eu_urlsha_3cc91aee0436279b`
- superseded_by: `inventory_only`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

##### `eurlex_eu:urlsha:51fd4eed44abc101` — EUR-Lex document celex:62019CJ0725

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `eurlex_eu`
- source_tier: `official`
- title_short: C-725/19
- summary_1line: Excluded inventory record retained for traceability: C-725/19.
- external_id: celex:62019CJ0725
- source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62019CJ0725
- normalized_source_url: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:62019CJ0725
- storage_uri: docs/eurlex_eu:urlsha:51fd4eed44abc101/raw/ERROR/original.bin
- same_case_group_id: `same_case:singleton:eurlex_eu_urlsha_51fd4eed44abc101`
- superseded_by: `inventory_only`
- exclusion_reason: Broken imported artifact retained for inventory only. Reasons: broken imported artifact path; invalid checksum sentinel; nonexistent storage path.

#### `uokik_pl` (1)

##### `uokik_pl:urlsha:5efe92f726049194` — AmC 86/2003

- status: `excluded`
- document_kind: `CASELAW`
- legal_role: `INVENTORY_ONLY`
- source_system: `uokik_pl`
- source_tier: `official`
- title_short: AMC 86/03
- summary_1line: Excluded inventory record retained for traceability: AMC 86/03.
- external_id: uokik:AmC 86/2003
- source_url: https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf
- normalized_source_url: https://rejestr.uokik.gov.pl/uzasadnienia/891/AmC%20_86_2003.pdf
- storage_uri: /Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja/artifacts/legal_rag_runtime_import/caslaw-md-flat-20260306T190935Z/docs/uokik_pl:urlsha:5efe92f726049194/raw/8e2daa04c9d2c88c17c2a1c2af91f20dc2a3f90dc0acf92e6aa0675a38dc9872/original.bin
- same_case_group_id: `same_case:singleton:uokik_pl_urlsha_5efe92f726049194`
- superseded_by: `inventory_only`
- exclusion_reason: Developer/admin relation only; move out of core runtime.
