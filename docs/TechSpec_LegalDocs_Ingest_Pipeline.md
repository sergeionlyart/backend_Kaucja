Ниже — TechSpec (ТЗ) для разработчика на реализацию пайплайна ingest/normalization → MongoDB для юридического корпуса (PL/EU) под будущий RAG “в духе PageIndex”: хранение постраничного текста + иерархических узлов (tree index) + метаданных/ссылок.

⸻

TechSpec: LegalDocs Ingest Pipeline → Normalized Corpus in MongoDB

0) Цель и результат

Цель

Сделать пайплайн, который:
	1.	По заданным ссылкам скачивает документы (PDF/HTML + SAOS по API).
	2.	Нормализует контент в машинно‑читаемый формат:
	•	PDF: извлечение текста (PyMuPDF),
	•	fallback на Mistral OCR 3 (POST /v1/ocr) при плохом качестве текстового слоя.  ￼
	3.	Приводит контент и метаданные к единой структуре:
	•	documents (карточка документа),
	•	document_sources (источник/сырьё/версии),
	•	pages (постранично/виртуально‑постранично),
	•	nodes (узлы дерева с диапазоном страниц),
	•	citations (ссылки/покликанные нормы),
	•	ingest_runs (прогоны пайплайна).
	4.	Загружает результат в MongoDB через идемпотентные upsert’ы и уникальные индексы.

Результат (deliverables)
	•	CLI‑утилита legal_ingest (или модуль python -m legal_ingest ...).
	•	Конфиг config.yml (пример ниже) и README с командой тестового прогона.
	•	Mongo‑коллекции с документированными схемами + индексы.
	•	Артефакты на диске: сохранённые raw‑файлы + нормализованные JSONL.
	•	Набор unit/integration тестов + критерии приёмки (в конце).

⸻

1) Область применения и ограничения

В scope
	•	Поддержка источников из списка пользователя:
	•	PDF: ELI, ISAP, SN, UOKiK, Rejestr UOKiK и др.
	•	HTML: EUR‑Lex, Curia, суд. порталы, SN docx.html, UOKiK страницы, prawo.pl.
	•	SAOS: ingest решений по ID через API https://www.saos.org.pl/api/judgments/{id}  ￼
	•	опционально ingest результатов поиска через API https://www.saos.org.pl/api/search/judgments  ￼
	•	Нормализация под будущий “PageIndex‑style tree search”: узлы (nodes) должны иметь start_index/end_index по страницам и title/node_id/summary (nullable).  ￼

Out of scope (можно позже)
	•	Полное юридическое “понимание” норм (effective dates, редакции, консолидации).
	•	Генерация summary/doc_description через LLM (оставляем поля, но шаг можно выключить).
	•	Полный парсинг ссылок‑цитирований для всех документов (в MVP обязательно только SAOS referencedRegulations).

⸻

2) Входные данные

2.1. Конфигурация (YAML)

Пайплайн принимает один YAML‑файл (строго валидируемый через Pydantic).

Формат config.yml:

run:
  run_id: "auto"                 # auto => ULID/UUID
  dry_run: false
  artifact_dir: "./artifacts"
  concurrency: 4
  http:
    user_agent: "LegalRAG-Ingest/0.1"
    timeout_seconds: 60
    max_retries: 4
    retry_backoff_seconds: 2.0

mongo:
  uri: "mongodb://localhost:27017"
  db: "legal_rag"
  write_concern: "majority"

parsers:
  pdf:
    engine: "pymupdf"             # required: pymupdf
    # критерии для OCR fallback:
    min_avg_chars_per_page: 200
    max_empty_page_ratio: 0.30
  html:
    engine: "bs4"
    max_tokens_per_virtual_page: 1200
    min_heading_to_split: 2       # H2 и ниже считаем “секции”

ocr:
  enabled: true
  provider: "mistral"
  endpoint: "https://api.mistral.ai/v1/ocr"
  api_key_env: "MISTRAL_API_KEY"
  model: "mistral-ocr-2512"       # OCR 3 model id (можно менять)
  table_format: "markdown"        # "markdown" | "html"
  include_image_base64: false
  extract_header: false
  extract_footer: false

