По описанию, текущее хранилище уже достаточно хорошее как source of truth для legal RAG: у вас есть логический каталог документов, история source-version, page/node-слой, зачаток citation-graph и хороший provenance через current_source_hash + raw_object_path. Узкое место не в самих данных, а в том, что GPT нельзя пускать напрямую в MongoDB и файловую систему. Для production-агента нужен тонкий read-only retrieval layer, который делает 4 вещи: ищет, выбирает точные фрагменты, нормализует ссылки и отдает стабильный provenance.

Для этой задачи я бы не строил swarm из множества “умных” агентов. Практичнее и устойчивее первая версия как 1 orchestration-agent на GPT-5.4 + 1 read-only tool legal_corpus + optional verifier pass. На вашем объеме корпуса это даст почти весь эффект без лишней операционной сложности.

1. Системная инструкция агента

Ниже готовый system prompt, который можно вставлять почти без правок.

Ты — Legal Deposit Dispute Agent, специализированный аналитический агент по спорам о невозврате кауции / арендного депозита.

Твоя задача:
1) разобрать описание кейса и пользовательские документы;
2) установить подтвержденные факты и спорные обстоятельства;
3) через внутренний инструмент legal_corpus найти применимые нормы и релевантную судебную практику;
4) выдать обоснованный вывод, где каждый существенный тезис опирается на:
   - пользовательские доказательства,
   - и/или найденные юридические источники.

Ты не адвокат и не суд. Ты даешь аналитическое заключение и практический план действий. Не изображай юридическое представительство и не выдавай вероятностный вывод за установленный факт.

Источники, на которые можно опираться:
- текстовое описание пользователя;
- извлеченный текст и метаданные пользовательских документов;
- только те материалы внутренней юридической базы, которые получены через tool `legal_corpus`.

Запрещено:
- выдумывать факты, суммы, даты, статьи, номера дел, сроки, цитаты и выводы суда;
- ссылаться на закон или судебную практику, если нет точного подтвержденного фрагмента;
- называть редакцию нормы действующей, если не проверена версия на релевантную дату;
- смешивать подтвержденные факты, вероятные выводы и предположения;
- опираться на внешние источники, если они не были явно предоставлены системой.

Общий принцип:
Для каждого ключевого вывода строй цепочку:
ФАКТ -> ДОКАЗАТЕЛЬСТВО -> НОРМА / ПРАКТИКА -> ВЫВОД -> УРОВЕНЬ УВЕРЕННОСТИ.

Рабочий порядок:

Шаг 1. Разбор пользовательских материалов.
- Классифицируй каждый пользовательский документ: договор аренды, приложение, акт приема-передачи, переписка, платежное подтверждение, квитанция, фото/осмотр, претензия, ответ собственника, судебный документ, иное.
- Извлеки и нормализуй:
  - сумму кауции / депозита;
  - валюту;
  - дату и способ оплаты;
  - срок аренды;
  - дату въезда и выезда;
  - условия договора о кауции;
  - условия о зачете, удержании, ремонте, коммунальных платежах;
  - наличие и содержание акта приема-передачи;
  - состояние помещения при въезде и при выезде;
  - основания удержания, заявленные собственником;
  - подтвержденные задолженности по аренде / коммунальным;
  - подтвержденные повреждения и расходы на их устранение;
  - дату требования о возврате и дату отказа / частичного возврата.
- Если документы противоречат друг другу, покажи обе версии с источниками.
- Если извлечение неполное, продолжай анализ, но явно отмечай пробелы.

Шаг 2. Сбор фактической матрицы.
Собери краткую timeline-матрицу:
- дата / период;
- событие;
- кто утверждает;
- подтверждающий документ;
- степень подтверждения: высокая / средняя / низкая.

Отдельно собери таблицу спорных сумм:
- сумма кауции;
- что уже возвращено;
- что удержано;
- на каком основании удержано;
- чем подтверждено удержание;
- что подтверждено документально, а что только заявлено.

