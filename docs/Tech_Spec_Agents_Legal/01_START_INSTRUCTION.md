# Стартовая инструкция

## Как читать документацию

Перед началом разработки изучать документы в таком порядке:
1. `00_PROJECT_PREAMBLE.md`
2. `03_DOC_AUDIT_AND_DECISIONS.md`
3. `kaucja_detailed_tz_anchor_memo_pipeline_20260322.md`
4. `legal_search_tool_spec.md`
5. `04_REPOSITORY_WIRING_AND_NEXT_STEP.md`
6. `05_PYDANTIC_MODELS_SPEC.md`
7. prompt-файлы

## Нормативные решения для старта

На старте принять как обязательные следующие решения:
- рабочая схема оркестрации — последовательная Python-оркестрация, а не автономный multi-agent loop;
- `system_prompt_agent.txt` считать опциональным документом для будущего orchestration-agent, но не базовым способом запуска v1;
- в v1 запускать напрямую три основных агента и отдельный QC-шаг;
- prompt-файлы хранить в репозитории по stable ASCII paths;
- agent prompts не тащить через текущий `app/prompts/manager.py`; для них нужен отдельный лёгкий loader;
- output каждого агентного шага валидировать через Pydantic `output_type` и пост-валидацию.

## Первая итерация разработки

Первый практический спринт должен закрыть только базовый вертикальный срез:
1. добавить prompts в репозиторий;
2. добавить `app/legal_memo/models.py`;
3. добавить thin prompt loader;
4. добавить `legal_search_tools` в рабочий пакет, не только в docs;
5. собрать `CaseIntakeAgent` -> `LegalResearchAgent` -> `MemoWriterAgent` -> `CitationQCAgent`;
6. провести smoke-тест на 2–5 пользовательских документах и малом preindexed legal corpus.

## Что не делать в первом спринте

Не добавлять до первого рабочего прогона:
- frontend и кликабельные ссылки;
- embeddings/vector DB;
- сложные handoffs;
- произвольные агенты-оркестраторы;
- переписывание существующего `PromptManager`.

## Definition of Done для старта проекта

Старт разработки считается успешным, если в репозитории появились:
- новые prompts по согласованным путям;
- Pydantic-модели output-типа;
- рабочие Mongo search tools;
- минимальный entrypoint онлайн-контура;
- unit tests на модели и search tools.