sources:
  # --- Польша — ELI / ISAP ---
  - source_id: "pl_eli_du_2001_733"
    url: "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "STATUTE"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      eli: "DU/2001/733"

  - source_id: "pl_isap_wdu19640160093"
    url: "https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU19640160093/U/D19640093Lj.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "STATUTE"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      isap_wdu: "WDU19640160093"

  # --- Польша — LEX (может быть ограничен лицензией/доступом) ---
  - source_id: "pl_lex_ochrona_praw_lokatorow"
    url: "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658"
    fetch_strategy: "direct"
    doc_type_hint: "STATUTE_REF"
    jurisdiction: "PL"
    language: "pl"
    license_tag: "COMMERCIAL"

  - source_id: "pl_lex_art_19a"
    url: "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a"
    fetch_strategy: "direct"
    doc_type_hint: "STATUTE_REF"
    jurisdiction: "PL"
    language: "pl"
    license_tag: "COMMERCIAL"

  - source_id: "pl_lex_kc_art_118"
    url: "https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118"
    fetch_strategy: "direct"
    doc_type_hint: "STATUTE_REF"
    jurisdiction: "PL"
    language: "pl"
    license_tag: "COMMERCIAL"

  # --- Польша — SN ---
  - source_id: "pl_sn_III_CZP_58-02"
    url: "https://www.sn.pl/sites/orzecznictwo/Orzeczenia1/III%20CZP%2058-02.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      sn_signature: "III CZP 58/02"

  - source_id: "pl_sn_II_CSK_862-14"
    url: "https://www.sn.pl/sites/orzecznictwo/orzeczenia3/ii%20csk%20862-14-1.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      sn_signature: "II CSK 862/14"

  - source_id: "pl_sn_I_CSK_292-12"
    url: "https://www.sn.pl/sites/orzecznictwo/Orzeczenia2/I%20CSK%20292-12-1.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      sn_signature: "I CSK 292/12"

  - source_id: "pl_sn_V_CSK_480-18_html"
    url: "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/v%20csk%20480-18-1.docx.html"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      sn_signature: "V CSK 480/18"

  - source_id: "pl_sn_I_CNP_31-13_html"
    url: "https://www.sn.pl/sites/orzecznictwo/OrzeczeniaHTML/I%20CNP%2031-13.docx.html"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"
    external_ids:
      sn_signature: "I CNP 31/13"

  # --- SAOS: поисковый seed (опционально) ---
  - source_id: "pl_saos_search_kaucja_mieszkaniowa"
    url: "https://www.saos.org.pl/search?courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa"
    fetch_strategy: "saos_search"
    saos_search_params:
      courtType: "COMMON"
      keywords: ["kaucja mieszkaniowa"]
      pageSize: 50
      pageNumber: 0
    jurisdiction: "PL"
    language: "pl"
    doc_type_hint: "CASELAW"

  # --- SAOS: конкретные решения ---
  - source_id: "pl_saos_171957"
    url: "https://www.saos.org.pl/judgments/171957"
    fetch_strategy: "saos_judgment"
    external_ids: { saos_id: 171957 }
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"

  # ... (и так далее для 205996 ... 521555)

  # --- Порталы решений ---
  - source_id: "pl_courts_wloclawek_I_Ca_56_2018"
    url: "https://orzeczenia.wloclawek.so.gov.pl/content/$N/151030000000503_I_Ca_000056_2018_Uz_2018-05-08_001"
    fetch_strategy: "direct"
    doc_type_hint: "CASELAW"
    jurisdiction: "PL"
    language: "pl"

  # --- EU: EUR-Lex / Curia ---
  - source_id: "eu_eurlex_dir_1993_13"
    url: "https://eur-lex.europa.eu/eli/dir/1993/13/oj/eng"
    fetch_strategy: "direct"
    doc_type_hint: "EU_ACT"
    jurisdiction: "EU"
    language: "en"
    external_ids:
      eli: "dir/1993/13/oj/eng"

  # --- UOKiK / rejestr / prawo.pl ---
  - source_id: "pl_uokik_RKR_37_2013"
    url: "https://decyzje.uokik.gov.pl/bp/dec_prez.nsf/43104c28a7a1be23c1257eac006d8dd4/6168c41ed23328e8c1257ec6007ba3ca/$FILE/RKR-37-2013%20Novis%20MSK.pdf"
    fetch_strategy: "direct"
    doc_type_hint: "GUIDANCE"
    jurisdiction: "PL"
    language: "pl"

