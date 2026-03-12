

1. Цель работ

Привести MongoDB-базу и генерируемое оглавление к состоянию, в котором агент на базе GPT‑5.2 быстро и стабильно находит:
	•	прямые нормы Польши по кауции в найме жилого помещения;
	•	сильные решения SN / TK / CJEU / UOKiK;
	•	релевантную фактическую практику по спорам lokator vs właściciel mieszkania;
	•	только те дополнительные EU/consumer/process материалы, которые реально нужны по запросу пользователя.

Источник истины — MongoDB legal_rag_runtime. Работы вести по коллекциям documents, pages, nodes, citations, document_sources, ingest_runs. Markdown-оглавление больше не вести вручную: оно должно генерироваться из БД.  ￼

2. Обязательное решение по списку 1–38

2.1. Обязательно включить в core-runtime или, если уже есть, привести к каноническому виду
По позициям 1–5:

В core-runtime обязаны быть официальный действующий текст Ustawa o ochronie praw lokatorów... и действующий Kodeks cywilny. Позицию 1 хранить не как главный runtime-PDF 2001 года, а как архивную исходную редакцию; главным источником сделать актуальный text jednolity / codified text того же акта. Это обязательно, потому что именно art. 6 прямо регулирует кaucja: допускает требование кауции, ограничивает её максимумом 12-кратного месячного czynsz и требует возврата в течение месяца после opróżnienie lokalu с удержанием należności wynajmującego. Для Kodeks cywilny обязательно создать nodes минимум по art. 6 и art. 118. Позиции 3, 4 и 5 из LEX не добавлять как самостоятельные документы: их нужно разложить как secondary_source и article_node under official acts. art. 19a должен стать article-node блока najem okazjonalny, а art. 118 — article-node блока przedawnienie.  ￼  ￼

По позициям 6, 13, 23, 24:

Это верхний слой польской authority-line по старым жилищным кауциям и waloryzacja. Обязательно держать как LEADING_CASE:
	•	6 — SN III CZP 58/02;
	•	13 — TK K 33/99;
	•	содержание дел 23 (III Ca 1707/18) и 24 (V ACa 599/14).

При этом сами портальные URL 23 и 24 не должны жить отдельными top-level документами: их нужно привязать к одному same_case_group_id с канонической записью соответствующего дела и показывать в оглавлении как один case-card. SN III CZP 58/02 прямо подтверждает, что art. 36 старого закона не исключал применения art. 358¹ § 3 KC к waloryzacja старых кауций; TK K 33/99 и позднейшая appellate line составляют ту же опорную цепочку.  ￼  ￼  ￼

По позициям 12, 14, 16, 17, 20:

Это core factual layer по невозврату кауции, и эти дела должны быть в high-priority runtime:
	•	12 / 171957 — спор о том, была ли сумма реальной кауцией;
	•	14 / 279345 — допустимые удержания из кауции по art. 6;
	•	16 / 346698 — конкретные удержания по ремонту и media;
	•	17 / 472812 — возврат и waloryzacja старой муниципальной кауции;
	•	20 / 505310 — najem okazjonalny и недопустимость перекладывать на нанимателя полное перекрашивание квартиры как обычный износ.  ￼

По позициям 25, 27, 31, 33, 35, 36:

Это обязательный EU_CONSUMER_LAYER:
	•	25 — official Directive 93/13/EEC;
	•	27 — Commission Notice — Guidance on the interpretation and application of Directive 93/13/EEC;
	•	31 — C-488/11 Asbeek Brusse and Katarina de Man Garabito, прямое решение по residential tenancy;
	•	33 — C-243/08 Pannon GSM, ключевой authority по ex officio review of unfair terms;
	•	35 — UOKiK RKR-37/2013 (Novis MSK), потому что дело затрагивает abusive lease clauses, включая проблематику forfeiture of deposit;
	•	36 — страница UOKiK Niedozwolone klauzule как guidance/navigation.  ￼  ￼

2.2. Хранить, но не как отдельные самостоятельные core-документы
Позиции 3, 4, 5, 22, 23, 24, 26 не должны появляться в runtime как независимые top-level documents. Их роль:
	•	secondary_source;
	•	article_node;
	•	alias;
	•	portal_mirror;
	•	same_case_group_member.

Для 22, 23 и 24 это означает: содержание дела можно использовать, но в поиске и в оглавлении должен фигурировать один канонический case-card на дело. Для 26 это означает: LexUriServ — legacy mirror, дублирующий official Directive 93/13, уже присутствующую в корпусе.  ￼  ￼  ￼  ￼