Шаг 3. Формирование юридических вопросов.
Для каждого кейса проверь минимум такие вопросы:
1. Подтверждено ли внесение кауции?
2. Что именно по договору допускает удержание кауции?
3. Есть ли императивные нормы, которые ограничивают договорные условия?
4. Доказаны ли повреждения сверх обычного износа?
5. Доказаны ли долги по аренде / коммунальным платежам?
6. Подтверждены ли расходы собственника документами?
7. Должна ли была быть возвращена хотя бы неоспариваемая часть кауции?
8. Имеются ли процессуально или доказательственно слабые места у позиции собственника?
9. Какая судебная практика помогает или мешает позиции пользователя?

Шаг 4. Определи релевантную дату для версии права.
- Обычно это дата окончания аренды, передачи помещения, удержания кауции, отказа в возврате или иная юридически значимая дата из кейса.
- Если право могло измениться в ходе отношений, учитывай историческую редакцию, релевантную спору.
- Если нельзя надежно определить нужную редакцию, прямо так и скажи.

Шаг 5. Работа с internal tool `legal_corpus`.
Используй tool только после первичного fact extraction.
Правила поиска:
- По умолчанию ищи только operational records и текущие источники.
- Игнорируй alias / excluded / broken записи, если система явно не просит audit/traceability режим.
- Для нормативных актов сначала ищи article-level фрагменты, затем при необходимости добирай соседний контекст.
- Для судебной практики сначала ищи фрагменты с holding / facts / related provisions, затем дочитывай контекст.
- Начинай с норм, затем подбирай судебную практику, затем при необходимости делай one-hop expansion по citations.
- Дедуплицируй выдачу по canonical_doc_uid, duplicate_owner_doc_uid и same_case_group_id.
- Не цитируй preview/snippet из поиска как окончательную цитату: перед финальным выводом получи точный фрагмент через `legal_corpus.fetch_fragments`.
- Если язык пользовательского кейса не совпадает с языком корпуса, формируй внутренние поисковые запросы на обоих языках, используя термины из договора и устойчивые юридические формулировки корпуса.

Приоритет источников:
1. условия договора пользователя;
2. применимые нормы закона в релевантной редакции;
3. судебная практика;
4. вторичные связанные источники, найденные через citation expansion.

При использовании судебной практики:
- не ограничивайся совпадением слов;
- кратко объясняй, почему фактическая ситуация похожа или чем она отличается;
- не выдавай одно решение за универсальное правило.

Шаг 6. Построение анализа.
По каждому ключевому вопросу:
- сформулируй факт;
- укажи, чем он подтвержден;
- укажи норму(ы) и/или практику;
- объясни, как норма применяется к установленным фактам;
- отметь уровень уверенности вывода;
- при нехватке данных дай условный вывод вида:
  “если подтвердится X, то вероятен вывод Y; если нет, позиция ослабевает”.

Шаг 7. Формат ответа пользователю.
Всегда отвечай в следующей структуре:

1. Краткий вывод
   - 3–6 предложений;
   - что выглядит сильным в позиции пользователя;
   - что выглядит слабым;
   - есть ли реальный шанс требовать полный или частичный возврат.

2. Что подтверждено документами
   - только установленные факты;
   - с короткими ссылками на пользовательские документы.

3. Что спорно или не доказано
   - противоречия;
   - недостающие документы;
   - сомнительные основания удержания.

4. Применимые нормы и практика
   - перечисли только действительно релевантные нормы и судебные решения;
   - укажи кратко, за что именно каждая норма / практика отвечает.

5. Анализ по вопросам
   - удержание за повреждения;
   - удержание за коммунальные / долги;
   - срок и объем возврата;
   - бремя доказывания;
   - иные вопросы, если релевантны.

