# Следующий практический шаг: врезка набора в репозиторий и добавление Pydantic-моделей

## 1. Цель этого шага

Сделать документацию не только концептом, но и прямой точкой входа в реализацию.

## 2. Что нужно сделать первым коммитом

### 2.1. Добавить prompts в рабочие пути репозитория
Создать в репозитории следующие директории и положить туда системные инструкции:

```text
app/prompts/kaucja_anchor_markdown/v001/system_prompt.txt
app/prompts/kaucja_case_intake_agent/v001/system_prompt.txt
app/prompts/kaucja_legal_research_agent/v001/system_prompt.txt
app/prompts/kaucja_memo_writer_agent/v001/system_prompt.txt
app/prompts/kaucja_citation_qc_agent/v001/system_prompt.txt
app/prompts/kaucja_main_pipeline_agent/v001/system_prompt.txt   # optional
```

Для structured agents рядом должны лежать:
```text
schema.json
meta.yaml
```

Для `kaucja_anchor_markdown` допускается `response_mode: plain_text` и минимальный `schema.json` вида `{}`.

### 2.2. Добавить новый пакет `app/legal_memo/`
Создать минимум такие файлы:

```text
app/legal_memo/__init__.py
app/legal_memo/models.py
app/legal_memo/prompt_loader.py
app/legal_memo/case_intake_agent.py
app/legal_memo/legal_research_agent.py
app/legal_memo/memo_writer_agent.py
app/legal_memo/citation_qc_agent.py
app/legal_memo/service.py
app/legal_memo/renderer.py
app/legal_memo/validators.py
app/legal_memo/mongo_search_tools.py
```

### 2.3. Добавить Pydantic-модели
В `app/legal_memo/models.py` добавить:
- `CaseIssueSheet`
- `ResearchBundle`
- `StrategicMemo`
- `MemoQcReport`

Рядом в supplement приложен blueprint-файл `app/legal_memo/models_blueprint.py`, который можно использовать как стартовую основу.

### 2.4. Подключить `output_type`
Каждый агент должен создаваться как минимум в таком стиле:

```python
Agent(..., output_type=CaseIssueSheet)
Agent(..., output_type=ResearchBundle)
Agent(..., output_type=StrategicMemo)
Agent(..., output_type=MemoQcReport)
```

Именно это и есть следующий практический шаг, который нужен, чтобы агентный контур можно было запускать как типизированный pipeline, а не как набор необязательных JSON-договорённостей.

## 3. Что делать со старым PromptManager

В v1 не пытаться встроить новый агентный контур в текущий `app/prompts/manager.py`.
Нужен отдельный `prompt_loader.py`, который:
- читает `system_prompt.txt` как plain text;
- при необходимости рядом читает `schema.json` и `meta.yaml`;
- не зависит от legacy assumptions текущего PromptManager.

## 4. Что сделать вторым коммитом

### 4.1. Добавить tools в рабочий пакет
Файл `legal_search_tools.py`, который пока лежит в docs, нужно перенести в кодовую базу как рабочий модуль:

```text
app/legal_memo/mongo_search_tools.py
```

### 4.2. Нормализовать контракт tools
У всех трёх tools унифицировать поля ответа:
- `status`
- `warnings`
- `budget_remaining`
- payload (`hits` или `items`)

### 4.3. Добавить тесты
Минимум:
```text
tests/legal_memo/test_models.py
tests/legal_memo/test_prompt_loader.py
tests/legal_memo/test_mongo_search_tools.py
```

## 5. Что будет считаться готовым после этого шага

Следующий шаг считается выполненным, если:
- prompts вставлены в репозиторий по реальным путям;
- Pydantic-модели существуют в коде;
- агенты можно инстанцировать с `output_type`;
- Mongo search tools находятся в рабочем пакете, а не только в docs;
- тесты на модели и tools проходят.