2.3. Держать только в optional/supporting layer
В SUPPORTING_CASE, OPTIONAL_EU, COMMENTARY или ARCHIVE_OPTIONAL, но не в core:
	•	7 — II CSK 862/14, полезно по формальным требованиям к oświadczenie o potrąceniu, но не rental-specific;
	•	8 — I CSK 292/12, спор про gmina / local socjalny, только косвенно полезен;
	•	15 — 330695, полезно по burden of proof / limitation, но не верхний приоритет;
	•	18 — 486542, foreign-law / German BGB case;
	•	19 — 487012, расчёты по найму, burden of proof и limitation, но не классический иск о возврате кауции;
	•	21 — 521555, само дело не о возврате кауции;
	•	28–30 — только EU_CROSS_BORDER_PROCEDURE;
	•	32 — Dexia, secondary EU unfair-terms case;
	•	34 — Curia fact sheet Unfair terms, только guidance;
	•	38 — prawo.pl, только commentary.  ￼  ￼

2.4. Удалить из core-runtime / перевести в excluded или archive
Из core-runtime исключить:
	•	9 — V CSK 480/18, коммерческий спор между компаниями;
	•	10 — I CNP 31/13, также коммерческий спор;
	•	11 — SAOS search-page, это не документ;
	•	37 — AmC 86/2003, потому что материал относится к developer/admin relation и лишь побочно упоминает модель kaucja depozytowo-czynszowa, а не спор lokator vs właściciel mieszkania.  ￼  ￼

3. Обязательные добавления вне вашего списка

Программист обязан добавить в базу и оглавление ещё три обязательных акта, даже если их нет в списке:
	•	действующий Kodeks postępowania cywilnego;
	•	действующую Ustawę o kosztach sądowych w sprawach cywilnych;
	•	если consumer-layer сохраняется, действующую Ustawę o ochronie konkurencji i konsumentów.

Без них агент будет плохо отвечать на вопросы о procesie, opłatach sądowych и enforcement abusive clauses. Это особенно важно, потому что сейчас statutory layer корпуса фактически состоит только из двух актов.  ￼  ￼

4. Очистка данных: критерии мусора, неактуальности и нерелевантности

Документ считать мусорным или нерелевантным для core-runtime, если выполнено хотя бы одно условие:
	1.	это search/result page, landing page или query-URL;
	2.	это mirror/alias при наличии official source;
	3.	это историческая редакция нормы при наличии действующего codified text;
	4.	это case law вне контура tenant vs landlord / housing deposit, например purely commercial matters;
	5.	это duplicate representation того же дела из SAOS и court portal;
	6.	у записи нет аутентичного текста или это технический артефакт.

Возраст сам по себе основанием для удаления не является. Все исключения не удалять физически без следа, а переводить в status=excluded или status=archived с обязательным exclusion_reason. В текущем корпусе точные дубли уже частично чистились, но semantic duplicates и слабые заголовки остаются, поэтому нужна полноценная migration, а не ручная подправка нескольких карточек.  ￼  ￼

5. Новая схема данных

Для всех active документов обязательны поля:

doc_uid, status, document_kind, legal_role, jurisdiction, source_tier, canonical_title, title_short, source_url, normalized_source_url, external_id, checksum_sha256, language, summary_1line, issue_tags, search_terms_positive, search_terms_negative, query_templates, relevance_score, last_verified_at, storage_uri.

Дополнительно для STATUTE / EU_ACT обязательны:

act_id, act_short_name, is_consolidated_text, current_status, current_text_ref, article_nodes, key_provisions.

Дополнительно для CASELAW обязательны:

case_signature, court_name, court_level, judgment_date, artifact_type, holding_1line, same_case_group_id, related_provisions, facts_tags.

Для excluded / archived обязательны:

exclusion_reason, superseded_by, is_search_page.

Обязательно создать article-nodes минимум для:
	•	закона o ochronie praw lokatorów: art. 6, art. 19a–19e, art. 36;
	•	Kodeks cywilny: art. 6, art. 118, art. 385¹–385³, art. 471, art. 481, art. 498–499, art. 659, art. 675, art. 677, art. 678.  ￼

6. Правила канонизации

