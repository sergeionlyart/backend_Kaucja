# Техническое задание
## Реализация прототипной ссылочной системы и юридического аналитического pipeline для стратегического меморандума по спорам о возврате арендной кауции

Версия: 0.1  
Дата: 2026-03-22  
База: текущий архив репозитория `backend_Kaucja-main (4)`

---

## 1. Цель решения

Необходимо реализовать новый рабочий контур, который на основании:
- текстового сообщения пользователя;
- пакета пользовательских документов в формате Markdown (`.md`);
- локальной нормативной базы в MongoDB,

формирует **стратегический меморандум** по спору о возврате арендной кауции.

Главное обязательное свойство результата: **прозрачная ссылочная система на конкретные правовые фрагменты**.  
На текущем этапе итоговый документ должен содержать **индексы якорей** и отдельный реестр соответствия этих индексов конкретным документам и anchor-id. Реализация кликабельных frontend-ссылок в scope не входит.

---

## 2. Scope и ограничения этапа

### 2.1. В scope входит

1. Анализ пользовательского сообщения и пользовательских Markdown-документов.
2. Подготовка якорной разметки для пользовательских документов и нормативного корпуса.
3. Поиск релевантных нормативных документов и anchor-фрагментов в MongoDB.
4. Генерация стратегического меморандума с индексами правовых якорей.
5. Сохранение артефактов прогонов и реестра цитирования.
6. Отдельный скрипт индексации нормативной коллекции и расстановки якорей.
7. Архитектура на базе OpenAI Agents SDK.

### 2.2. В scope не входит

1. OCR.
2. Извлечение текста из PDF/изображений/сканов.
3. Кликабельные ссылки и frontend-навигация по якорям.
4. Полноценная промышленная citation-runtime система с sentence-level гарантией.
5. Векторная БД и сложный semantic search-stack.
6. Автоматическое обновление / reindex всего корпуса по cron.

### 2.3. Базовые допущения

1. Все пользовательские документы на входе уже находятся в Markdown.
2. Нормативные документы уже собраны в MongoDB текущим `legal_docs_pipeline`.
3. Хост, на котором запускается индексация нормативного корпуса, имеет доступ к исходным `.md` по путям из поля `source.absolute_path` текущей master-коллекции.
4. Корпус небольшой/средний и на первом контуре решения не требует отдельного vector stack.

---

## 3. Что уже есть в текущем репозитории и должно быть переиспользовано

### 3.1. Правовой корпус

В текущем репозитории `legal_docs_pipeline` уже формирует Mongo-коллекцию документов с полезными doc-level полями:
- `_id` / `doc_id`;
- `source.title`, `source.absolute_path`, `source.file_sha256`, `source.canonical_text_sha256`;
- `dedup.canonical_doc_uid`;
- `classification.document_type_code`;
- `search.document_family`;
- `search.authority_level`;
- `search.relevance`;
- `search.usually_supports`;
- `search.topic_codes`;
- `search.use_for_tasks_codes`;
- `search.tags_original`, `search.tags_ru`;
- `processing.status`.

Эти поля являются базой для prefilter и retrieval.

### 3.2. Нормализация сложных HTML-heavy документов

В репозитории уже есть `legal_docs_pipeline/canonicalize.py`. Его нужно использовать как обязательный pre-step для нормативных документов, которые были получены как HTML-heavy Markdown и плохо подходят для прямой якоризации.

### 3.3. Упаковка документов

В `app/pipeline/pack_documents.py` уже реализована безопасная упаковка документов в контейнер:
- `<BEGIN_DOCUMENTS>`
- `<DOC_START id="...">`
- `<DOC_END>`
- `<END_DOCUMENTS>`

Эту схему нужно переиспользовать для некоторых LLM-вызовов.

### 3.4. Хранилище артефактов прогонов

В `app/storage/artifacts.py` и `app/storage/repo.py` уже есть рабочая схема хранения run/session артефактов. Новый pipeline должен использовать её, а не создавать новый параллельный механизм без необходимости.

### 3.5. Важное ограничение текущей master-коллекции

Текущая коллекция правового корпуса **не хранит большие текстовые blob-поля inline**. Это правильно.  
Следовательно:
- новый контур **не должен** возвращать в master-коллекцию `annotated_markdown` и большие anchor index blob-поля;
- anchor runtime должен храниться отдельно.

### 3.6. Важное ограничение PromptManager

Текущий `app/prompts/manager.py` всегда ожидает `schema.json`, даже если prompt работает в `plain_text`-режиме.  
Для нового агентного контура это означает:
- либо доработать PromptManager;
- либо для Agents SDK использовать отдельный lightweight loader для prompt text;
- либо держать prompts в той же файловой иерархии, но не прогонять их через текущий `PromptManager`.

В рамках данного ТЗ рекомендуется **не завязывать агентные prompts на текущий PromptManager**, а хранить их как текстовые файлы и загружать напрямую.

---

## 4. Входные данные

### 4.1. Вход online pipeline

1. `user_message: str` — текстовое сообщение пользователя.
2. `user_documents: list[UserMarkdownDocument]` — пакет пользовательских Markdown-документов.
3. `runtime_config` — режим тест/прод, лимиты tool calls, лимиты retrieval и т.п.

### 4.2. Структура пользовательского документа