6. Что делать дальше
   - какие документы срочно запросить / приложить;
   - какие аргументы использовать;
   - где позиция пользователя наиболее уязвима;
   - что можно требовать уже сейчас.

7. Источники
   - отдельным блоком перечисли использованные пользовательские документы и юридические источники.

Правила цитирования:
- Пользовательские документы цитируй в формате:
  [Документ пользователя: <название/тип>, <страница/фрагмент/дата при наличии>]
- Нормы цитируй в формате:
  [Норма: <краткое название акта>, <структурный локатор статьи/параграфа/пункта>]
- Судебную практику цитируй в формате:
  [Практика: <суд>, <дата>, № <номер дела/сигнатура>]
- Не вставляй длинные цитаты. Достаточно короткого точного фрагмента и краткого пояснения.
- В пользовательском тексте используй человекочитаемые ссылки. Внутренние machine refs допустимы только в служебной metadata, если система это поддерживает.

Обязательная внутренняя самопроверка перед финализацией:
- у каждого ключевого вывода есть опора хотя бы на один факт и один источник;
- нет неподтвержденных сумм и дат;
- не использована устаревшая редакция без пометки;
- нет дублирующихся authority без добавочной ценности;
- отделены факты, правовые выводы и предположения;
- если правовая база не нашла надежной опоры, это явно сказано.

2. ТЗ на инструмент доступа к юридической базе

2.1. Назначение

Нужен read-only сервис legal_corpus, который стоит между GPT-5.4 и текущими MongoDB/FS-данными.

Ключевой принцип: модель не должна иметь произвольный доступ ни к Mongo query language, ни к файловой системе. Только к жестко ограниченному API, который возвращает уже нормализованные, безопасные и пригодные для цитирования результаты.

2.2. Архитектурное правило

MongoDB — основной источник для поиска и чтения нормализованного текста.
FS — слой provenance / replay / raw artifact access, но не источник для основного retrieval-пути.

Причина простая: у вас сейчас нормализованные файловые выгрузки есть только для части корпуса, а storage_uri неоднороден. Поэтому retrieval не должен зависеть от конкретного layout на диске.

2.3. Интерфейс инструмента

Я бы задал программисту такой контракт.

from typing import Literal, TypedDict, NotRequired, Sequence


class SearchRequest(TypedDict):
    query: str
    query_language: NotRequired[str]
    query_expansions: NotRequired[list[str]]
    scope: Literal["acts", "case_law", "mixed"]
    return_level: Literal["document", "fragment", "mixed"]
    as_of_date: NotRequired[str]          # YYYY-MM-DD
    include_history: NotRequired[bool]
    expand_citations: NotRequired[bool]
    top_k: NotRequired[int]
    locator: NotRequired[dict]            # act_id/article or case_signature etc.
    filters: NotRequired[dict]


class FetchFragmentsRequest(TypedDict):
    refs: list[dict]                      # stable machine refs from search
    include_neighbors: NotRequired[bool]
    neighbor_window: NotRequired[int]
    max_chars_per_fragment: NotRequired[int]


class ExpandRelatedRequest(TypedDict):
    refs: list[dict]
    relation_types: list[
        Literal["cites", "cited_by", "same_case", "supersedes", "related_provision"]
    ]
    top_k: NotRequired[int]


class ProvenanceRequest(TypedDict):
    ref: dict                             # machine ref
    include_artifacts: NotRequired[bool]
    debug: NotRequired[bool]


class LegalCorpusTool:
    def search(self, request: SearchRequest) -> dict: ...
    def fetch_fragments(self, request: FetchFragmentsRequest) -> dict: ...
    def expand_related(self, request: ExpandRelatedRequest) -> dict: ...
    def get_provenance(self, request: ProvenanceRequest) -> dict: ...

2.4. Что должен делать каждый метод

search
Назначение: вернуть ранжированные кандидаты, а не сразу финальные цитаты.

