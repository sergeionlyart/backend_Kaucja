# Workflow: versioning system prompt + schema

## Когда использовать
- Изменения в system prompt или JSON schema.

## Правила
- Единица версионирования = папка `prompts/<prompt_name>/vNNN/` с:
  - `system_prompt.txt`
  - `schema.json`
  - `meta.yaml` (changelog)

## Шаги
1) Создать новую версию (vNNN+1), не менять старую.
2) Прогнать один и тот же набор документов на старой и новой версии.
3) Сравнить:
- валидность JSON,
- gaps,
- стоимость/тайминги.
4) Зафиксировать выводы в `meta.yaml`.