```json
{
  "doc_id": "user_lease_01",
  "file_name": "lease.md",
  "markdown": "..."
}
```

### 4.3. Вход offline indexing pipeline

1. Подключение к MongoDB.
2. Имя master-коллекции правового корпуса.
3. Список документов для индексации:
   - весь корпус;
   - shortlist по `doc_id`;
   - limit N.
4. Доступ к исходным `.md` по `source.absolute_path`.

---

## 5. Выходные данные

### 5.1. Основной итоговый документ

**Стратегический меморандум** в Markdown.

### 5.2. Обязательные артефакты online run

1. `case_issue_sheet.json`
2. `research_bundle.json`
3. `memo.json`
4. `memo.md`
5. `citation_register.json`
6. `search_trace.json`
7. user-doc anchor artifacts:
   - `annotated.md`
   - `anchor_index.json`

### 5.3. Обязательные артефакты offline indexing run

Для каждого нормативного документа:
1. `annotated.md`
2. `anchor_index.json`
3. `validation.json`
4. `build_manifest.json`

---

## 6. Архитектура решения

Решение состоит из двух контуров.

### 6.1. Контур A — offline индексация нормативной базы

Назначение:
- прочитать текущий правовой корпус из Mongo master-коллекции;
- загрузить исходный Markdown;
- при необходимости применить canonicalize;
- расставить якоря с помощью LLM;
- провалидировать результат;
- сохранить anchor runtime для дальнейшего retrieval.

### 6.2. Контур B — online юридический анализ пользовательского кейса

Назначение:
- принять сообщение пользователя и пользовательские `.md`;
- anchorize пользовательские документы;
- извлечь facts/issues;
- через Mongo-search tools найти релевантные правовые anchor-фрагменты;
- сформировать research bundle;
- сгенерировать стратегический меморандум;
- сохранить memo и citation register.

---

## 7. Новые хранилища и коллекции

## 7.1. Существующая master-коллекция

Используется без изменения как источник doc-level правового корпуса.  
По умолчанию брать имя из текущего `config/pipeline.yaml`, например `documents_cas_law_v2_2_prod_v3`.

## 7.2. Новая коллекция `legal_anchor_builds_proto_v1`

Назначение: хранить status и manifest якоризации нормативного документа.

Пример документа:

```json
{
  "_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md:sha256:abcd...",
  "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
  "source_sha256": "abcd...",
  "canonical_text_sha256": "efgh...",
  "anchor_schema": "md-anchor-v0-proto",
  "build_status": "completed",
  "model_id": "gpt-5.4",
  "reasoning_effort": "medium",
  "prompt_version": "v001",
  "anchor_count": 187,
  "artifact_paths": {
    "annotated_markdown": ".../annotated.md",
    "anchor_index": ".../anchor_index.json",
    "validation": ".../validation.json"
  },
  "created_at": "...",
  "updated_at": "..."
}
```

## 7.3. Новая коллекция `legal_anchor_nodes_proto_v1`

Назначение: runtime-поиск по якорям и passage retrieval.

Один Mongo-документ = один anchor.

Пример:

```json
{
  "_id": "eu_acts/25...::s01-p003::abcd",
  "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
  "source_sha256": "abcd...",
  "canonical_text_sha256": "efgh...",
  "anchor_schema": "md-anchor-v0-proto",
  "anchor_id": "s01-p003",
  "parent_anchor": null,
  "type": "paragraph",
  "section_path": "s01",
  "order": 17,
  "locator": {
    "kind": "block",
    "label": "Article 1"
  },
  "preview": "The purpose of this Directive is to approximate...",
  "passage_text": "The purpose of this Directive is to approximate...",
  "passage_text_normalized": "the purpose of this directive is to approximate...",
  "synthetic": false,
  "doc_meta": {
    "title": "COUNCIL DIRECTIVE 93/13/EEC",
    "document_family": "normative_act",
    "document_type_code": "eu_directive",
    "authority_level": "primary",
    "relevance": "core",
    "usually_supports": "both",
    "topic_codes": ["consumer_protection", "unfair_terms"],
    "use_for_tasks_codes": ["claim", "legal_position"]
  },
  "artifact_paths": {
    "annotated_markdown": ".../annotated.md",
    "anchor_index": ".../anchor_index.json"
  },
  "created_at": "..."
}
```

## 7.4. Хранение артефактов

### Нормативные anchor artifacts

Рекомендуемый путь:

```text
artifacts/legal_anchor_builds/<doc_id>/<source_sha256>/
  annotated.md
  anchor_index.json
  validation.json
  build_manifest.json
```

### Online case artifacts

Использовать текущую run/session-структуру `app/storage/artifacts.py`, расширив её:

```text
data/sessions/<session_id>/runs/<run_id>/
  documents/<user_doc_id>/original/source.md
  documents/<user_doc_id>/anchors/annotated.md
  documents/<user_doc_id>/anchors/anchor_index.json
  case/case_issue_sheet.json
  research/search_trace.json
  research/research_bundle.json
  memo/memo_request.json
  memo/memo_response.json
  memo/memo.md
  memo/citation_register.json
  logs/run.log
```

---

## 8. Формат якорей и прототипная citation-схема

## 8.1. Канонический встроенный маркер

Использовать:

```text
<!--anchor:ANCHOR_ID-->
```

