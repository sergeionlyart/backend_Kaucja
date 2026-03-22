# Аудит документации и принятые решения

## 1. Краткий вывод

Исходный комплект документации качественный как архитектурный foundation, но в текущем виде недостаточно полон для устойчивого старта разработки без дополнительных решений.

База сильная:
- есть подробное ТЗ;
- есть практическая спецификация Mongo search tools;
- есть системные prompt-файлы для большинства ролей;
- есть понятные границы scope.

Но перед стартом нужно зафиксировать несколько решений и закрыть несколько пробелов.

## 2. Выявленные проблемы

### 2.1. Отсутствует prompt для `LegalResearchAgent`
В `README.md` и в ТЗ агент предусмотрен, но в папке отсутствует отдельный файл системной инструкции для него.

Решение:
- добавить `system_prompt_legal_research_agent.txt`;
- использовать его как нормативный prompt для research-шага.

### 2.2. Несогласованность в именовании prompt-ов и путей
Сейчас одновременно встречаются:
- `kaucja_case_intake_agent`
- `legal_case_intake`
- `strategic_memo_writer`
- `kaucja_memo_writer_agent`
- плоские файлы `system_prompt_*.txt`

Также часть имён файлов с кириллицей в архиве выглядит как escaped Unicode sequences, что плохо для практического использования.

Решение:
- принять единый набор путей:
  - `app/prompts/kaucja_anchor_markdown/v001/system_prompt.txt`
  - `app/prompts/kaucja_case_intake_agent/v001/system_prompt.txt`
  - `app/prompts/kaucja_legal_research_agent/v001/system_prompt.txt`
  - `app/prompts/kaucja_memo_writer_agent/v001/system_prompt.txt`
  - `app/prompts/kaucja_citation_qc_agent/v001/system_prompt.txt`
  - `app/prompts/kaucja_main_pipeline_agent/v001/system_prompt.txt` — optional
- внутри `docs/Tech_Spec_Agents_Legal` хранить только ASCII-стабильные filenames.

### 2.3. Противоречие по архитектуре верхнеуровневого агента
`system_prompt_agent.txt` описывает top-level agent, который может вызывать specialist agents.
Но ТЗ в разделе про Agents SDK рекомендует последовательную Python-оркестрацию без сложных handoff chains.

Решение:
- для v1 нормативным считается вариант с последовательной Python-оркестрацией;
- `system_prompt_agent.txt` считать optional/legacy document для будущего orchestration-layer;
- запуск v1 делать без отдельного main agent.

### 2.4. QC-agent есть в prompts, но отсутствует формализация модели `MemoQcReport`
В папке есть `system_prompt_citation_QC.txt`, но нет формализованной модели его результата.

Решение:
- ввести `MemoQcReport` как обязательную Pydantic-модель;
- использовать QC как отдельный пост-шаг после MemoWriter.

### 2.5. Нет практического документа по врезке набора в репозиторий
Документация описывает архитектуру, но не фиксирует точный следующий шаг: какие файлы куда положить и что создать в коде первым.

Решение:
- добавить отдельный документ `04_REPOSITORY_WIRING_AND_NEXT_STEP.md`;
- положить рядом blueprint Pydantic-моделей.

### 2.6. Неполная формализация alias-логики
Документация вводит `L01`, `U01`, но недостаточно ясно фиксирует:
- кто и когда присваивает alias;
- как обеспечивается стабильность `Uxx`;
- какой объект считается источником истины для alias register.

Решение:
- ввести отдельные правила alias assignment;
- для `Uxx` использовать deterministic builder;
- для `Lxx` считать источником истины `ResearchBundle.legal_authorities`.

### 2.7. Расхождение между tool spec и Python blueprint
В `legal_search_tool_spec.md` сказано, что tools должны всегда возвращать `budget_remaining`.
Но в текущем `legal_search_tools.py` у `get_anchor_details` поля `budget_remaining` нет.

Решение:
- нормализовать контракты трёх tools;
- для простоты v1 вернуть `budget_remaining` во всех трёх инструментах.

### 2.8. README обещает versioned prompt-layout, но docs-папка содержит только flat files
Это создаёт ложное впечатление, что комплект уже готов к прямой вставке в код.

Решение:
- добавить wiring-document с mapping из flat docs в реальные repo paths;
- не считать docs-папку напрямую runnable bundle без этого шага.

## 3. Итоговое решение по готовности

До внесения дополнений документации недостаточно для безопасного handoff программисту.
После применения supplement-пакета документация становится достаточной для старта разработки первого рабочего спринта.