Примечание: список sources должен включать все URL из вашего набора (1–38). Для SAOS решений 12–21 — по аналогии.

⸻

3) Выходные данные

3.1. Артефакты на диске (artifact store)

В run.artifact_dir создаётся структура:

artifacts/
  runs/{run_id}/
    run_report.json
    logs.jsonl
  docs/{doc_uid}/
    raw/{source_hash}/
      original.bin          # скачанный PDF/HTML
      response_meta.json    # status_code, headers, final_url
    normalized/{source_hash}/
      pages.jsonl           # постраничный текст
      nodes.jsonl           # плоские узлы дерева
      citations.jsonl       # ссылки (если есть)
      document.json         # итоговая карточка документа (как в Mongo)

source_hash = SHA‑256 от raw bytes (для HTML — от UTF‑8 bytes canonicalized).

3.2. MongoDB: коллекции и схемы

Коллекции:
	•	documents
	•	document_sources
	•	pages
	•	nodes
	•	citations
	•	ingest_runs

Все записи обязаны содержать поля:
	•	doc_uid (string) — стабильный ID документа
	•	source_hash (string, sha256 hex) — версия сырья/контента
	•	ingested_at (datetime, ISODate)

⸻

4) Идентификаторы и идемпотентность

4.1. Генерация doc_uid (стабильно и детерминированно)

doc_uid должен быть детерминированным, чтобы повторный запуск не создавал дубликатов.

Правило:
	1.	Если в sources[].external_ids задан “главный” ID → используем его.
	2.	Иначе пытаемся извлечь ID из URL по доменным правилам.
	3.	Если не получилось → fallback: urlsha:{sha256(canonical_url)[:16]}.

Формат doc_uid:
{source_system}:{primary_id}

source_system по hostname:
	•	eli_pl (eli.gov.pl)
	•	isap_pl (isap.sejm.gov.pl)
	•	lex_pl (sip.lex.pl)
	•	sn_pl (sn.pl)
	•	saos_pl (saos.org.pl)
	•	courts_pl (orzeczenia.*)
	•	eurlex_eu (eur-lex.europa.eu)
	•	curia_eu (curia.europa.eu)
	•	uokik_pl (uokik.gov.pl / rejestr.uokik.gov.pl / decyzje.uokik.gov.pl)
	•	prawo_pl (prawo.pl)

Примеры:
	•	eli_pl:DU/2001/733
	•	isap_pl:WDU19640160093
	•	saos_pl:171957
	•	eurlex_eu:eli:dir/1993/13/oj/eng
	•	curia_eu:docid:137830
	•	sn_pl:III_CZP_58-02

4.2. Версионирование через source_hash
	•	Любая смена raw bytes ⇒ новый source_hash.
	•	documents.current_source_hash указывает на актуальную версию.
	•	pages/nodes/citations всегда записываются с привязкой к source_hash.
	•	Повторный запуск с тем же контентом не должен создавать новые записи.

4.3. Upsert‑логика
	•	documents: upsert по _id == doc_uid.
	•	document_sources: upsert по (doc_uid, source_hash).
	•	pages: upsert по (doc_uid, source_hash, page_index).
	•	nodes: upsert по (doc_uid, source_hash, node_id).
	•	citations: upsert по (doc_uid, source_hash, citation_uid).

citation_uid = sha256 от конкатенации:
from_node_id|to_anchor|raw_citation_text|target_external_id(optional).