## 8.2. Формат `anchor_id`

На первом этапе использовать только простую стабильную схему:
- section anchors: `s01`, `s01-02`, `s01-02-03`
- paragraph anchors: `s01-p001`
- list item anchors: `s01-li001`
- table anchors: `s01-tbl001`
- blockquote anchors: `s01-bq001`
- code anchors: `s01-code001`
- pre-heading content: `pre-p001`
- optional subanchors: `s01-p003-a`, `s01-p003-b`

## 8.3. Что обязательно якорить в v1

1. headings;
2. обычные paragraph blocks;
3. list items;
4. tables как единый block;
5. blockquotes как единый block;
6. fenced code blocks;
7. pre-heading prose.

## 8.4. Что не обязательно в v1

1. table row synthetic anchors;
2. footnotes;
3. reference-style link definitions;
4. сложная распаковка raw HTML;
5. sentence-level anchors как обязательная норма.

## 8.5. Alias-система для memo

В финальном memo используются **локальные alias-идентификаторы**, а не полные `doc_id + anchor_id`.

Типы alias:
- `L01`, `L02`, ... — legal anchors;
- `U01`, `U02`, ... — user evidence anchors (рекомендуемо, но не обязательно для acceptance текущего этапа).

Правило:
- агент и memo writer получают **только заранее выданный список разрешённых alias**;
- в итоговом тексте memo используются только alias;
- в `citation_register.json` alias разворачиваются в `doc_id + anchor_id + preview`.

---

## 9. Индексационный скрипт нормативной базы

Имя entrypoint:

```text
scripts/build_proto_legal_anchors.py
```

### 9.1. Назначение

Скрипт должен:
1. выбрать документы из master-коллекции;
2. загрузить Markdown-текст документа;
3. при необходимости применить `canonicalize.py`;
4. вызвать LLM для anchor-разметки;
5. провалидировать ответ;
6. сохранить артефакты и записать anchor nodes в Mongo.

### 9.2. Источник текста документа

Так как текущая Mongo master-коллекция не хранит полный inline-текст, скрипт должен:
1. прочитать документ master-коллекции;
2. взять `source.absolute_path`;
3. открыть локальный `.md` файл;
4. при отсутствии файла пометить build как `failed` с кодом `source_unavailable`.

### 9.3. Правило выбора текста для якоризации

Для каждого документа:
- если документ обычный Markdown — использовать исходный `## Content` block;
- если документ HTML-heavy — использовать результат `legal_docs_pipeline/canonicalize.py`;
- если canonicalize завершился ошибкой — документ помечается `failed`, build не публикуется в anchor collection.

### 9.4. LLM prompt для anchorization

Нужно создать prompt:

```text
app/prompts/kaucja_anchor_markdown/v001/system_prompt.txt
```

Рекомендуемая стратегия prompt:
- роль: deterministic anchor markup module;
- задача: только вставка anchor comments и построение anchor index;
- запрет на смысловую редактуру;
- запрет на summary/translation;
- возврат строго двух блоков:
  - `<BEGIN_ANCHOR_INDEX> ... <END_ANCHOR_INDEX>`
  - `<BEGIN_ANNOTATED_MARKDOWN> ... <END_ANNOTATED_MARKDOWN>`

### 9.5. Упрощённый контракт `anchor_index`

```json
{
  "anchor_schema": "md-anchor-v0-proto",
  "doc_id": "string|null",
  "source_wrapper": "plain_markdown|doc_wrapper",
  "validation_warnings": [],
  "anchors": [
    {
      "anchor_id": "s01-p001",
      "parent_anchor": null,
      "type": "paragraph",
      "section_path": "s01",
      "order": 2,
      "synthetic": false,
      "locator": {
        "kind": "block",
        "label": "Article 1"
      },
      "preview": "Первые слова исходного фрагмента"
    }
  ]
}
```

### 9.6. Обязательная валидация после LLM

После ответа модели скрипт обязан проверить:
1. оба блока присутствуют;
2. JSON валиден;
3. `anchor_id` уникальны;
4. `anchor_index` отсортирован по порядку появления;
5. все non-synthetic anchors реально присутствуют в annotated markdown;
6. если удалить все `<!--anchor:...-->` из annotated markdown, исходный Markdown полностью совпадает с input text после нормализации переводов строк;
7. `doc_id` не придуман, а соответствует входу, если он был передан;
8. число anchors не равно нулю.

### 9.7. Политика ошибок anchorization

1. Первая невалидная попытка:
   - сохранить raw response;
   - выполнить 1 repair-pass с коротким системным repair prompt.
2. Вторая невалидная попытка:
   - `build_status = failed`;
   - не публиковать nodes в `legal_anchor_nodes_proto_v1`.

### 9.8. Политика re-build

Ключ versioning:
- `doc_id`
- `source_sha256`

Правило:
- если для пары `doc_id + source_sha256` уже есть `completed` build, повторный запуск без `--force` не пересоздаёт anchors;
- при изменении sha создаётся новый build.

### 9.9. Mongo запись после успешной сборки

После успешной валидации:
1. upsert в `legal_anchor_builds_proto_v1`;
2. полная перезапись anchor nodes только для текущей пары `doc_id + source_sha256`;
3. старые nodes для того же `doc_id`, но другого `source_sha256`, остаются как исторические или помечаются `stale=true`.