Должен уметь:
	•	искать по актам, судебной практике или по смешанному корпусу;
	•	принимать as_of_date, чтобы не путать текущую и историческую редакции;
	•	учитывать issue_tags, facts_tags, court_level, judgment_date, related_provisions, act_id, status, legal_role, document_kind;
	•	принимать query_expansions для двуязычного/синонимического поиска;
	•	по умолчанию работать только по operational slice;
	•	по умолчанию использовать documents.current_source_hash;
	•	по опции expand_citations=true делать только one-hop expansion, не больше.

Что возвращает:
	•	results[] с коротким preview;
	•	machine_ref на документ/фрагмент;
	•	display_citation;
	•	score и score_breakdown;
	•	why_relevant;
	•	основные metadata для rerank и UI.

Важно: search не должен отдавать сырые Mongo _id как стабильные идентификаторы. Нужен машинный реф вида:

{
  "doc_uid": "doc:...",
  "source_hash": "sha256:...",
  "unit_id": "unit:...",
  "node_id": "art:12",
  "page_range": [4, 5]
}

fetch_fragments
Назначение: по выбранным machine_ref вернуть точный фрагмент для цитирования.

Должен:
	•	возвращать точный текст фрагмента;
	•	возвращать title_path, page_start/page_end, locator, source_hash, doc_uid;
	•	при include_neighbors=true отдавать соседний контекст;
	•	уметь fallback-ить на Mongo, если файловый normalized artifact отсутствует;
	•	возвращать quote_checksum, чтобы фронт/бэкенд могли проверять, не устарел ли cached fragment.

expand_related
Назначение: из найденного документа или фрагмента показать связанные authority.

Должен уметь:
	•	идти по citations;
	•	использовать mapping external_id -> doc_uid;
	•	расширять по same_case_group_id, canonical_doc_uid, superseded_by и citation-relations;
	•	по умолчанию отдавать только ближайшие и объяснимые связи.

get_provenance
Назначение: дать стабильный traceability-слой для человека и для отладки.

Должен возвращать:
	•	doc_uid, source_hash;
	•	source_url, final_url, normalized_source_url;
	•	raw_object_path или нормализованный артефактный URI;
	•	license_tag;
	•	информацию о текущей/исторической версии;
	•	признак целостности артефактов.

Это нужно не для LLM-рассуждений, а для UI, аудита и воспроизводимости.

2.5. Логика поиска

Инструмент должен искать не “по коллекциям”, а по нормализованным retrieval units.

Минимальный поисковый pipeline:
	1.	Candidate generation
	•	фильтрация по documents;
	•	поиск по материализованным fragment units;
	•	отдельный recall для актов и для case law.
	2.	Hybrid scoring
	•	lexical/BM25;
	•	vector similarity;
	•	metadata priors:
	•	issue_tags, facts_tags, related_provisions;
	•	holding_1line, summary_1line, key_provisions;
	•	court_level, judgment_date, relevance_score;
	•	source_tier, status, current_status.
	3.	Demotion / filtering
	•	alias, excluded, broken inventory;
	•	low-quality extraction;
	•	negative search terms;
	•	дубли в одном same_case_group_id.
	4.	Dedup
	•	по canonical_doc_uid;
	•	по duplicate_owner_doc_uid;
	•	по same_case_group_id.
	5.	Optional graph expansion
	•	только one-hop;
	•	только после основного recall;
	•	только если исходный кандидат уже релевантен.

2.6. Что должно возвращаться агенту для ответа пользователю

Каждый результат должен содержать 2 слоя данных.

User-facing слой
	•	display_citation
	•	короткий preview
	•	source_label
	•	document_kind
	•	court_name / act_short_name
	•	judgment_date / version_date
	•	deep_link в UI

Machine-facing слой
	•	machine_ref
	•	doc_uid
	•	source_hash
	•	canonical_doc_uid
	•	node_id / unit_id
	•	page_range
	•	score
	•	score_breakdown
	•	matched_fields
	•	provenance_status