⸻

5) MongoDB схемы (строго)

Ниже — “JSON Schema‑like” описание полей. Разработчик должен реализовать Pydantic модели с валидацией типов.

5.1. documents (карточка документа)

Коллекция: documents
Ключ: _id = doc_uid (string)

{
  "_id": "eli_pl:DU/2001/733",
  "doc_uid": "eli_pl:DU/2001/733",

  "doc_type": "STATUTE",               // enum: STATUTE | CASELAW | EU_ACT | GUIDANCE | COMMENTARY | STATUTE_REF
  "jurisdiction": "PL",                // enum: PL | EU
  "language": "pl",                    // ISO 639-1
  "source_system": "eli_pl",

  "title": "Ustawa z dnia ...",        // required if доступен
  "date_published": "2001-06-21",      // optional
  "date_decision": null,              // для CASELAW
  "version_label": null,              // напр. "t.j. 2025-12-10" (если удаётся извлечь)

  "external_ids": {                   // JSON object, optional
    "eli": "DU/2001/733"
  },

  "source_urls": [
    "https://eli.gov.pl/api/acts/DU/2001/733/text/O/D20010733.pdf"
  ],

  "license_tag": "OFFICIAL",          // OFFICIAL | COMMERCIAL | UNKNOWN
  "access_status": "OK",              // OK | RESTRICTED | ERROR
  "current_source_hash": "sha256...",
  "mime": "application/pdf",

  "page_count": 15,
  "content_stats": {
    "total_chars": 123456,
    "total_tokens_est": 45678,
    "parse_method": "PDF_TEXT",        // PDF_TEXT | OCR3 | HTML
    "ocr_used": false
  },

  // Быстрый доступ к дереву (опционально, но рекомендуется):
  "pageindex_tree": [
    {
      "title": "Rozdział 1 ...",
      "node_id": "ch:1",
      "start_index": 0,
      "end_index": 3,
      "summary": null,
      "nodes": [
        {
          "title": "Art. 6. Kaucja",
          "node_id": "art:6",
          "start_index": 1,
          "end_index": 2,
          "summary": null,
          "nodes": []
        }
      ]
    }
  ],

  "ingested_at": "2026-03-01T12:00:00Z",
  "updated_at": "2026-03-01T12:00:00Z"
}

Обязательные поля: _id/doc_uid, doc_type, jurisdiction, language, source_system, source_urls, current_source_hash, mime, ingested_at.

⸻

5.2. document_sources (сырьё и HTTP‑метаданные)

{
  "_id": "eli_pl:DU/2001/733|sha256:abcd...",   // составной string id
  "doc_uid": "eli_pl:DU/2001/733",
  "source_hash": "abcd...",

  "source_id": "pl_eli_du_2001_733",            // из config
  "url": "https://...",
  "final_url": "https://...",                   // после редиректов
  "fetched_at": "2026-03-01T12:00:00Z",
  "http": {
    "status_code": 200,
    "etag": null,
    "last_modified": null,
    "content_length": 1234567
  },

  "raw_object_path": "artifacts/docs/.../raw/.../original.bin",
  "raw_mime": "application/pdf",
  "license_tag": "OFFICIAL",

  "ingested_at": "2026-03-01T12:00:00Z"
}


⸻

5.3. pages (постраничный/виртуальный текст)

Нумерация:
	•	page_index — 0‑based.
	•	Для PDF: соответствует реальным страницам (0..N-1).
	•	Для HTML/SAOS: виртуальные страницы, сформированные разбиением по заголовкам/размеру.

{
  "_id": "eli_pl:DU/2001/733|abcd...|p:0",
  "doc_uid": "eli_pl:DU/2001/733",
  "source_hash": "abcd...",

  "page_index": 0,
  "text": "plain text ...",            // required
  "markdown": null,                    // если OCR/HTML выдаёт markdown
  "token_count_est": 950,
  "char_count": 5200,

  "extraction": {
    "method": "PDF_TEXT",              // PDF_TEXT | OCR3 | HTML
    "quality": {
      "alpha_ratio": 0.62,
      "empty": false
    },
    "ocr_meta": null                   // если OCR3: {model, page_index_raw, images_count,...}
  },

  "ingested_at": "2026-03-01T12:00:00Z"
}