### 9.10. CLI-параметры скрипта

Обязательные параметры:
- `--mongo-uri`
- `--mongo-db`
- `--source-collection`
- `--anchor-builds-collection`
- `--anchor-nodes-collection`
- `--model`
- `--reasoning-effort`
- `--doc-id` (повторяемый)
- `--limit`
- `--force`
- `--dry-run`
- `--artifacts-root`

---

## 10. MongoDB индексы для нового runtime

### 10.1. Для `legal_anchor_builds_proto_v1`

Создать индексы:
- `(_id)`
- `(doc_id, source_sha256)` unique
- `(build_status)`
- `(updated_at)`

### 10.2. Для `legal_anchor_nodes_proto_v1`

Создать индексы:
- `(_id)`
- `(doc_id, anchor_id, source_sha256)` unique
- `(doc_meta.document_family)`
- `(doc_meta.authority_level)`
- `(doc_meta.topic_codes)`
- `(doc_meta.use_for_tasks_codes)`
- `(doc_meta.usually_supports)`
- `(source_sha256)`
- text index на полях:
  - `passage_text`
  - `preview`
  - `doc_meta.title`
  - `locator.label`

---

## 11. Agent-система на базе OpenAI Agents SDK

Реализация должна использовать OpenAI Agents SDK, но в **простом и контролируемом режиме**:
- без сложных handoff chains;
- без fully autonomous бесконечного tool loop;
- с последовательной оркестрацией в Python.

### 11.1. Общая схема агентной системы

Использовать 3 специализированных агента:

1. `CaseIntakeAgent`
   - без инструментов;
   - задача: выделить факты, timeline, денежные параметры, спорные вопросы;
   - output: `CaseIssueSheet`.

2. `LegalResearchAgent`
   - с Mongo-search tools;
   - задача: найти релевантные правовые документы и anchor-фрагменты;
   - output: `ResearchBundle`.

3. `MemoWriterAgent`
   - без инструментов;
   - задача: по `CaseIssueSheet + ResearchBundle` построить итоговый стратегический меморандум;
   - output: `StrategicMemo`.

### 11.2. Причина выбора именно такой схемы

1. Она сохраняет агентную архитектуру, но не делает её чрезмерно сложной.
2. Она хорошо совпадает с текущим стилем репозитория: отдельные LLM-stage с жёсткими contracts.
3. Она облегчает тестирование каждого шага отдельно.
4. Она даёт прозрачный контроль над tool usage и стоимостью.

---

## 12. Системные промпты агентов

## 12.1. `CaseIntakeAgent` — системный prompt

```text
Ты — юридический intake-аналитик по спорам о возврате арендной кауции.

Твоя задача:
1. прочитать сообщение пользователя;
2. проанализировать переданные Markdown-документы пользователя;
3. выделить факты, даты, денежные параметры, спорные вопросы и пробелы доказательной базы;
4. вернуть только структурированный JSON формата CaseIssueSheet.

Правила:
- используй только сообщение пользователя и переданные документы;
- не обращайся к внешнему праву;
- не придумывай факты;
- если факт не подтверждён прямо, помечай его как ambiguous или missing;
- если документы конфликтуют, отражай конфликт явно;
- ссылайся на пользовательские anchor-ссылки только если они присутствуют во входе;
- не пиши стратегический меморандум на этом шаге;
- не делай юридических выводов beyond issue framing.
```

## 12.2. `LegalResearchAgent` — системный prompt

```text
Ты — агент юридического поиска по локальной нормативной базе для споров о возврате арендной кауции.

Твоя задача:
1. получить CaseIssueSheet;
2. при необходимости вызвать доступные Mongo-search tools;
3. найти релевантные правовые документы и точечные anchor-фрагменты;
4. вернуть только структурированный JSON формата ResearchBundle.

Правила:
- используй только доступные tools и уже полученные данные по делу;
- не выдумывай правовые нормы, anchor_id или документы;
- предпочитай более авторитетные источники: primary/high перед medium/low;
- по ключевым вопросам старайся найти и supporting, и adverse материалы, если они есть;
- если правовой опоры недостаточно, отрази это в coverage_gaps;
- не формируй финальный меморандум;
- не превышай search budget;
- не цитируй anchor'ы, которых не вернул tool.
```

## 12.3. `MemoWriterAgent` — системный prompt

```text
Ты — юридический аналитик, который пишет стратегический меморандум по спору о возврате арендной кауции.

Твоя задача:
1. получить структурированный CaseIssueSheet;
2. получить структурированный ResearchBundle;
3. подготовить стратегический меморандум в формате StrategicMemo;
4. для каждого существенного правового вывода указывать legal_ref_ids из переданного citation register.

Правила:
- не используй никакие правовые источники, кроме тех, что переданы в ResearchBundle;
- не придумывай legal_ref_ids;
- если правовой опоры недостаточно, прямо укажи ограничение;
- отделяй установленные факты от предположений;
- отделяй сильные аргументы от рисков и слабых мест;
- не добавляй кликабельные ссылки;
- используй только переданные alias вида L01, L02, ... и при наличии U01, U02, ...;
- вывод должен быть полезным для практического решения, но не должен маскировать пробелы доказательств или слабую нормативную опору.
```

---

## 13. Модели данных для агентных шагов

