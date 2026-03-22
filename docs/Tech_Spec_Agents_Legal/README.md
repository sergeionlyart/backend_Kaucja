# Kaucja prompt & tooling bundle

Этот bundle подготовлен под текущую структуру репозитория `backend_Kaucja` и повторяет его versioned prompt-layout:

- `app/prompts/<prompt_name>/v001/system_prompt.txt`
- `app/prompts/<prompt_name>/v001/schema.json`
- `app/prompts/<prompt_name>/v001/meta.yaml`

## Что входит

### Промпты
- `kaucja_anchor_markdown` — plain-text prompt для LLM-якоризации Markdown
- `kaucja_main_pipeline_agent` — системная инструкция для верхнеуровневого агентного контура
- `kaucja_case_intake_agent` — facts/issues extraction
- `kaucja_legal_research_agent` — legal retrieval через local tools
- `kaucja_memo_writer_agent` — генерация стратегического меморандума
- `kaucja_citation_qc_agent` — проверка integrity и groundedness ссылок

### Tooling
- `docs/tooling/legal_search_tool_spec.md` — практическая спецификация поискового инструмента
- `app/agents/tools/legal_search_tools.py` — Python blueprint function tools для OpenAI Agents SDK

## Важное замечание
В текущем репозитории `app/prompts/manager.py` ожидает наличие `schema.json` даже для plain-text prompt.
Поэтому у `kaucja_anchor_markdown` положен пустой `schema.json` (`{}`), а `meta.yaml` содержит `response_mode: plain_text`.

## Рекомендуемое использование
1. Для anchorization грузить только `system_prompt.txt` и запускать LLM в plain-text режиме.
2. Для агентов с structured output использовать `system_prompt.txt` + соответствующий `schema.json` или эквивалентный `output_type` в OpenAI Agents SDK.
3. Для legal retrieval использовать `legal_search_tools.py` как основу function tools и ограничивать search budget через run context.