⸻

5.4. nodes (плоская таблица узлов дерева)

Ключевые требования:
	•	Каждый документ должен иметь минимум один root‑узел node_id="root", который покрывает весь документ: start_index=0, end_index=page_count.
	•	Узлы имеют диапазоны [start_index, end_index) как в примере PageIndex (end exclusive).  ￼

{
  "_id": "eli_pl:DU/2001/733|abcd...|node:art:6",
  "doc_uid": "eli_pl:DU/2001/733",
  "source_hash": "abcd...",

  "node_id": "art:6",
  "parent_node_id": "root",
  "depth": 1,
  "order_index": 12,

  "title": "Art. 6. Kaucja",
  "start_index": 1,
  "end_index": 2,
  "summary": null,

  "anchors": {
    "article": "6",
    "chapter": "2"
  },

  "ingested_at": "2026-03-01T12:00:00Z"
}


⸻

5.5. citations (граф ссылок/цитирования)

MVP обязательство: для SAOS — заполнять из referencedRegulations (оно есть в SAOS API)  ￼
Для остальных источников — можно оставить пустым, но структура должна быть.

{
  "_id": "saos_pl:171957|abcd...|cit:9f3a...",
  "doc_uid": "saos_pl:171957",
  "source_hash": "abcd...",

  "from_node_id": "root",
  "raw_citation_text": "art. 6 ust. 1 ustawy ...",
  "target": {
    "jurisdiction": "PL",
    "external_id": "eli:DU/2001/733",
    "anchor": "art:6"
  },
  "confidence": 0.9,
  "evidence": {
    "page_index": 2,
    "char_start": 1200,
    "char_end": 1305
  },

  "ingested_at": "2026-03-01T12:00:00Z"
}


⸻

5.6. ingest_runs (прогон пайплайна)

{
  "_id": "run:01J...ULID",
  "run_id": "01J...ULID",
  "started_at": "2026-03-01T12:00:00Z",
  "finished_at": "2026-03-01T12:10:00Z",

  "config_hash": "sha256...",
  "pipeline_version": "0.1.0",

  "stats": {
    "sources_total": 38,
    "docs_ok": 30,
    "docs_restricted": 5,
    "docs_error": 3,
    "pages_written": 1234,
    "nodes_written": 5678,
    "citations_written": 120
  },

  "errors": [
    {
      "source_id": "pl_lex_art_19a",
      "stage": "fetch",
      "error_type": "AccessDenied",
      "message": "Paywall detected"
    }
  ]
}


⸻

6) Индексы MongoDB (обязательные)

Разработчик обязан создать индексы при старте (если нет) — через миграцию или bootstrap.

documents
	•	_id уникальный (по умолчанию)
	•	current_source_hash (обычный индекс)
	•	doc_type, jurisdiction, language (составной)
	•	external_ids.eli (sparse)
	•	external_ids.saos_id (sparse)

document_sources
	•	уникальный: { doc_uid: 1, source_hash: 1 }
	•	индекс: { fetched_at: -1 }

pages
	•	уникальный: { doc_uid: 1, source_hash: 1, page_index: 1 }
	•	индекс: { doc_uid: 1, source_hash: 1 }

nodes
	•	уникальный: { doc_uid: 1, source_hash: 1, node_id: 1 }
	•	индекс: { doc_uid: 1, source_hash: 1, start_index: 1 }
	•	индекс: { doc_uid: 1, source_hash: 1, anchors.article: 1 } (sparse)

citations
	•	уникальный: { doc_uid: 1, source_hash: 1, _id: 1 }
	•	индекс: { "target.external_id": 1 } (sparse)

ingest_runs
	•	_id уникальный
	•	индекс: { started_at: -1 }

