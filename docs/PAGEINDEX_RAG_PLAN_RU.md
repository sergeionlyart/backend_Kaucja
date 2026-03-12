# План построения RAG-системы в духе PageIndex поверх текущего корпуса

## 1. Контекст и цель

Цель: построить поверх текущего корпуса `legal_rag_runtime` RAG-систему для юридических документов по спорам о возврате кауции, которая:

- извлекает релевантные нормы и судебные позиции без потери структуры документа;
- сохраняет точную привязку ответа к источнику;
- отдает проверяемые ссылки в формате:
  - документ-основание;
  - страница;
  - абзац или тезис;
  - переход к нужному месту в документе.

План опирается на идеи PageIndex:

- retrieval должен идти не только по сходству текста, а по структуре документа и рассуждению по дереву;
- индекс должен быть LLM-friendly: краткий, иерархический, читаемый моделью;
- retrieval должен быть traceable: каждый шаг можно связать с узлом, страницей и конкретным фрагментом;
- для длинных документов сначала подается компактное дерево, а полный текст открывается только для выбранных узлов.

Источники:

- https://pageindex.ai/research/pageindex-intro
- https://pageindex.ai/blog/claude-code-agentic-rag
- https://pageindex.ai/blog/pageindex-chat
- https://pageindex.ai/blog/technical-manuals
- https://docs.pageindex.ai/tutorials/tree-search/basic
- https://docs.pageindex.ai/tutorials/tree-search/hybrid
- https://docs.pageindex.ai/tutorials/doc-search/metadata
- https://docs.pageindex.ai/sdk/ocr

## 2. Текущая стартовая точка

По состоянию на текущую базу:

- коллекции:
  - `documents`
  - `document_sources`
  - `pages`
  - `nodes`
  - `citations`
  - `ingest_runs`
- объем:
  - `documents`: 927
  - `pages`: 3034
  - `nodes`: 6522
  - `citations`: 3647
- основа корпуса:
  - `saos_pl`: 885 документов
  - нормативка: `eli_pl`, `isap_pl`, `eurlex_eu`, `lex_pl`, `uokik_pl`
  - судебные акты: `saos_pl`, `sn_pl`, `courts_pl`, `curia_eu`

Что уже хорошо подходит под подход PageIndex:

- `documents` уже играет роль карточки документа;
- `pages` дает page-level raw content;
- `nodes` уже задает иерархические узлы с `start_index/end_index`;
- `document_sources.raw_object_path` дает путь к исходному PDF/HTML;
- `citations` уже хранит связи между актами и решениями.

Что сейчас мешает сделать полноценный reasoning-based RAG:

- один и тот же документ местами дублируется как canonical id и `urlsha:*`;
- `nodes` обычно гранулярны до статьи или секции, но не до абзаца;
- `pages` знают страницу, но не знают стабильный `paragraph_id`;
- `citations.target.anchor` часто пустой;
- для UI пока нет единого citation object, который можно сразу отдать пользователю как ссылку.

## 3. Принципы архитектуры

### 3.1. Что берем из PageIndex

Из идей PageIndex для нашего случая полезно взять следующее:

1. Не строить retrieval только на vector similarity.
2. Сделать иерархический in-context index поверх документа.
3. Искать сначала документ или ветку дерева, потом конкретный узел, потом конкретный passage.
4. Считать retrieval частью reasoning loop:
   - выбрать ветку;
   - проверить, достаточно ли контекста;
   - если нет, сделать еще один переход по дереву или по внутренней ссылке.
5. Не терять page-level traceability на каждом шаге.

### 3.2. Что не переносим буквально

Не нужно копировать PageIndex как продукт. Для нашего корпуса достаточно практичного гибрида:

- без отдельной vector DB на первом этапе;
- без сложного MCTS на старте;
- без нового формата хранения исходных документов;
- с использованием уже существующих `documents/pages/nodes/citations`.

Итоговый принцип:

> Базовый retrieval должен быть tree-first, passage-grounded и citation-safe.

## 4. Целевая архитектура

### 4.1. Слой хранения

Оставляем как source of truth:

- `documents`
- `document_sources`
- `pages`
- `nodes`
- `citations`

Добавляем материализованные служебные слои:

1. `doc_aliases`
2. `passages`
3. `retrieval_runs`
4. `answer_citations`

