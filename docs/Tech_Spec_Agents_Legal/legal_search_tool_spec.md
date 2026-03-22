# Практическая спецификация поискового инструмента `legal_search_tools`

Версия: 0.1  
Дата: 2026-03-22

## 1. Назначение

`legal_search_tools` — это набор локальных Python function tools для OpenAI Agents SDK, через который агентная система получает **контролируемый** доступ к правовой базе в MongoDB.

Агент **не имеет** прямого доступа к MongoDB и **не формирует** произвольные запросы к базе.  
Он может вызывать только три инструмента:

1. `search_legal_docs`
2. `search_legal_anchors`
3. `get_anchor_details`

Именно этот набор обеспечивает:
- doc-level prefilter;
- anchor-level retrieval;
- точечную подгрузку passage details для финального меморандума.

---

## 2. Коллекции MongoDB

Инструмент работает с двумя коллекциями.

### 2.1. Master-коллекция правового корпуса
Источник doc-level метаданных.  
Ожидаемые поля:

- `_id` / `doc_id`
- `processing.status`
- `source.title`
- `source.absolute_path`
- `search.document_family`
- `search.authority_level`
- `search.topic_codes`
- `search.use_for_tasks_codes`
- `search.usually_supports`
- `search.tags_original`
- `search.tags_ru`
- `classification.document_type_code`

### 2.2. Anchor-коллекция
Источник passage-level retrieval.  
Ожидаемые поля:

- `doc_id`
- `anchor_id`
- `passage_text`
- `preview`
- `locator.label`
- `section_path`
- `doc_meta.title`
- `doc_meta.topic_codes`
- `doc_meta.authority_level`
- `doc_meta.usually_supports`
- `doc_meta.document_family`

---

## 3. Общая стратегия поиска

Поиск всегда двухступенчатый.

### Стадия 1. `search_legal_docs`
Используется для короткого shortlist релевантных документов.

### Стадия 2. `search_legal_anchors`
Используется для поиска конкретных passage-фрагментов внутри shortlist.

### Стадия 3. `get_anchor_details`
Используется только для тех passage-фрагментов, которые уже отобраны для включения в `ResearchBundle`.

Это принципиально важно: агент не должен сразу тянуть большие куски текста и не должен искать якоря по всему корпусу без doc-level prefilter, если только shortlist не пуст.

---

## 4. Как формируется поисковый запрос

### 4.1. Базовые источники query
Поисковая фраза собирается из:

1. `user_message`
2. `CaseIssueSheet.issue_codes`
3. кратких терминов по спору:
   - `kaucja`
   - `zwrot kaucji`
   - `deposit return`
   - `potrącenie`
   - `uszkodzenie`
   - `zużycie`
   - `czynsz`
   - `opłaty`
   - `burden of proof`

### 4.2. Правило query-building
Для каждого issue code строится отдельный короткий query:
- 1 формулировка вопроса;
- 3–8 ключевых терминов;
- без длинных описательных абзацев;
- без попытки “втиснуть всё дело в один запрос”.

### 4.3. Пример
Для issue `allowed_deductions`:
- `question`: `What legal grounds allow or limit deductions from a rental deposit?`
- `keywords`: `kaucja`, `potrącenie`, `zwrot`, `damage`, `wear and tear`, `arrears`

Итоговая search string:
`allowed_deductions kaucja potrącenie zwrot damage wear and tear arrears`

---

## 5. Tool 1 — `search_legal_docs`

## 5.1. Задача
Найти shortlist документов-кандидатов на уровне документа.

## 5.2. Вход
```json
{
  "question": "string",
  "issue_codes": ["deposit_return_term", "allowed_deductions"],
  "position": "tenant",
  "max_docs": 5,
  "authority_min": "high"
}
```

## 5.3. Поиск
Сначала применяется фильтр:
- `processing.status = completed`
- `search.document_family in {normative_act, judicial_decision, consumer_admin, commentary_article}`
- `search.authority_level >= authority_min`

Далее применяются:
- точное/частичное совпадение по `search.topic_codes`
- match по `search.tags_original`, `search.tags_ru`
- match по `source.title`
- при наличии индекса — `$text` search

## 5.4. Ранжирование
После Mongo-fetch ранжирование идёт в Python.

Рекомендуемая формула:
- `text_score`
- `+0.30` для `authority_level=primary`
- `+0.20` для `authority_level=high`
- `+0.10` за exact topic match
- `+0.05` если `usually_supports in {tenant, both}` при tenant-side деле
- `-0.10` для `commentary_article`

## 5.5. Выход
```json
{
  "status": "ok",
  "query_used": "string",
  "budget_remaining": {
    "search_calls_left": 1,
    "docs_per_search_left": 5,
    "anchors_per_search_left": 8,
    "legal_refs_left": 10
  },
  "hits": [
    {
      "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
      "title": "COUNCIL DIRECTIVE 93/13/EEC",
      "document_family": "normative_act",
      "authority_level": "primary",
      "usually_supports": "both",
      "topic_codes": ["consumer_protection", "unfair_terms"],
      "score": 0.91
    }
  ],
  "warnings": []
}
```

---

## 6. Tool 2 — `search_legal_anchors`

## 6.1. Задача
Найти конкретные passage-фрагменты в anchor-коллекции.

## 6.2. Вход
```json
{
  "query": "string",
  "candidate_doc_ids": ["doc1", "doc2"],
  "issue_code": "allowed_deductions",
  "max_hits": 8
}
```

## 6.3. Поведение
1. Если `candidate_doc_ids` не пуст, поиск ограничивается ими.
2. Если shortlist пуст, инструмент может искать по всей anchor-коллекции, но это должно быть отдельным осознанным решением агента.
3. Поиск идёт по:
   - `passage_text`
   - `preview`
   - `doc_meta.title`
   - `locator.label`