⸻

7) Шаги пайплайна (детально)

7.1. CLI команды

Обязательные команды:
	1.	legal_ingest ingest --config config.yml
	2.	legal_ingest ensure-indexes --config config.yml
	3.	legal_ingest validate-config --config config.yml
	4.	legal_ingest dry-run --config config.yml --limit 5 (алиас ingest с dry_run=true)

7.2. Общий алгоритм ingest

0) Init
	•	Считать config → валидировать.
	•	Создать run_id (если auto).
	•	Создать запись ingest_runs со статусом RUNNING.
	•	Поднять Mongo клиент, проверить доступность, создать индексы.

1) Resolve sources
	•	Для каждого sources[]:
	•	определить fetch_strategy:
	•	direct → HTTP GET URL
	•	saos_judgment → вызвать SAOS API judgment by id
	•	saos_search → вызвать SAOS API search, собрать IDs, добавить в очередь как saos_judgment

SAOS API детали:
	•	Получение конкретного решения: GET https://www.saos.org.pl/api/judgments/{JUDGMENT_ID}  ￼
	•	Поиск: GET https://www.saos.org.pl/api/search/judgments с параметрами, включая keywords, courtType, all, referencedRegulation, и т.д.  ￼

2) Fetch raw
	•	Скачать документ:
	•	httpx GET, таймаут и ретраи по config.
	•	Сохранить original.bin + response_meta.json.
	•	Посчитать source_hash = sha256(bytes).
	•	Записать/обновить document_sources (upsert по doc_uid+source_hash).

3) Detect content type
	•	MIME приоритет:
	1.	Content-Type header
	2.	сигнатура файла (magic bytes)
	3.	по URL расширению
	•	Категории:
	•	PDF
	•	HTML
	•	JSON (SAOS API)
	•	другое → статус ERROR (не поддерживается)

4) Parse + normalize → pages
	•	PDF:
	1.	Попытка PyMuPDF извлечь текст по страницам.
	2.	Посчитать quality‑метрики:
	•	avg_chars_per_page
	•	empty_page_ratio
	•	alpha_ratio средний
	3.	Если качество не проходит пороги (min_avg_chars_per_page или max_empty_page_ratio) → OCR fallback:
	•	вызвать Mistral OCR 3 POST /v1/ocr  ￼
(стратегия document_url как в примерах API; поля запроса см. ниже)
	•	взять pages[].markdown и преобразовать в text (strip markdown) + сохранить markdown отдельно
	4.	Сформировать pages с page_index 0..N-1.
	•	HTML:
	1.	BeautifulSoup удалить script/style/nav/footer.
	2.	Извлечь заголовки h1-h6, абзацы, списки.
	3.	Сконвертировать в “упрощённый markdown”.
	4.	Разбить на виртуальные страницы:
	•	границы по h2+ и/или по max_tokens_per_virtual_page.
	•	SAOS JSON:
	1.	Взять:
	•	textContent (полный текст)  ￼
	•	decision (резолютивная часть)
	•	summary (если есть)
	2.	Собрать markdown:
	•	# Decision + decision
	•	# Summary + summary
	•	# Text + textContent
	3.	Разбить на виртуальные страницы.

Mistral OCR3 запрос (обязательная реализация)
	•	Endpoint: POST https://api.mistral.ai/v1/ocr  ￼
	•	Минимальный JSON:

{
  "model": "mistral-ocr-2512",
  "document": {
    "documentUrl": "https://...pdf",
    "type": "document_url"
  },
  "table_format": "markdown",
  "include_image_base64": false
}

Поля и пример структуры ответа с pages[].markdown/images/dimensions есть в документации OCR endpoint.  ￼

5) Extract document-level metadata
Минимум:
	•	title:
	•	PDF: попытка взять первые 1–2 страницы и regex по шаблонам (PL: “Ustawa z dnia …”, “Kodeks …”, “WYROK”, “UCHWAŁA”).
	•	HTML: title тэг + h1.
	•	SAOS: можно сформировать title = "{judgmentType} {caseNumber} ({court})" если доступно в JSON.  ￼
	•	date_published/date_decision:
	•	SAOS: judgmentDate.  ￼
	•	PDF/HTML: regex/heuristics (опционально).
	•	external_ids: как минимум те, что в config + извлечённые.

