# Iteration 2: Proof of Coverage for LEX & SAOS Fallback Ingestion

## Цель прогона
Обеспечить доказательную базу пайплайна для целевых юридических документов: `#3`, `#4`, `#5`, `#11`, `#12` из списка `cas_law_V_2.2 2.md`. Запуск производился без ограничений (`limit=None`), чтобы полностью развернуть параметры поиска SAOS (#11) и загрузить все судебные рішення, а также корректно дойти до `#12`.

## Результаты прогона (Детерминированный Run ID: `iter2_run_deterministic`)
Всего `run_pipeline` инжестировал **50 документов**, покрыв все запланированные источники:

### Successfully Loaded (Status: `OK`)
- **#3 (`lex_test_3`)**: URL `https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658` — Успешно извлечён через прямое подключение к apimobile endpoints и обработан как HTML-контент.
- **#4 (`lex_test_4`)**: URL `https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/ochrona-praw-lokatorow-mieszkaniowy-zasob-gminy-i-zmiana-kodeksu-16903658/art-19-a` — Успешно извлечена конкретная единица через apimobile `unitId`.
- **#11 (`saos_search_test_11_XXXXXX`)**: URL `https://www.saos.org.pl/` — Поисковый запрос `courtCriteria.courtType=COMMON&keywords=kaucja+mieszkaniowa` успешно развернулся в 46 дел. Из-за добавленной логики защиты от таймаутов `tenacity @retry` все документы были успешно скачаны, распарсены и обработаны пайплайном в штатном режиме.
- **#12 (`saos_judg_test_12`)**: URL `https://www.saos.org.pl/judgments/171957` — Успешно извлечено напрямую через SAOS Judgment API/Fallback HTML без обрывов пайплайна.

### Not Loaded (Status: `RESTRICTED` or `ERROR`)
- **#5 (`lex_test_5`)**: URL `https://sip.lex.pl/akty-prawne/dzu-dziennik-ustaw/kodeks-cywilny-16785996/art-118` — Status: `RESTRICTED`. Причина: `Restricted content detected via heuristics (e.g. low char count / paywall)`. Пайплайн успешно отловил невидимый пейволл и отметил документ корректным статусом без падений.

## Абсолютные пути к артефактам
Все данные по запуску зафиксированы в репозитории:
- **Run Report**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter2/runs/iter2_run_deterministic/run_report.json`
- **Logs**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/artifacts_iter2/runs/iter2_run_deterministic/logs.jsonl`
- **Source Status Mapping JSON**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter2_source_status.json`
- **Coverage Report Markdown**: `/Users/sergejavdejcik/Library/Mobile Documents/com~apple~CloudDocs/2026_1/backend_Kaucja-labs/2026-03-01__legaldocs_ingest__foundation/docs/reports/iter2_subset_coverage.md`

## Git State
- **Branch**: `exp/iter1-lex-saos-fixes`
- **Commit**: `c3039b614a864321e8d655886551ca0b32b911c5`

## Verification
```
docs/reports/iter2_source_status.json
docs/reports/iter2_subset_coverage.md
```
