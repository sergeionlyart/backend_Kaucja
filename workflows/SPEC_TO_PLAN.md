# Workflow: TechSpec → план работ

## Когда использовать
- Перед началом любой существенной фичи/эпика.

## Шаги
1) Найти в `docs/TECH_SPEC_MVP.md`:
   - In-scope / Out-of-scope
   - контракты данных (OCRResult/LLMResult/RunConfig)
   - файловую структуру артефактов
   - DoD и error taxonomy

2) Сформулировать **acceptance criteria**:
   - 5–10 буллетов, проверяемых.

3) Выделить минимальный «вертикальный срез»:
   - UI → pipeline → storage → artifacts → validation.

4) Разрезать по модулям:
   - ocr_client
   - llm_client
   - storage
   - pipeline
   - ui

5) Для каждого модуля:
   - список файлов,
   - публичные функции/контракты,
   - тест-стратегия.

## Выход (в PR/issue)
- План (3–8 шагов)
- Файлы
- Риски
- Как тестировать