6) Build PageIndex-style tree → nodes
Обязательный минимум:
	•	Узел root покрывающий весь документ [0, page_count).

Дальше — по типу:

6.1 STATUTE / EU_ACT (законы/директивы)
Цель: узлы chapter + article.
	•	Детект chapter:
	•	PL: ^(Rozdział|ROZDZIAŁ)\s+...
	•	EN: ^CHAPTER\s+... (если есть)
	•	Детект article:
	•	PL: ^Art\.\s+\d+[a-z]?\b
	•	EN: ^Article\s+\d+\b

Алгоритм:
	1.	Пройти все pages[i].text.
	2.	Найти позиции начала глав/статей → map {article_id -> first_page_index}.
	3.	Отсортировать по странице.
	4.	Для каждой статьи:
	•	start_index = first_page
	•	end_index = next_first_page или page_count
	5.	Создать nodes:
	•	node_id: art:{номер} (стабильно)
	•	anchors.article: {номер}
	6.	Если главы найдены:
	•	node_id: ch:{номер}
	•	дети: статьи, попадающие по диапазону страниц.

6.2 CASELAW (судебные решения)
Цель: узлы крупных секций (минимум).

Детект по маркерам (PL):
	•	WYROK, UCHWAŁA, POSTANOWIENIE
	•	UZASADNIENIE
	•	SENTENCJA (если встречается)

Алгоритм:
	1.	По pages[i].text искать начало секций (regex).
	2.	Разбить диапазоны аналогично статьям.
	3.	Узлы:
	•	node_id: sec:uzasadnienie, sec:wyrok и т.п.
	•	title: человеко‑читаемо.

6.3 HTML (прочие)
	•	Построение дерева по заголовкам:
	•	h1 → depth 1
	•	h2 → depth 2 и т.д.
	•	Диапазоны страниц:
	•	каждый heading покрывает виртуальные страницы до следующего heading того же/меньшего уровня.

7) Citations extraction
MVP:
	•	Для SAOS:
	•	взять referencedRegulations[] из API и сохранить как citations.  ￼
	•	raw_citation_text = referencedRegulations[i].text
	•	если journalYear/journalEntry есть → сохранить в target как структурированное.
	•	Для остальных:
	•	можно пропустить (пусто), но структура и коллекция должны быть.

8) Persist to Mongo (idempotent)
Порядок записи (важен):
	1.	document_sources (фиксируем сырьё)
	2.	pages
	3.	nodes
	4.	citations
	5.	documents (обновить current_source_hash, page_count, pageindex_tree snapshot)

Все операции — bulk upsert (batch размер configurable, напр. 200).

9) Run finalization
	•	Обновить ingest_runs:
	•	finished_at
	•	stats
	•	errors
	•	Сформировать run_report.json в artifacts.

⸻

8) Логирование и наблюдаемость

8.1 Формат логов
	•	JSON lines в stdout + дублирование в artifacts/runs/{run_id}/logs.jsonl
	•	Каждая запись обязана содержать:
	•	ts, level, run_id, source_id, doc_uid, stage, msg
	•	duration_ms (для stage завершений)
	•	metrics (chars/pages/nodes/etc)

Пример:

{"ts":"2026-03-01T12:00:02Z","level":"INFO","run_id":"01J...","source_id":"pl_eli_du_2001_733","doc_uid":"eli_pl:DU/2001/733","stage":"parse_pdf","msg":"parsed via PDF_TEXT","duration_ms":812,"metrics":{"page_count":15,"avg_chars_per_page":1800}}

8.2 Обработка ошибок
	•	Ошибка на одном документе не останавливает весь run.
	•	Все ошибки фиксируются в:
	•	логах
	•	ingest_runs.errors[]
	•	documents.access_status="ERROR" или "RESTRICTED"