Агенту этого достаточно, чтобы:
	•	выбрать кандидатов;
	•	добрать точные фрагменты через fetch_fragments;
	•	сослаться на источник без галлюцинаций;
	•	показать пользователю человекочитаемую цитату и clickable source.

2.7. Нефункциональные требования
	1.	Read-only. Ни обновлений, ни удаления, ни raw query passthrough.
	2.	Стабильные идентификаторы. Не завязываться на layout файловой системы.
	3.	Полный audit trail:
	•	request_id;
	•	tool_call_id;
	•	query hash;
	•	returned refs;
	•	latency;
	•	warnings.
	4.	Детерминированная сортировка при равных score.
	5.	Graceful degradation:
	•	если normalized artifacts нет на диске, читать из Mongo;
	•	если citation не разрешился, возвращать unresolved с reason.
	6.	Token-aware response:
	•	previews короткие;
	•	full text только через fetch_fragments.
	7.	Index freshness control:
	•	retrieval/index layer должен знать, на каком ingest_run он построен;
	•	при рассинхроне с последним успешным ingest_run — warning в diagnostics.

2.8. Приемочные критерии

Разработку можно считать принятой, когда выполняются такие проверки:
	1.	По запросу вроде
невозврат кауции, удержание за повреждения и коммунальные после выезда
сервис возвращает:
	•	минимум 1–2 релевантных нормативных фрагмента;
	•	минимум 1–3 релевантных case-law кандидата;
	•	без дублей по same_case_group_id.
	2.	При current_only=true сервис использует documents.current_source_hash.
	3.	При as_of_date=<date> сервис может:
	•	вернуть исторически релевантную версию;
	•	либо явно сообщить, что историческая версия не найдена.
	4.	fetch_fragments возвращает точный текст и локатор, пригодный для пользовательской цитаты.
	5.	expand_related умеет разворачивать ссылки через external_id -> doc_uid, а не только по raw citation text.
	6.	Broken/synthetic paths не попадают в operational search.
	7.	В ответе всегда есть достаточно metadata, чтобы:
	•	показать ссылку пользователю,
	•	воспроизвести разбор,
	•	открыть исходный raw artifact человеку.

2.9. Практическая реализация без лишнего overengineering

На текущем объеме корпуса я бы дал программисту такой ориентир:
	•	не переписывать ingestion;
	•	поверх текущего Mongo сделать materialized retrieval layer;
	•	индекс перестраивать целиком после каждого успешного ingest_run — на 931 документах это нормально;
	•	API сделать backend-agnostic, но source of truth оставить за Mongo;
	•	отдельный vector/lexical backend допустим, но контракт инструмента важнее, чем конкретный движок.

3. Требования к доработке хранилища

Главный тезис: переписывать текущую схему целиком не нужно. Она уже хороша как truth/provenance-слой. Но для агентной системы нужен derived operational layer и несколько обязательных полей, которых сейчас не хватает.

3.1. Что уже хорошо

Сильные стороны текущей схемы:
	•	documents уже играет роль каталога и фильтрующего слоя;
	•	document_sources уже хранит версионность и provenance;
	•	pages и nodes дают текст + структуру;
	•	citations уже дают зацепку для графа ссылок;
	•	current_source_hash + raw_object_path уже позволяют делать replay.

Это хорошая база. Перестраивать нужно не основу, а слой доступа и materialized search representation.

3.2. P0 — обязательно до rollout агента

1. Нормализованный retrieval_units
Сейчас GPT будет слишком дорого и хрупко собирать контекст из documents + pages + nodes на лету. Нужна materialized коллекция, где каждая запись — уже цитируемый фрагмент.

Новая коллекция: retrieval_units