### 4.2. Основные компоненты

#### A. Canonical Document Resolver

Назначение:

- склеивает дубли `eli_pl:DU/2001/733` и `eli_pl:urlsha:*`;
- назначает единый `canonical_doc_id`;
- определяет предпочтительный документ для цитирования.

Правило канонизации:

- приоритет `external_ids.eli`, `external_ids.isap_wdu`, `external_ids.saos_id`, `external_ids.sn_signature`;
- если официального внешнего id нет, брать детерминированный id по нормализованному URL;
- `urlsha:*` хранить как alias, но не использовать в пользовательской ссылке.

#### B. Tree Index Builder

Назначение:

- формирует компактное LLM-friendly дерево для каждого документа;
- берет базу из `nodes`, а если `nodes` слишком грубые, достраивает подузлы.

Итоговая структура дерева для retrieval:

- document
- top-level section / article / chapter
- subsection / reasoning block
- paragraph / thesis passage

#### C. Passage Builder

Назначение:

- режет документ на стабильные passage-единицы;
- каждая passage-единица получает ссылку на:
  - документ;
  - страницу;
  - абзац;
  - node_id;
  - excerpt.

#### D. Retrieval Orchestrator

Назначение:

- исполняет multi-step retrieval по модели PageIndex:
  - metadata filter;
  - tree search;
  - node expansion;
  - passage grounding;
  - answer synthesis.

#### E. Citation Renderer

Назначение:

- преобразует внутренние `passage_id` в пользовательские ссылки;
- отдает UI-ready ссылочный объект;
- обеспечивает переход к исходнику.

## 5. Целевая модель данных

### 5.1. `doc_aliases`

Минимальная коллекция канонизации:

```json
{
  "_id": "alias:eli_pl:urlsha:8b1bb9b48a8ca9ec",
  "alias_doc_uid": "eli_pl:urlsha:8b1bb9b48a8ca9ec",
  "canonical_doc_id": "DU/2001/733",
  "canonical_doc_uid": "eli_pl:DU/2001/733",
  "reason": "same_source_hash_and_official_external_id",
  "updated_at": "2026-03-06T12:00:00Z"
}
```

### 5.2. `passages`

Ключевая коллекция для retrieval и цитирования:

```json
{
  "_id": "DU/2001/733|01bfc264...|pg:2|par:7",
  "canonical_doc_id": "DU/2001/733",
  "doc_uid": "eli_pl:DU/2001/733",
  "source_hash": "01bfc264...",
  "node_id": "art:6",
  "page_index": 1,
  "page_number": 2,
  "paragraph_index": 7,
  "paragraph_number": 8,
  "passage_type": "paragraph",
  "legal_anchor": {
    "article": "6",
    "section": "2",
    "point": null,
    "label": "art. 6 ust. 2"
  },
  "text": "Kaucja podlega zwrotowi w ciągu miesiąca...",
  "text_norm": "kaucja podlega zwrotowi w ciagu miesiaca...",
  "char_start": 1342,
  "char_end": 1498,
  "breadcrumbs": [
    "USTAWA z dnia 21 czerwca 2001 r.",
    "Art. 6"
  ],
  "source_locator": {
    "raw_object_path": "artifacts_dev/docs/eli_pl:DU/2001/733/raw/.../original.bin",
    "page_anchor": "#page=2",
    "paragraph_anchor": "pg:2-par:8"
  },
  "ingested_at": "2026-03-06T12:00:00Z"
}
```

### 5.3. `retrieval_runs`

Нужно для отладки reasoning и воспроизводимости:

```json
{
  "_id": "retrieval:run:2026-03-06T12:00:00Z:abcd",
  "query": "Czy wynajmujący może zatrzymać kaucję bez rozliczenia szkód?",
  "case_context": {
    "dispute_summary": "...",
    "user_doc_ids": ["USR:lease:1", "USR:protocol:1"]
  },
  "candidate_docs": ["DU/2001/733", "WDU19640160093", "saos_pl:330695"],
  "tree_steps": [
    {
      "doc_id": "DU/2001/733",
      "selected_node_ids": ["art:6"]
    },
    {
      "doc_id": "saos_pl:330695",
      "selected_node_ids": ["root", "reasoning:kaucja"]
    }
  ],
  "selected_passage_ids": [
    "DU/2001/733|01bfc264...|pg:2|par:7",
    "saos_pl:330695|015342b0...|pg:1|par:12"
  ],
  "created_at": "2026-03-06T12:00:00Z"
}
```