Paywall/Restricted detection (обязательно)
	•	Если HTML содержит явные маркеры ограниченного доступа (например “Zaloguj”, “Abonament”, “Kup dostęp”) или мало текста (ниже порога) — присвоить access_status="RESTRICTED", license_tag="COMMERCIAL" и:
	•	сохранить raw HTML snapshot
	•	в pages сохранять только то, что реально доступно (обычно заголовок/анонс)
	•	не падать.

⸻

9) Тестовый прогон

9.1. Инфраструктура для теста
	•	docker-compose.yml с MongoDB:
	•	порт 27017
	•	volume для данных
	•	make test-ingest (или аналог) запускает:
	1.	ensure-indexes
	2.	ingest --config config.yml --limit N (если реализован limit)
	3.	проверки count’ов в Mongo

9.2. Минимальный тестовый набор (обязательный)

Для стабильного CI теста использовать подмножество (5–8 источников), включающее:
	•	1 PDF закон (ELI или ISAP)
	•	1 PDF SN
	•	1 HTML EUR‑Lex
	•	1 SAOS judgment по API (ID)
	•	1 “restricted” источник (LEX) — чтобы проверить мягкую деградацию

⸻

10) Критерии приёмки (Acceptance Criteria)

Решение считается принятым, если выполняется всё ниже:

A. Функциональные критерии
	1.	Пайплайн обрабатывает все источники из config.yml:
	•	для доступных: documents.access_status="OK"
	•	для недоступных/ограниченных: "RESTRICTED" без падения
	2.	Для каждого documents.access_status="OK":
	•	есть минимум 1 запись в pages
	•	есть минимум 1 запись в nodes (root)
	•	documents.page_count == count(pages) для PDF
	3.	Для документов типа STATUTE/EU_ACT:
	•	дерево содержит узлы статей (node_id вида art:*) если текст позволяет (в противном случае OCR fallback должен был сработать)
	4.	Для SAOS saos_judgment:
	•	метаданные берутся из API
	•	citations заполнены из referencedRegulations (если они есть у решения)  ￼

B. Идемпотентность
	5.	Два запуска подряд на одном и том же config.yml:
	•	не увеличивают количество документов/страниц/узлов (кроме ingest_runs)
	•	documents.current_source_hash не меняется
	6.	Если raw контент изменился (искусственно подменить файл/HTML в тесте):
	•	создаётся новый document_sources с новым source_hash
	•	documents.current_source_hash обновляется
	•	pages/nodes появляются для нового source_hash, старые остаются

C. Качество инженерии
	7.	Есть bootstrap индексов (команда ensure-indexes).
	8.	Логи структурированные JSON, есть run_report.json.
	9.	Тесты:
	•	unit: минимум URL→doc_uid, PDF quality→OCR decision, tree builder ranges
	•	integration: прогон на test Mongo (docker) с проверками

⸻

11) Требования к стеку реализации

Язык и библиотеки
	•	Python 3.11+
	•	Обязательные зависимости:
	•	httpx
	•	pydantic
	•	pymongo
	•	pymupdf (fitz)
	•	beautifulsoup4 + lxml
	•	pyyaml
	•	tenacity (или собственный retry)
	•	OCR (опционально, но по ТЗ включено):
	•	либо прямой REST вызов /v1/ocr (рекомендуется),
	•	либо SDK mistralai (если удобно); endpoint и поля запроса фиксированы документацией.  ￼

Безопасность
	•	API ключ Mistral читается только из env var MISTRAL_API_KEY (имя задаётся в config).
	•	В логи нельзя писать ключи/токены/куки.

⸻

12) Примечания по совместимости с PageIndex-подходом
	•	nodes.start_index/end_index должны быть page-based диапазонами и использовать end-exclusive семантику, чтобы узлы “стыковались” без перекрытий (как в примере PageIndex).  ￼
	•	documents.pageindex_tree хранится как nested JSON, пригодный для подачи в LLM tree-search.

⸻