Приоритет канонического источника должен быть таким:
	1.	официальный действующий текст закона Польши (ELI / ISAP);
	2.	официальные решения SN, TK, CURIA, EUR-Lex, UOKiK;
	3.	SAOS API;
	4.	официальные порталы решений судов;
	5.	commentary / commercial mirrors;
	6.	search pages — никогда не канон.

Для одного и того же дела должен существовать один same_case_group_id. Примеры, которые нужно обязательно сгруппировать:
	•	III Ca 1707/18 — SAOS + portal;
	•	V ACa 599/14 — SAOS/иной канон + portal;
	•	I Ca 56/18 — каноническая запись + portal mirror.  ￼  ￼  ￼

7. Обязательная нормализация текущих плохих заголовков

Минимум вручную нормализовать следующие записи:
	•	sn_pl:V_CSK_480-18 — убрать заголовок SN, оставить официальный signature/title;
	•	sn_pl:I_CNP_31-13 — убрать Untitled HTML Document;
	•	uokik_pl:urlsha:c506ff470f4740ad — переименовать в Decyzja Prezesa UOKiK RKR-37/2013 (Novis MSK);
	•	curia_eu:urlsha:54acc341b17f3a57 — переименовать в C-488/11 Asbeek Brusse and Katarina de Man Garabito;
	•	curia_eu:urlsha:ef65918198e5ffee — переименовать в C-243/08 Pannon GSM;
	•	eurlex_eu:urlsha:252f802534879b95 — переименовать в Commission Notice — Guidance on the interpretation and application of Directive 93/13/EEC;
	•	uokik_pl:urlsha:5efe92f726049194 — вывести из core-runtime.  ￼  ￼  ￼  ￼  ￼  ￼  ￼

8. Технический порядок выполнения
	1.	Снять backup documents, pages, nodes, citations, document_sources, ingest_runs.  ￼
	2.	Создать migration-map по позициям 1–38 со статусами: canonical, article_node, alias, optional, excluded.
	3.	Для уже существующих записей обновлять metadata in-place, а не создавать новые дубли.
	4.	Переингестить и поднять в runtime current consolidated versions нормативных актов.
	5.	Сгруппировать одинаковые дела из SAOS / portal / mirror в same_case_group_id.
	6.	Перестроить pages, nodes, citations.
	7.	Сгенерировать новое Markdown-оглавление из БД.
	8.	Прогнать regression queries.
	9.	Закрыть миграцию CI-проверками, запрещающими попадание в runtime:
	•	search pages;
	•	legacy mirrors как top-level docs;
	•	Untitled/RPEX/raw XML titles;
	•	duplicate case groups.

9. Новая структура оглавления

Оглавление должно генерироваться в такой структуре:
	1.	Нормы Польши — прямое регулирование
	2.	Нормы Польши — процесс и судебные расходы
	3.	Ведущие решения Польши (SN / TK / leading appellate)
	4.	Фактическая практика по спорам о возврате кауции
	5.	EU consumer layer
	6.	EU cross-border / optional procedure
	7.	Guidance / commentary
	8.	Archive / excluded

Каждая строка оглавления обязана содержать:
	•	canonical_title;
	•	doc_uid;
	•	legal_role;
	•	relevance_score;
	•	issue_tags;
	•	summary_1line;
	•	для норм — key_provisions;
	•	для дел — holding_1line и same_case_group_id.

10. Критерии приёмки

После миграции система должна проходить минимум такие запросы:
	•	zwrot kaucji po najmie mieszkania
	•	waloryzacja kaucji mieszkaniowej sprzed 12 listopada 1994
	•	najem okazjonalny zwrot kaucji
	•	potrącenie z kaucji a ciężar dowodu
	•	abuzywna klauzula zatrzymania kaucji
	•	odsetki i przedawnienie roszczenia o zwrot kaucji

Работа считается принятой, если:
	•	в top-5 по базовым запросам появляется хотя бы одна прямая норма Польши;
	•	search pages и legacy mirrors не попадают в выдачу;
	•	один и тот же кейс не показывается дважды из SAOS и portal;
	•	commentary не ранжируется выше official norm / leading case по умолчанию;
	•	все документы из блока обязательно включить присутствуют в корпусе и правильно классифицированы;
	•	все документы из блока excluded исключены из core-runtime.

Главный принцип этой редакции такой: из вашего списка нужно не «залить все ссылки как есть», а собрать из них чистый канон — official current norms, ведущие решения, прямую фактическую практику, article-nodes и aliases, без search pages, без зеркал и без коммерческого шума.