Минимальные поля:
	•	unit_id
	•	doc_uid
	•	source_hash
	•	canonical_doc_uid
	•	document_kind
	•	legal_role
	•	unit_type (article, section, page_chunk, holding, facts, reasoning)
	•	node_id
	•	title
	•	title_path
	•	text
	•	text_norm
	•	page_start
	•	page_end
	•	locator
	•	issue_tags
	•	facts_tags
	•	related_provisions
	•	court_level
	•	judgment_date
	•	current_status
	•	operational_status
	•	is_indexable
	•	display_citation
	•	authority_weight
	•	effective_from
	•	effective_to
	•	embedding_ref или embedding_vector (если вектор хранится рядом)

Зачем это нужно:
	•	единый fragment layer для актов и case law;
	•	быстрый hybrid retrieval;
	•	точные цитаты без runtime-сборки из нескольких коллекций;
	•	простое дедуплирование и rerank.

2. Разрешение citation-target
Сейчас citations хранят target.external_id, но не target_doc_uid. Для agentic retrieval это слишком косвенно.

Минимум:
	•	backfill поля citations.target_doc_uid
	•	backfill citations.target_canonical_doc_uid

Более аккуратный вариант:
	•	оставить citations как raw extraction;
	•	добавить отдельную коллекцию citation_resolutions.

citation_resolutions:
	•	citation_uid
	•	from_doc_uid
	•	from_source_hash
	•	from_node_id
	•	target_external_id
	•	target_doc_uid
	•	target_canonical_doc_uid
	•	target_node_id (если можно разрешить до нормы/статьи)
	•	resolver_version
	•	resolution_status (resolved, ambiguous, unresolved)
	•	confidence
	•	resolved_at

Это снимет один из самых дорогих runtime-hop’ов.

3. Версионность “на дату”
Для юридического анализа мало знать “текущий источник”. Нужна применимость нормы на дату спора.

Добавить в documents и/или document_sources:
	•	jurisdiction
	•	language
	•	publication_date
	•	effective_from
	•	effective_to
	•	version_date
	•	is_current_source
	•	version_kind (current, historical, consolidated, official)

Особенно важно для актов:
	•	агент не должен путать current consolidated text с редакцией, действовавшей на дату спора.

4. Нормализация storage layer
Сейчас storage_uri гетерогенен и нельзя рассчитывать на один корень. Это надо formalize, а не лечить условными os.path.join.

Добавить в document_sources:
	•	storage_backend (file, s3, gcs, unknown)
	•	storage_uri_normalized
	•	artifact_manifest
	•	integrity_status

artifact_manifest должен содержать:
	•	raw_bin_uri
	•	response_meta_uri
	•	normalized_pages_uri
	•	normalized_nodes_uri
	•	availability_flags

Именно artifact_manifest, а не исходный storage_uri, должен стать источником правды для provenance/UI.

5. Явное разделение operational vs traceability
Сейчас это описано концептуально, но агенту лучше не оставлять свободу трактовок по status.

Добавить в documents и retrieval_units:
	•	operational_status (operational, traceability, excluded, broken, alias)
	•	is_indexable: bool

Правило:
	•	в agentic retrieval по умолчанию участвует только is_indexable=true и operational_status="operational".

3.3. P1 — очень желательно в первой итерации

documents
Добавить:
	•	jurisdiction
	•	language
	•	operational_status
	•	is_indexable
	•	authority_weight
	•	display_citation
	•	publication_date
	•	effective_from
	•	effective_to
	•	version_date

Уточнить:
	•	issue_tags и facts_tags должны стать контролируемым словарем, а не свободным текстом.

Индексы:
	•	unique: doc_uid
	•	compound: (document_kind, operational_status, is_indexable)
	•	separate multikey: issue_tags
	•	separate multikey: facts_tags
	•	compound: (canonical_doc_uid)
	•	compound: (same_case_group_id)
	•	acts: (act_id, effective_from, effective_to)
	•	case law: (court_level, judgment_date)
	•	sparse/registry-based mapping для external_id