## 13.1. `CaseIssueSheet`

Обязательные поля:

```json
{
  "user_goal": "string",
  "case_summary": "string",
  "timeline": [
    {
      "event": "string",
      "date": "string|null",
      "status": "confirmed|ambiguous|missing|conflict",
      "evidence": [
        {"doc_id": "user_lease_01", "anchor_id": "s01-p003"}
      ]
    }
  ],
  "money_facts": [
    {
      "name": "deposit_amount",
      "value": "string|null",
      "status": "confirmed|ambiguous|missing|conflict",
      "evidence": [
        {"doc_id": "user_payment_01", "anchor_id": "s01-p002"}
      ]
    }
  ],
  "established_facts": ["..."],
  "disputed_facts": ["..."],
  "missing_evidence": ["..."],
  "issue_codes": [
    "deposit_return_term",
    "allowed_deductions",
    "burden_of_proof"
  ]
}
```

## 13.2. `ResearchBundle`

```json
{
  "issues": [
    {
      "issue_code": "deposit_return_term",
      "question": "Когда и на каких условиях должна быть возвращена кауция?",
      "search_notes": "..."
    }
  ],
  "legal_authorities": [
    {
      "ref_id": "L01",
      "doc_id": "eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md",
      "anchor_id": "s01-p003",
      "document_title": "COUNCIL DIRECTIVE 93/13/EEC",
      "locator_label": "Article 1",
      "authority_level": "primary",
      "usually_supports": "both",
      "topic_codes": ["consumer_protection"],
      "quote": "The purpose of this Directive is to approximate...",
      "supports_position": "supporting|adverse|neutral"
    }
  ],
  "coverage_gaps": ["..."],
  "search_trace": {
    "tool_calls_used": 2,
    "queries": ["..."]
  }
}
```

## 13.3. `StrategicMemo`

```json
{
  "title": "Стратегический меморандум по спору о возврате кауции",
  "executive_summary": [
    {
      "text": "...",
      "legal_ref_ids": ["L01", "L03"],
      "evidence_ref_ids": ["U01"]
    }
  ],
  "facts_considered": [
    {
      "text": "...",
      "evidence_ref_ids": ["U01", "U02"]
    }
  ],
  "legal_analysis": [
    {
      "issue_code": "allowed_deductions",
      "issue_title": "Допустимые удержания из кауции",
      "analysis_points": [
        {
          "text": "...",
          "legal_ref_ids": ["L02", "L05"],
          "evidence_ref_ids": ["U03"]
        }
      ],
      "risks": [
        {
          "text": "...",
          "legal_ref_ids": ["L06"]
        }
      ],
      "practical_takeaway": "..."
    }
  ],
  "recommended_next_steps": ["..."],
  "limitations": ["..."],
  "citation_register": {
    "legal": [
      {
        "ref_id": "L01",
        "doc_id": "...",
        "anchor_id": "...",
        "locator_label": "...",
        "preview": "..."
      }
    ],
    "evidence": [
      {
        "ref_id": "U01",
        "doc_id": "...",
        "anchor_id": "...",
        "preview": "..."
      }
    ]
  }
}
```

---

## 14. Tooling-слой для MongoDB

## 14.1. Общий принцип

Агент не получает прямой доступ к MongoDB.  
Он вызывает только ограниченный набор Python function tools.

## 14.2. Набор обязательных tools

### Tool 1. `search_legal_docs`

Назначение:
- выполнить doc-level prefilter по master-коллекции корпуса.

Вход:
- `question: str`
- `issue_codes: list[str]`
- `position: "tenant"|"landlord"|"both"`
- `max_docs: int`
- `authority_min: "primary"|"high"|"medium"|"low"`

Выход:
- shortlist релевантных документов.

Поля, которые использовать в поиске:
- `search.document_family`
- `search.authority_level`
- `search.topic_codes`
- `search.use_for_tasks_codes`
- `search.usually_supports`
- `search.tags_original`
- `search.tags_ru`
- `source.title`
- `classification.document_type_code`
- `processing.status`

Политика фильтрации:
- брать только `processing.status = completed`;
- исключать явно сервисные/нерелевантные документы;
- по умолчанию ограничивать `document_family` значениями:
  - `normative_act`
  - `judicial_decision`
  - `consumer_admin`
  - при необходимости `commentary_article`, но с пониженным приоритетом.

### Tool 2. `search_legal_anchors`

Назначение:
- найти anchor-фрагменты внутри shortlist или по всему `legal_anchor_nodes_proto_v1`.

Вход:
- `query: str`
- `candidate_doc_ids: list[str]`
- `issue_code: str|null`
- `max_hits: int`

Выход:
- список anchor hits.

Поля поиска:
- text index по `passage_text`, `preview`, `doc_meta.title`, `locator.label`
- metadata filters по:
  - `doc_meta.topic_codes`
  - `doc_meta.authority_level`
  - `doc_meta.usually_supports`
  - `doc_meta.document_family`

### Tool 3. `get_anchor_details`

Назначение:
- вернуть точные passage-фрагменты по выбранным `doc_id + anchor_id`.

Вход:
- `items: list[{doc_id, anchor_id}]`

Выход:
- детальный passage payload для memo.

## 14.3. Как ограничивать объём и число поисковых обращений

Нужно реализовать search budget в `RunContext`.