### 5.4. `answer_citations`

Хранилище уже разрешенных ссылок, которые можно безопасно рендерить:

```json
{
  "_id": "anscit:abcd:1",
  "answer_id": "answer:abcd",
  "recommendation_id": "rec_1",
  "passage_id": "DU/2001/733|01bfc264...|pg:2|par:7",
  "label": "[1]",
  "document_title": "Ustawa z dnia 21 czerwca 2001 r.",
  "document_short": "Ustawa o ochronie praw lokatorów",
  "page_number": 2,
  "paragraph_number": 8,
  "legal_anchor_label": "art. 6 ust. 2",
  "excerpt": "Kaucja podlega zwrotowi w ciągu miesiąca...",
  "open_target": {
    "doc_uid": "eli_pl:DU/2001/733",
    "source_hash": "01bfc264...",
    "page_index": 1,
    "paragraph_index": 7
  }
}
```

## 6. Как строить passages и anchors

### 6.1. Для PDF-нормативки

Источник:

- `pages.text`
- `nodes`
- `document_sources.raw_object_path`

Правило разметки:

1. Взять диапазон страниц узла `node.start_index..node.end_index`.
2. На каждой странице выполнить нормализацию переносов:
   - склеить переносы слов;
   - сохранить оригинальный текст отдельно;
   - не удалять цифры, маркеры и ссылки.
3. Резать на абзацы по шаблонам:
   - `^Art\.`
   - `^\d+\.`
   - `^\d+\)`
   - пустая строка
   - явный markdown/html block, если есть OCR markdown
4. Для каждого абзаца вычислить:
   - `paragraph_index`
   - `char_start/char_end`
   - `legal_anchor`
   - `node_id`
   - `page_number`

Для актов типа `DU/2001/733` это даст ссылку вида:

- документ: закон о защите прав локаторов;
- страница: 2;
- абзац: 8;
- тезис: `art. 6 ust. 2`.

### 6.2. Для SAOS, SN HTML, EUR-Lex HTML, UOKiK HTML

Источник:

- `pages.text`, где уже встречаются `<p>`, `<h2>`, `<li>`, `<table>`

Правило разметки:

1. Если есть HTML-подобная структура, резать по `<p>`, `<li>`, `<h2>`, `<h3>`.
2. Если passage слишком длинный, разрешить вторичное деление по предложениям или логическим блокам.
3. Для судебных актов отдельно помечать:
   - вводная часть;
   - факты;
   - мотивировка;
   - вывод суда.

### 6.3. Для пользовательских документов

Для user docs делать такой же passage-layer, но хранить отдельно:

- `user_passages`

Поля те же, плюс:

- `run_id`
- `session_id`
- `user_doc_id`
- путь к OCR markdown и page render.

Это позволит ссылаться в рекомендациях и на документы пользователя по той же схеме.

## 7. Retrieval-поток

### 7.1. Общая схема

```text
Запрос пользователя
-> нормализация intent и facts
-> metadata/doc filter
-> tree search по shortlist документов
-> раскрытие выбранных node_id
-> passage grounding
-> synthesis only from selected passages
-> citation rendering
```

### 7.2. Этап 1. Metadata filter

Сначала не нужно открывать весь корпус.

Нужно отбирать документы по жестким признакам:

- юрисдикция;
- тип документа;
- источник;
- наличие официального id;
- тематические метки: `kaucja`, `najem`, `lokator`, `potrącenie`, `przedawnienie`, `waloryzacja`.

Практически:

- использовать `documents`, `external_ids`, `doc_type`, `source_system`;
- завести дополнительное поле `topic_tags`;
- для legal corpus применять strategy наподобие PageIndex metadata search:
  - сначала документный shortlist;
  - потом внутридокументный retrieval.

### 7.3. Этап 2. Tree search

На вход LLM подается не текст целиком, а компактное дерево:

- `title`
- `node_id`
- `start_index/end_index`
- `summary`
- `anchors`
- `topic_tags`

Минимальный prompt-контракт:

- вопрос;
- краткий case summary;
- список shortlist документов;
- tree fragment;
- ответ в JSON:
  - reasoning
  - selected_node_ids
  - why
  - need_more_context

