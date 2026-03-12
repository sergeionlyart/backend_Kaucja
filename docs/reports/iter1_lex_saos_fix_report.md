# Iteration 1 Report: LEX and SAOS Data Ingestion Fix

- **Run ID (Failed)**: `bd38d9f842704b698f6883ca44874553`
- **Run ID (Success)**: `eaf9d072e15c4213b8cc37838befd626`

## Различия между прогонами
- **Прогон `bd38d9f842704b698f6883ca44874553`** завершился ошибкой для LEX ссылок, так как MIME-тип извлекался как `application/json`, однако контент перехватывался и возвращался как HTML, что ломало пайплайн на этапе парсинга (`ValueError: Unsupported MIME type: application/json`).
- **Прогон `eaf9d072e15c4213b8cc37838befd626`** успешен, так как в адаптере LEX мы подменили заголовок `content-type` на `text/html; charset=utf-8` после успешного извлечения `content` из JSON-ответа `apimobile`. Это позволило штатному HTML-парсеру обработать извлечённый контент.

## Метрики успешного прогона (`eaf9d072e15c4213b8cc37838befd626`)
- `sources_total`: 50
- `docs_ok`: 4
- `docs_restricted`: 1
- `docs_error`: 0
- `pages_written`: 6
- `nodes_written`: 9
- `citations_written`: 4

## Распределение и проверка по поднабору
Мы проверили выборку из 5 целевых документов пайплайна (`#3`, `#4`, `#5`, `#11`, `#12`). 
- **`#3` (lex_test_3)**: Успешно извлеклось полное постановление как `STATUTE`. 
- **`#4` (lex_test_4)**: Успешно извлечена конкретная "единица" (nested unitId) Постановления `art-19-a`.
- **`#5` (lex_test_5)**: Отмечено как `RESTRICTED` из-за низкого объёма символов (< 500) сработавшего на HTML эвристике (вероятный невидимый paywall). Дашборд корректно обработал статус.
- **`#11` (saos_search_test_11_535713 / saos_search_test_11_521555)**: Использован fallback-запрос со стороны HTML для SAOS поиска — корректно прошла пагинация `all="test"`, извлечены все идентификаторы и загружены соответствующие судебные решения в штатный `fetch_saos_judgment`.
*(Для `#12` лимит списка сработал на процессе expand - в логах первые 5 позиций были покрыты #3, #4, #5, #11(535713), #11(521555)).*

## Артефакты
- [Run Report](/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter1/runs/eaf9d072e15c4213b8cc37838befd626/run_report.json)
- [Logs](/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter1/runs/eaf9d072e15c4213b8cc37838befd626/logs.jsonl)
- [Source Status](/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter1/source_status.json)
- [Walkthrough Report](/Users/sergejavdejcik/.gemini/antigravity/brain/6c4b3e42-b8e9-4565-bb2f-69a4d30d1955/walkthrough.md)