Обязательные параметры:
- `max_search_calls`
- `max_docs_per_search`
- `max_anchors_per_search`
- `max_total_legal_refs`

Правила:
1. каждый вызов `search_legal_docs` и `search_legal_anchors` уменьшает budget;
2. при превышении лимита tool возвращает controlled error payload;
3. агент в prompt обязан прекращать поиск при исчерпании budget;
4. в `search_trace.json` сохраняется фактическое число вызовов.

## 14.4. Рекомендуемые лимиты

### Test mode
- `max_search_calls = 2`
- `max_docs_per_search = 5`
- `max_anchors_per_search = 8`
- `max_total_legal_refs = 10`

### Product mode
- `max_search_calls = 4`
- `max_docs_per_search = 10`
- `max_anchors_per_search = 15`
- `max_total_legal_refs = 18`

## 14.5. Как формируется поисковый запрос

Поисковый запрос должен собираться из:
1. `user_message`
2. `issue_codes` из `CaseIssueSheet`
3. кратких keywords по спору:
   - кauцja
   - возврат/zwrot
   - срок возврата
   - удержания
   - повреждения
   - коммунальные платежи
   - burden of proof

Логика:
- сначала doc-level prefilter;
- затем anchor-level text search;
- затем точечный fetch деталей.

## 14.6. Ранжирование результатов

Для первого этапа ранжирование реализовать в Python после Mongo-fetch.

Рекомендуемая формула score:
- базовый `text_score`
- +0.30 для `authority_level = primary`
- +0.20 для `authority_level = high`
- +0.10 за exact topic match
- +0.05 если `usually_supports in {both, tenant}` и дело инициировано арендатором
- -0.10 для `commentary_article`

После ранжирования:
- dedupe по `doc_id + anchor_id`
- diversity cap: не более 3 anchors на один документ, если не требуется иначе.

---

## 15. Конфигурация моделей и режимов

### 15.1. Базовая модель

Для всех агентных шагов использовать:

```text
gpt-5.4
```

### 15.2. Режимы reasoning

Обязательные режимы:
- `test` -> `medium`
- `prod` -> `high`

### 15.3. Verbosity

Для всех агентов:
- `verbosity = low`

### 15.4. Параметры по умолчанию

#### Test mode
- model: `gpt-5.4`
- reasoning effort: `medium`
- max turns (research agent): `6`
- max search calls: `2`

#### Product mode
- model: `gpt-5.4`
- reasoning effort: `high`
- max turns (research agent): `10`
- max search calls: `4`

### 15.5. Примечание по anchorization script

Для простоты текущего этапа скрипт индексации также должен поддерживать те же режимы:
- test -> `medium`
- prod -> `high`

---

## 16. Online pipeline: пошаговая логика

## Шаг 1. Приём запроса и документов

Вход:
- `user_message`
- `list[Markdown document]`

Действия:
1. создать session/run в текущем run storage;
2. сохранить входные `.md` в артефакты run;
3. присвоить стабильные `user_doc_id`.

## Шаг 2. Якоризация пользовательских документов

Действия:
1. применить тот же anchor-builder, что и для нормативной базы, но в run-local режиме;
2. сохранить `annotated.md` и `anchor_index.json` по каждому пользовательскому документу;
3. собрать `user_anchor_catalog`.

Если user-doc anchorization невалидна:
- 1 repair-pass;
- если снова fail — run завершается `failed`.

## Шаг 3. Case intake

Действия:
1. собрать input для `CaseIntakeAgent`:
   - `user_message`
   - anchored user docs;
2. получить `CaseIssueSheet`;
3. провалидировать JSON schema;
4. сохранить `case_issue_sheet.json`.

## Шаг 4. Legal research

Действия:
1. передать `CaseIssueSheet` в `LegalResearchAgent`;
2. агент через tools ищет правовые документы и anchor passages;
3. после выполнения tool calls deterministic bundler:
   - assigns `L01`, `L02`, ...
   - строит `ResearchBundle`;
4. сохранить `research_bundle.json` и `search_trace.json`.

## Шаг 5. Memo generation

Действия:
1. передать `CaseIssueSheet + ResearchBundle` в `MemoWriterAgent`;
2. получить `StrategicMemo` JSON;
3. провалидировать schema;
4. проверить, что все `legal_ref_ids` существуют в citation register;
5. сохранить `memo.json`.

## Шаг 6. Рендеринг memo

Действия:
1. из `memo.json` сформировать `memo.md`;
2. сформировать `citation_register.json`;
3. сохранить артефакты.

## Шаг 7. Финальная валидация

Проверить:
1. memo не пустой;
2. каждый существенный правовой вывод имеет минимум 1 `Lxx`;
3. все `Lxx` существуют в register;
4. если есть `Uxx`, они тоже существуют;
5. нет неразрешённых alias.

---

## 17. Формат итогового стратегического меморандума

Финальный Markdown должен иметь следующую структуру.

```text
# Стратегический меморандум

## 1. Краткий вывод
...
[L01][L03]

## 2. Установленные факты
...
[U01][U02]

## 3. Ключевые правовые вопросы
### 3.1. ...
...
[L02][L05]

## 4. Сильные стороны позиции
...
[L01][L04]

## 5. Риски и слабые места
...
[L06]

## 6. Практические следующие шаги
...

## Приложение A. Реестр правовых якорей
L01 — doc_id=...; anchor_id=...; locator=...; preview="..."
L02 — doc_id=...; anchor_id=...; locator=...; preview="..."

## Приложение B. Реестр доказательственных якорей (опционально)
U01 — doc_id=...; anchor_id=...; preview="..."
```

