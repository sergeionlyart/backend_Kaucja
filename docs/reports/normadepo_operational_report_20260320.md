# NormaDepo Operational Report

Дата: 2026-03-20

## 1. Что это за скрипт

Основной entrypoint pipeline:

- `scripts/annotate_legal_docs.py`

Это локальный синхронный CLI-скрипт для пакетной обработки markdown-корпуса юридических документов и сохранения результата в MongoDB.

Целевой корпус:

- `docs/legal/cas_law_v2_2_md`

Основной runtime-пакет:

- `legal_docs_pipeline`

## 2. Функциональные особенности

Pipeline делает следующее:

1. Рекурсивно сканирует `*.md` в детерминированном порядке.
2. Для каждого файла создаёт или обновляет Mongo-документ по правилу `_id == relative_path`.
3. Читает markdown, нормализует текст, извлекает metadata/content.
4. Определяет язык и классифицирует документ rule-based router-ом с LLM fallback только при необходимости.
5. Для annotatable-документов выполняет два отдельных LLM-вызова:
   - `annotate_original`
   - `annotate_ru`
6. Валидирует structured output.
7. Сохраняет source, classification, annotation, llm metadata, processing state и search-поля в MongoDB.
8. Поддерживает безопасные режимы `new`, `full`, `rerun`.
9. Сохраняет partial progress и умеет резюмировать перевод через rerun.

## 3. Архитектурные особенности

Архитектура разделена по явным слоям:

- `legal_docs_pipeline/scanner.py` — discovery
- `legal_docs_pipeline/reader.py` — чтение и soft normalization
- `legal_docs_pipeline/parser.py` — разбор markdown container
- `legal_docs_pipeline/language.py` — heuristics language detection
- `legal_docs_pipeline/router.py` — rule-based routing
- `legal_docs_pipeline/prompts.py` — external prompt-pack resolution and hashes
- `legal_docs_pipeline/llm.py` — OpenAI Responses API integration
- `legal_docs_pipeline/repository.py` — Mongo persistence and index management
- `legal_docs_pipeline/pipeline.py` — orchestration, rerun semantics, logging
- `legal_docs_pipeline/logging.py` — JSONL event log

Ключевые архитектурные свойства:

- sequential runtime, `workers=1`
- one file = one Mongo document
- upsert semantics instead of insert-only
- external prompt pack instead of hardcoded prompts
- two-call annotation architecture
- reproducibility fields: prompt hash, request hash, schema version, pipeline version
- partial success semantics: analysis может сохраниться даже если перевод упал

## 4. Ветка во внешнем репозитории

Внешний репозиторий:

- `origin = https://github.com/sergeionlyart/backend_Kaucja.git`

Состояние по веткам:

- текущий локальный checkout находится на ветке `lab-kaucja-annotation-pipeline`
- такой remote branch на `origin` сейчас отсутствует
- зафиксированная реализация pipeline во внешнем репозитории находится в ветке `main`

Практически это означает:

- baseline-версия скрипта присутствует во внешнем репозитории в `origin/main`
- часть текущих эксплуатационных диагностик и локальных наблюдений относится к локальной рабочей ветке `lab-kaucja-annotation-pipeline`

## 5. С какими проблемами столкнулись при эксплуатации

### 5.1 Oversized corpus file

Файл:

- `eu_acts/29_eu_eurlex_eli_reg_2006_1896_oj_eng.md`

Проблема:

- размер файла превышает configured ingest limit `16 MB`
- он был исключён из controlled `run1` staging corpus

Вывод:

- для первого прогона пришлось использовать staging root на `54` документа вместо `55`

### 5.2 Нестабильность live LLM behavior

Во время controlled probe наблюдался сбой:

- `annotate_ru` вернул `llm_incomplete`

Проблема:

- первый live probe дал provider-side incomplete result
- повторный isolated rerun этого же stage завершился успешно

Вывод:

- баг не подтвердился как детерминированно воспроизводимый
- он выглядит как нестабильный runtime/provider-side сбой

### 5.3 Недостаточная диагностика incomplete-ответов

Изначально pipeline терял причину incomplete-состояния.

Проблема:

- SDK даёт `response.incomplete_details.reason`
- pipeline сохранял только общий `llm_incomplete`

Что было сделано:

- diagnostic layer был расширен
- теперь сохраняются `response_id`, `status`, `usage`, `incomplete_details.reason`

### 5.4 Business validation failures на analysis stage

Во время `run1` два документа завершились `failed` уже на `annotate_original`:

- `eu_acts/26_eu_eurlex_31993l0013_en_html.md`
- `eu_acts/27_eu_eurlex_52019xc0927_01.md`

Причина:

- `llm_schema_validation_error`
- точное сообщение pipeline: `Analysis response failed business validation.`

Вывод:

- даже при технически успешном LLM-ответе pipeline может отвергать output по бизнес-правилам

### 5.5 Критическая проблема MongoDB document size

Это главный эксплуатационный блокер batch-run.

Симптом:

- batch завершился с ошибкой `update command document too large`

Документ, на котором это произошло:

- `eu_acts/28_eu_eurlex_eli_reg_2007_861_oj_eng.md`

Факты:

- `source.size_bytes = 7,997,964`
- в Mongo уже успели сохраниться:
  - `raw_markdown` около `7,997,833` символов
  - `normalized_text` около `7,980,041` символов

Почему это произошло:

- pipeline хранит внутри одного Mongo-документа крупные текстовые поля
- следующий update после read-stage довёл BSON payload до лимита MongoDB

Вывод:

- текущая схема хранения неустойчива для больших markdown-документов
- проблема уже не в OpenAI и не в timeout, а в размере самого Mongo-документа

## 6. Состояние product run на момент отчёта

Целевая коллекция:

- `kaucja_legal_corpus.documents_cas_law_v2_2_run1`

Итог batch-run:

- процесс завершился аварийно
- коллекция создана, но неполная и не пригодна как продуктовая baseline collection

Состояние коллекции на момент фиксации:

- `completed`: 1
- `failed`: 2
- `read`: 1
- `skipped_non_target`: 1

Корректно завершённый документ:

- `eu_acts/25_eu_eurlex_eli_dir_1993_13_oj_eng.md`

У него подтверждено наличие релевантных блоков:

- `classification`
- `annotation.original`
- `annotation.ru`
- `llm.analysis`
- `llm.translation_ru`
- `processing`
- `search.tags_original`
- `search.tags_ru`

## 7. Общий вывод

Скрипт функционально и архитектурно уже является рабочим foundation pipeline:

- он умеет читать corpus
- классифицировать документы
- выполнять двухшаговую аннотацию
- сохранять structured results в MongoDB
- вести idempotent/partial-aware processing

Но в текущем эксплуатационном состоянии pipeline нельзя считать готовым к полному продуктовому прогону всего `run1`, потому что:

1. есть нестабильные LLM-side сбои типа `llm_incomplete`
2. есть business validation failures на части документов
3. есть критический архитектурный блокер по размеру Mongo-документа для крупных файлов

Главный текущий blocker:

- модель хранения больших markdown-документов в одном Mongo record упирается в BSON size limit