Это почти прямой перенос идеи PageIndex tree search.

### 7.4. Этап 3. Multi-hop expansion

Если из выбранного node видно, что он ссылается на другой акт или на другую часть документа, retrieval делает еще один шаг:

- из SAOS решения -> к cited statute;
- из статьи закона -> к связанной статье или к SN/SAOS case law;
- из пользовательского договора -> к норме закона и судебной практике.

Тут используем:

- `citations`
- `nodes`
- `doc_aliases`

Критически важно:

- LLM не получает право открывать произвольный документ;
- она работает только с whitelist кандидатов, отобранных orchestrator.

### 7.5. Этап 4. Passage grounding

После выбора узлов orchestrator сам раскрывает passages и отдает модели только:

- `passage_id`
- заголовок документа;
- page/paragraph label;
- краткий excerpt;
- при необходимости full passage text.

Именно на этом этапе закрепляется source binding.

### 7.6. Этап 5. Answer synthesis

Модель должна возвращать structured output:

```json
{
  "recommendations": [
    {
      "id": "rec_1",
      "text": "Wynajmujący powinien zwrócić kaucję w ciągu miesiąca...",
      "source_ref_ids": [
        "DU/2001/733|01bfc264...|pg:2|par:7",
        "saos_pl:330695|015342b0...|pg:1|par:12"
      ],
      "confidence": "high"
    }
  ]
}
```

Модель не должна сама придумывать страницы и абзацы. Она выбирает только из уже переданных `source_ref_ids`.

## 8. Схема цитирования и якорей

### 8.1. Внутренний формат ссылки

Внутренний citation key:

```text
{canonical_doc_id}|{source_hash}|pg:{page_number}|par:{paragraph_number}
```

Пример:

```text
DU/2001/733|01bfc264...|pg:2|par:8
```

### 8.2. Пользовательский формат ссылки

В тексте рекомендации:

```text
Wynajmujący ma obowiązek rozliczyć i zwrócić kaucję w terminie miesiąca od opróżnienia lokalu [1].
```

Карточка ссылки `[1]`:

- документ: `Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorów`
- страница: `2`
- абзац: `8`
- тезис: `art. 6 ust. 2`
- excerpt: `Kaucja podlega zwrotowi w ciągu miesiąca...`

### 8.3. Формат для UI / API

```json
{
  "label": "[1]",
  "document_title": "Ustawa z dnia 21 czerwca 2001 r. o ochronie praw lokatorów",
  "page_number": 2,
  "paragraph_number": 8,
  "legal_anchor_label": "art. 6 ust. 2",
  "excerpt": "Kaucja podlega zwrotowi w ciągu miesiąca...",
  "jump_target": {
    "doc_uid": "eli_pl:DU/2001/733",
    "source_hash": "01bfc264...",
    "page_index": 1,
    "paragraph_index": 7
  }
}
```

### 8.4. Переход по ссылке

Для PDF:

- открыть `document_sources.raw_object_path`;
- перейти на страницу через `#page=N`;
- внутри viewer подсветить `paragraph_index` по заранее сохраненным offsets.

Для HTML/SAOS:

- открыть pre-rendered HTML/markdown view;
- скроллить к `paragraph_anchor`.

Для локального приложения удобен универсальный deep link:

```text
/source-jump?doc_uid=eli_pl:DU/2001/733&source_hash=01bfc264...&page=2&paragraph=8
```

## 9. Индексация и хранение

### 9.1. Что индексировать

Нужно индексировать не raw chunks, а три уровня:

1. document-level
2. node-level
3. passage-level

Document-level индекс:

- `canonical_doc_id`
- `doc_type`
- `source_system`
- `jurisdiction`
- `topic_tags`
- `official_priority`

Node-level индекс:

- `node_id`
- `title`
- `summary`
- `start_index/end_index`
- `anchors.article`
- `anchors.chapter`
- `topic_tags`

Passage-level индекс:

- `text_norm`
- `page_number`
- `paragraph_number`
- `legal_anchor_label`
- `node_id`

### 9.2. Какие индексы БД добавить

Для Mongo:

`doc_aliases`

- `{ alias_doc_uid: 1 }` unique
- `{ canonical_doc_id: 1 }`

`passages`