### Обязательное правило

В основном тексте memo должны присутствовать **только индексы/alias**, а не кликабельные ссылки.

---

## 18. Детали реализации через OpenAI Agents SDK

### 18.1. Новая зависимость

Добавить в проект зависимость:

```text
openai-agents
```

### 18.2. Принцип использования SDK

В v1 использовать SDK так:
- `Agent` для каждого специализированного шага;
- `Runner.run()` или `Runner.run_sync()` для запуска;
- `output_type` через Pydantic-модели;
- function tools через Python-функции;
- `RunContext` для search budget.

### 18.3. Отдельные handoffs не обязательны

В текущем этапе handoffs и agents-as-tools использовать не обязательно.  
Предпочтительный вариант — последовательная оркестрация в Python:
1. Intake agent
2. Research agent
3. Memo agent

Это проще, надёжнее и легче тестируется.

### 18.4. Session management

По умолчанию online pipeline можно делать one-shot без долгоживущей session.  
Если потребуется follow-up режим, допускается подключение `SQLiteSession`.

---

## 19. Новые модули и файлы, которые нужно реализовать

### 19.1. Новый пакет `app/legal_memo/`

Рекомендуемая структура:

```text
app/legal_memo/
  __init__.py
  config.py
  models.py
  anchor_models.py
  anchor_builder.py
  anchor_parser.py
  anchor_validator.py
  anchor_repository.py
  user_anchor_service.py
  case_intake_agent.py
  legal_research_agent.py
  memo_writer_agent.py
  mongo_search_tools.py
  renderer.py
  validators.py
  service.py
```

### 19.2. Prompts

```text
app/prompts/kaucja_anchor_markdown/v001/system_prompt.txt
app/prompts/legal_case_intake/v001/system_prompt.txt
app/prompts/legal_research_agent/v001/system_prompt.txt
app/prompts/strategic_memo_writer/v001/system_prompt.txt
```

### 19.3. Скрипты

```text
scripts/build_proto_legal_anchors.py
scripts/run_strategic_memo.py
```

### 19.4. Тесты

```text
tests/legal_memo/test_anchor_parser.py
tests/legal_memo/test_anchor_validator.py
tests/legal_memo/test_anchor_builder.py
tests/legal_memo/test_anchor_repository.py
tests/legal_memo/test_mongo_search_tools.py
tests/legal_memo/test_case_intake_agent.py
tests/legal_memo/test_legal_research_agent.py
tests/legal_memo/test_memo_writer_agent.py
tests/legal_memo/test_service_end_to_end.py
```

---

## 20. Логика поиска и retrieval: практическая реализация

## 20.1. Search path

Поиск должен идти по двухступенчатой схеме.

### Стадия A. Prefilter документов

По `search.*` и doc-level metadata master-коллекции.

### Стадия B. Поиск anchor passages

По `legal_anchor_nodes_proto_v1`.

## 20.2. Почему не искать сразу по master-коллекции

Потому что memo должен ссылаться на конкретные anchors, а не на документ в целом.  
Следовательно, runtime retrieval должен работать по anchor nodes.

## 20.3. Почему не нужен vector DB на первом этапе

Потому что:
1. корпус ограничен;
2. тема узкая;
3. существующие `topic_codes`, `authority_level`, `usually_supports` уже дают сильный prefilter;
4. для пилота проще и надёжнее использовать Mongo text index + metadata boosts.

---

## 21. Валидация результата и quality gates

## 21.1. Валидация anchor builds

Build считается успешным только если:
1. response contract соблюдён;
2. strip-anchors == source text;
3. anchor ids уникальны;
4. build сохранён в artifacts;
5. nodes опубликованы в Mongo.

## 21.2. Валидация `CaseIssueSheet`

Проверить:
1. JSON schema valid;
2. issue_codes не пусты;
3. каждая ссылка на `doc_id + anchor_id` существует в user anchor catalog.

## 21.3. Валидация `ResearchBundle`

Проверить:
1. `legal_authorities` не пусты либо явно заполнен `coverage_gaps`;
2. все `doc_id + anchor_id` существуют в `legal_anchor_nodes_proto_v1`;
3. `Lxx` уникальны;
4. `search_trace.tool_calls_used <= max_search_calls`.

## 21.4. Валидация `StrategicMemo`

Проверить:
1. JSON schema valid;
2. в каждом `analysis_point` есть `legal_ref_ids`;
3. все `legal_ref_ids` принадлежат citation register;
4. нет неизвестных `Lxx`;
5. если указаны `Uxx`, они тоже существуют;
6. memo не содержит ссылок на anchor ids напрямую, кроме alias-системы.

---

## 22. План тестирования

## 22.1. Unit tests

### Anchorization
- корректный разбор двухблочного ответа LLM;
- уникальность `anchor_id`;
- strip-anchors == source;
- отказ при дублировании anchors;
- отказ при потере текста.

### Search tools
- корректный prefilter по `topic_codes`;
- корректный поиск anchors по text index;
- работа authority ranking;
- enforcement `max_search_calls`.