document_sources
Добавить:
	•	storage_backend
	•	storage_uri_normalized
	•	artifact_manifest
	•	integrity_status
	•	is_current_source
	•	effective_from
	•	effective_to
	•	version_date

Индексы:
	•	unique: (doc_uid, source_hash)
	•	compound: (doc_uid, is_current_source)
	•	compound: (integrity_status)
	•	compound: (storage_uri_normalized)

nodes
По вашему описанию nodes выглядят больше как structural boundaries, чем как полноценные quoteable chunks. Для agentic retrieval этого мало.

Сделать обязательными или материализовать:
	•	text
	•	text_norm
	•	title_path
	•	page_start
	•	page_end
	•	locator
	•	semantic_role (article, definition, holding, facts, reasoning, disposition)
	•	display_citation

Индексы:
	•	unique: (doc_uid, source_hash, node_id)
	•	compound: (doc_uid, source_hash, semantic_role)
	•	compound: (doc_uid, source_hash, page_start, page_end)

Если вы не хотите расширять nodes, этот смысл должен жить в retrieval_units. Но где-то это materialize-ить нужно обязательно.

pages
Сейчас markdown = null везде — для retrieval это не фатально, но для качества UI и цитирования слабовато.

Полезно добавить:
	•	rendered_markdown
	•	block_spans
	•	ocr_confidence / text_quality_score

Так агент и UI смогут точнее ссылаться на фрагменты, особенно в PDF.

citations
Либо backfill прямых target-полей, либо ввести citation_resolutions.

Индексы:
	•	(from_doc_uid, from_node_id)
	•	(target_external_id)
	•	(target_doc_uid)
	•	(target_canonical_doc_uid)

3.4. P1 — отдельный case workspace для пользовательских документов

Это не часть текущего справочного корпуса, но для реальной агентной системы необходимо.

Не смешивать пользовательские документы со справочной базой documents/pages/nodes.

Нужны отдельные коллекции, хотя бы:
	•	case_workspaces
	•	case_documents
	•	case_facts
	•	case_authority_links
	•	analysis_runs

Минимум по case_workspaces:
	•	case_id
	•	created_at
	•	jurisdiction
	•	claim_type (deposit_return)
	•	claim_amount
	•	currency
	•	lease_start
	•	lease_end
	•	move_out_date
	•	deposit_return_due_date
	•	status

Минимум по case_facts:
	•	fact_id
	•	case_id
	•	fact_type
	•	value
	•	confidence
	•	source_doc_refs
	•	extracted_at
	•	verified_by_user

Это снимет соблазн складывать пользовательские файлы в authoritative corpus и сильно упростит traceability.

3.5. P2 — улучшения, которые дадут запас на рост
	1.	authority_registry
	•	единое разрешение external_id, alias IDs, source-system collisions;
	•	особенно полезно, если корпус будет расширяться.
	2.	authority_edges
	•	обобщенный граф cites, interprets, supersedes, same_case, duplicate_of;
	•	удобно для graph-based expansion и explainability.
	3.	index_runs
	•	отдельная фиксация того, на каком ingest_run построен retrieval index;
	•	помогает диагностировать рассинхрон.
	4.	Языконезависимые tag IDs
	•	полезно, если пользователь пишет на русском, а корпус — на польском;
	•	issue_tags лучше делать не в виде “слов”, а в виде stable IDs.

Что бы я внедрял в первую очередь

Порядок, который даст максимум эффекта при минимуме риска:
	1.	retrieval_units
	2.	citation_resolutions или хотя бы target_doc_uid
	3.	legal_corpus.search + fetch_fragments + expand_related + get_provenance
	4.	operational_status/is_indexable
	5.	effective_from/effective_to/version_date
	6.	отдельный case_workspace

Для MVP обязательны ровно эти шесть вещей. Без них агент будет не анализировать право, а тратить большую часть контекста на хрупкую сборку источников и начнет ошибаться именно на стыках схемы.