- `{ canonical_doc_id: 1, source_hash: 1, page_index: 1, paragraph_index: 1 }` unique
- `{ doc_uid: 1, node_id: 1 }`
- `{ "legal_anchor.article": 1 }`
- text index по `text_norm`, `breadcrumbs`, `legal_anchor.label`

`retrieval_runs`

- `{ created_at: -1 }`
- `{ "case_context.session_id": 1, created_at: -1 }`

`answer_citations`

- `{ answer_id: 1, recommendation_id: 1 }`

### 9.3. Где хранить дерево для LLM

Не нужно каждый раз собирать дерево на лету из `nodes`.

Практичный вариант:

- materialized JSON tree в `documents.pageindex_tree_v2`;
- при больших документах дополнительно хранить:
  - `tree_levels.top`
  - `tree_levels.expanded`

Это позволит:

- быстро отдавать top-level tree в prompt;
- раскрывать только нужные ветки по `node_id`.

## 10. Рекомендуемый retrieval strategy

### Фаза A. MVP без vector DB

Использовать:

- metadata filter
- tree search по summaries
- passage grounding по `passages`
- simple lexical fallback

Это уже даст:

- точные ссылки;
- объяснимый retrieval;
- отсутствие потери связи с источником.

### Фаза B. Hybrid node scoring

Если corpus вырастет, добавить PageIndex-style hybrid tree search:

- embeddings использовать только для node scoring;
- retrieval возвращает не chunk, а node;
- финальный grounding все равно делается только через `passages`.

Это важно: embedding не должен становиться source of truth.

### Фаза C. Domain preferences

Для нашего домена добавить expert rules в tree search prompt:

- если вопрос про возврат кауции -> приоритет `art. 6`, `art. 36`, `art. 678`, `art. 118`;
- если вопрос про potrącenie -> приоритет case law и passages с `potrącenie`, `rozliczenie`, `wierzytelność`;
- если вопрос про смену собственника -> приоритет `art. 678 k.c.` и SN/SAOS решения по legitymacja bierna.

Это полностью согласуется с идеей PageIndex о preference-aware tree search.

## 11. План внедрения

### Этап 1. Канонизация и anchors

Сделать:

1. `doc_aliases`
2. builder `passages`
3. правила `legal_anchor`
4. deep-link format

Результат:

- можно строить цитаты документ + страница + абзац.

### Этап 2. Retrieval API v1

Сделать:

1. metadata shortlist
2. tree payload generator
3. node selection prompt
4. passage grounding

Результат:

- tree-first retrieval без vector DB.

### Этап 3. Answer generation с безопасными citation ids

Сделать:

1. JSON schema для ответа модели;
2. `source_ref_ids` только из whitelist;
3. post-processor `answer_citations`.

Результат:

- модель перестает выдумывать ссылки.

### Этап 4. UI переходы к источнику

Сделать:

1. citation popover;
2. jump to page/paragraph;
3. preview excerpt;
4. открытие исходного PDF/HTML.

Результат:

- пользователь получает проверяемый, навигируемый ответ.

### Этап 5. Hybrid optimization

Сделать позже:

1. node scoring model;
2. hybrid tree search;
3. retrieval benchmark по кейсам из `docs/legal/kaucja_registry.csv`.

## 12. Критерии готовности

Система считается готовой к первому рабочему запуску, когда:

1. Для каждого ответа каждая рекомендация имеет не меньше одной валидной citation link.
2. Каждая citation link раскрывается в:
   - документ;
   - страница;
   - абзац;
   - excerpt.
3. Клик по ссылке открывает исходный документ в нужном месте.
4. Retrieval логируется и воспроизводим.
5. Дубликаты документов не попадают к пользователю как разные источники.
6. Ответ строится только из passages, реально выбранных orchestrator.

## 13. Главное решение

Для нашего корпуса лучший практический вариант — не строить классический chunk+embedding RAG, а построить PageIndex-подобный слой поверх уже существующих:

- `documents` как doc-level metadata;
- `nodes` как skeleton дерева;
- `pages` как raw source;
- новый `passages` как точный слой цитирования;
- retrieval как `metadata -> tree -> node -> passage -> answer`.

Это даст:

- устойчивую привязку к источнику;
- объяснимый retrieval;
- точные page/paragraph citations;
- минимальный объем миграций относительно текущей базы.