### Agents
- schema-valid `CaseIssueSheet`;
- schema-valid `ResearchBundle`;
- schema-valid `StrategicMemo`;
- отказ при unknown `Lxx`.

## 22.2. Integration tests

1. Инициализация маленькой тестовой Mongo-базы.
2. Индексация 2–5 нормативных документов.
3. Запуск online pipeline на 2–3 пользовательских документах.
4. Генерация `memo.md`.
5. Проверка реестра `Lxx`.

## 22.3. E2E smoke tests

Минимальный pilot-набор:
- 2–5 пользовательских `.md`;
- 10–20 нормативных документов в preindexed short corpus;
- 1 пользовательский запрос.

Проверять:
1. run завершается успешно;
2. memo содержит legal refs;
3. refs разрешаются в register;
4. артефакты полностью сохранены;
5. время выполнения укладывается в целевой бюджет.

## 22.4. Негативные тесты

1. user-doc anchorization invalid;
2. отсутствует `source.absolute_path` для нормативного документа;
3. search budget exceeded;
4. research bundle пуст;
5. memo writer пытается сослаться на неизвестный alias.

---

## 23. Критерии качества результата

## 23.1. Функциональные

1. Pipeline принимает `user_message + user_documents.md`.
2. Pipeline выполняет legal retrieval по Mongo.
3. Pipeline формирует стратегический меморандум.
4. Каждый существенный правовой вывод в memo имеет legal alias `Lxx`.
5. Каждый `Lxx` разрешается в `doc_id + anchor_id`.

## 23.2. Качественные

1. Нет вымышленных `anchor_id`.
2. Нет ссылок на несуществующие документы.
3. Нет ссылок вне citation register.
4. Memo не скрывает пробелы доказательств и пробелы правовой опоры.
5. Search budget соблюдается.

## 23.3. Инженерные

1. Master-коллекция нормативного корпуса не раздувается большими blob-полями.
2. Anchor runtime хранится отдельно.
3. Артефакты прогонов сохраняются.
4. Логи достаточны для отладки.
5. Все новые модули покрыты unit/integration tests.

---

## 24. Критерии готовности к следующему этапу

Решение считается готовым к следующему этапу, если выполнены все условия:

1. Успешно проиндексирован pilot-набор нормативных документов.
2. Есть рабочие Mongo-search tools.
3. Есть end-to-end pipeline: intake -> retrieval -> memo.
4. Memo стабильно содержит правовые alias `Lxx`.
5. Реестр `citation_register.json` корректно восстанавливает `doc_id + anchor_id`.
6. На pilot-кейсах нет неизвестных или битых ссылок.
7. Система не требует frontend-слоя для понимания, на какие anchors опирается memo.

---

## 25. Порядок реализации

### Фаза 1. Нормативная индексация
1. Реализовать anchor data models.
2. Реализовать parser + validator.
3. Реализовать `build_proto_legal_anchors.py`.
4. Реализовать `legal_anchor_builds_proto_v1` и `legal_anchor_nodes_proto_v1`.

### Фаза 2. User-document anchorization
1. Реализовать user-local anchor service.
2. Добавить сохранение артефактов в текущий run storage.

### Фаза 3. Agent pipeline
1. Реализовать `CaseIntakeAgent`.
2. Реализовать Mongo-search tools.
3. Реализовать `LegalResearchAgent`.
4. Реализовать `MemoWriterAgent`.
5. Реализовать renderer и validators.

### Фаза 4. Тестирование и smoke run
1. Unit tests.
2. Integration tests.
3. Smoke E2E на малой выборке.

---

## 26. Практическое решение по спорным архитектурным вопросам

### 26.1. Нужно ли делать сложную кликабельную ссылочную систему сейчас?

Нет. В текущем этапе достаточно:
- alias в тексте memo;
- реестр alias -> `doc_id + anchor_id + preview`.

### 26.2. Нужно ли делать полноформатную canonical citation runtime прямо сейчас?

Нет. Для текущего этапа достаточно прототипной LLM-якоризации с жёсткой post-validation и version binding по `source_sha256`.

### 26.3. Нужно ли использовать handoffs и сложную multi-agent оркестрацию?

Нет. Последовательные агенты проще, дешевле в сопровождении и лучше соответствуют текущему стилю репозитория.

### 26.4. Нужно ли расширять PromptManager под Agents SDK прямо сейчас?

Нет. Для этого этапа лучше использовать отдельный text prompt loader и Pydantic `output_type` в коде.

---

## 27. Итог

В результате реализации по данному ТЗ должна появиться рабочая прототипная система, которая:
1. использует существующую MongoDB-коллекцию правового корпуса как основу для retrieval;
2. предварительно индексирует нормативные документы якорями;
3. anchorize-ит пользовательские Markdown-документы внутри run;
4. строит `CaseIssueSheet`;
5. через OpenAI Agents SDK и Mongo tools находит релевантные правовые anchor-фрагменты;
6. генерирует стратегический меморандум;
7. указывает в нём индексы правовых якорей;
8. сохраняет реестр, по которому можно проверить, на какие документы и anchors опирается каждый ключевой вывод.

Это достаточный и реалистичный контур для перехода к рабочему прототипу без преждевременного усложнения архитектуры.