Плюс metadata filters по:
- `doc_meta.topic_codes`
- `doc_meta.authority_level`
- `doc_meta.document_family`
- `doc_meta.usually_supports`

## 6.4. Выход
```json
{
  "status": "ok",
  "query_used": "string",
  "budget_remaining": {
    "search_calls_left": 0,
    "docs_per_search_left": 5,
    "anchors_per_search_left": 8,
    "legal_refs_left": 10
  },
  "hits": [
    {
      "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
      "anchor_id": "s01-p003",
      "document_title": "COUNCIL DIRECTIVE 93/13/EEC",
      "locator_label": "Article 1",
      "authority_level": "primary",
      "usually_supports": "both",
      "topic_codes": ["consumer_protection"],
      "preview": "The purpose of this Directive is to approximate...",
      "score": 0.88
    }
  ],
  "warnings": []
}
```

---

## 7. Tool 3 — `get_anchor_details`

## 7.1. Задача
Вернуть точный passage payload по уже выбранным `doc_id + anchor_id`.

## 7.2. Вход
```json
{
  "items": [
    {"doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md", "anchor_id": "s01-p003"}
  ]
}
```

## 7.3. Выход
```json
{
  "status": "ok",
  "items": [
    {
      "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
      "anchor_id": "s01-p003",
      "document_title": "COUNCIL DIRECTIVE 93/13/EEC",
      "locator_label": "Article 1",
      "authority_level": "primary",
      "usually_supports": "both",
      "topic_codes": ["consumer_protection"],
      "quote": "The purpose of this Directive is to approximate...",
      "preview": "The purpose of this Directive is to approximate..."
    }
  ],
  "warnings": []
}
```

---

## 8. Как агент вызывает tools

## 8.1. Типичный порядок
1. `search_legal_docs(...)`
2. `search_legal_anchors(...)`
3. `get_anchor_details(...)`

## 8.2. Типичный flow для одного issue
- агент видит `issue_code = deposit_return_term`;
- строит query из issue code + коротких keyword;
- получает shortlist документов;
- делает anchor search по shortlist;
- выбирает 2–4 лучших passage;
- вызывает `get_anchor_details`;
- включает passages в `ResearchBundle`.

## 8.3. Когда НЕ вызывать повторный поиск
Агент не должен делать новый search call, если:
- уже есть 2–3 качественных primary/high authorities на тот же issue;
- новый запрос по сути дублирует предыдущий;
- budget почти исчерпан и coverage уже приемлемая.

---

## 9. Ограничение числа обращений

В `RunContext` хранится search budget:

```python
max_search_calls
max_docs_per_search
max_anchors_per_search
max_total_legal_refs
```

Каждый вызов `search_legal_docs` и `search_legal_anchors` уменьшает `search_calls_left`.

### Рекомендуемые лимиты

#### Test mode
- `max_search_calls = 2`
- `max_docs_per_search = 5`
- `max_anchors_per_search = 8`
- `max_total_legal_refs = 10`

#### Product mode
- `max_search_calls = 4`
- `max_docs_per_search = 10`
- `max_anchors_per_search = 15`
- `max_total_legal_refs = 18`

Если budget исчерпан, tool возвращает controlled payload:
```json
{
  "status": "budget_exhausted",
  "hits": [],
  "warnings": ["search budget exhausted"]
}
```

---

## 10. Как результаты используются дальше

### 10.1. После `search_legal_docs`
Результаты используются только как shortlist.

### 10.2. После `search_legal_anchors`
Результаты используются для отбора passage-кандидатов.

### 10.3. После `get_anchor_details`
Результаты становятся входом в `ResearchBundle.legal_authorities`.

Именно из этих authorities потом строится:
- alias mapping `L01`, `L02`, ...
- `citation_register`
- финальный стратегический меморандум.

---

## 11. Практические правила качества

1. Не возвращать агенту сырой Mongo-документ целиком.
2. Не возвращать больше 1–2 экранов текста за один tool call.
3. Возвращать короткие, пригодные к reasoning payload’ы.
4. Не смешивать в одном tool call слишком много ролей:
   - shortlist отдельно,
   - anchors отдельно,
   - detail fetch отдельно.
5. Всегда возвращать `warnings`, даже если массив пуст.
6. Всегда возвращать `budget_remaining`, чтобы агент видел остаток лимитов.

---

## 12. Обязательные Mongo-индексы

### Для master-коллекции
- `processing.status`
- `search.document_family`
- `search.authority_level`
- `search.topic_codes`
- `search.usually_supports`
- text index по:
  - `source.title`
  - `search.tags_original`
  - `search.tags_ru`

### Для anchor-коллекции
- unique `(doc_id, anchor_id, source_sha256)`
- `doc_meta.topic_codes`
- `doc_meta.authority_level`
- `doc_meta.document_family`
- text index по:
  - `passage_text`
  - `preview`
  - `doc_meta.title`
  - `locator.label`

---

## 13. Что нельзя делать инструменту

Инструмент не должен:
- выполнять правовой анализ вместо агента;
- присваивать `Lxx` alias сам;
- формировать стратегический вывод;
- возвращать passages, которых нет в коллекции;
- скрывать, что budget исчерпан;
- silently truncating результаты без явного предупреждения.

---

## 14. Минимальный критерий готовности

`legal_search_tools` считается готовым, если:
1. агент может получить shortlist документов;
2. агент может получить shortlist anchor passages;
3. агент может точечно подгрузить финальные passage details;
4. все tool outputs детерминированно сериализуются в JSON;
5. лимиты budget реально соблюдаются;
6. `search_trace` можно восстановить по результатам run.
