# Спецификация Pydantic-моделей для агентного контура

## 1. Назначение

Этот документ фиксирует обязательные модели, которые должны появиться в `app/legal_memo/models.py`.

Они нужны для того, чтобы агентный pipeline запускался как типизированная цепочка `Agent(..., output_type=...)`, а не как произвольный JSON.

## 2. Обязательные модели

### 2.1. `CaseIssueSheet`
Назначение: результат factual intake-шага.

Обязательные блоки:
- `user_goal: str`
- `case_summary: str`
- `timeline: list[TimelineItem]`
- `money_facts: list[MoneyFact]`
- `established_facts: list[str]`
- `disputed_facts: list[str]`
- `missing_evidence: list[str]`
- `issue_codes: list[str]`

Вспомогательные модели:
- `EvidenceRef { doc_id, anchor_id }`
- `TimelineItem { event, date, status, evidence }`
- `MoneyFact { name, value, status, evidence }`

### 2.2. `ResearchBundle`
Назначение: результат legal research-шага.

Обязательные блоки:
- `issues: list[ResearchIssue]`
- `legal_authorities: list[LegalAuthority]`
- `coverage_gaps: list[str]`
- `search_trace: SearchTrace`

`LegalAuthority` должен содержать:
- `ref_id: str` (`L01`, `L02`, ...)
- `doc_id: str`
- `anchor_id: str`
- `document_title: str`
- `locator_label: str`
- `authority_level: str`
- `usually_supports: str | None`
- `topic_codes: list[str]`
- `quote: str`
- `supports_position: Literal["supporting", "adverse", "neutral"]`

### 2.3. `StrategicMemo`
Назначение: финальный типизированный результат memo writer.

Обязательные блоки:
- `title: str`
- `executive_summary: list[MemoPoint]`
- `facts_considered: list[FactsPoint]`
- `legal_analysis: list[LegalAnalysisSection]`
- `recommended_next_steps: list[str]`
- `limitations: list[str]`
- `citation_register: CitationRegister`

`MemoPoint`:
- `text: str`
- `legal_ref_ids: list[str]`
- `evidence_ref_ids: list[str]`

`LegalAnalysisSection`:
- `issue_code: str`
- `issue_title: str`
- `analysis_points: list[MemoPoint]`
- `risks: list[RiskPoint]`
- `practical_takeaway: str`

### 2.4. `MemoQcReport`
Назначение: результат QC-проверки memo.

Обязательные блоки:
- `status: Literal["pass", "needs_revision", "fail"]`
- `issues: list[QcIssue]`
- `checked_paths: list[str]`
- `summary: str`

`QcIssue`:
- `severity: Literal["critical", "major", "minor"]`
- `path: str`
- `message: str`
- `suggested_fix: str | None`

## 3. Дополнительные правила

### 3.1. Extra fields
Все модели должны использовать `extra="forbid"`.

### 3.2. Alias format
Проверять regex:
- legal refs: `^L\d{2}$`
- evidence refs: `^U\d{2}$`

### 3.3. Status fields
Для `TimelineItem.status` и `MoneyFact.status` использовать только:
- `confirmed`
- `ambiguous`
- `missing`
- `conflict`

### 3.4. Empty lists
Пустые списки допустимы только там, где это прямо ожидаемо:
- `coverage_gaps`
- `limitations`
- `issues` в `MemoQcReport`

`issue_codes` в `CaseIssueSheet` должен быть непустым.

## 4. Следующий практический шаг

После добавления этих моделей агентный контур можно сразу запускать так:

```python
intake_agent = Agent(..., output_type=CaseIssueSheet)
research_agent = Agent(..., tools=[...], output_type=ResearchBundle)
memo_agent = Agent(..., output_type=StrategicMemo)
qc_agent = Agent(..., output_type=MemoQcReport)
```

Это обязательный шаг для перехода от текстовой документации к реально исполняемому pipeline.
