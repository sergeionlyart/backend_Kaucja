# Workflow: реализация feature-slice

## Цель
Сделать маленький PR, который добавляет одну проверяемую единицу функциональности.

## Шаги
1) Plan:
- что добавляем,
- какие файлы меняем,
- какие тесты добавляем.

2) Implement:
- сначала типы/контракты,
- затем реализация,
- затем интеграция.

3) Tests:
- unit: чистые функции (packer, validators, cost)
- integration: orchestrator step with fakes/mocks

4) Verify:
- ruff format/check
- pytest

5) Report:
- Summary
- Files changed
- Commands run
- Follow-ups

