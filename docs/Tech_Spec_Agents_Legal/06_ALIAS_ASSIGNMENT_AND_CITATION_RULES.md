# Правила присвоения alias и формирования citation register

## 1. Зачем нужен отдельный документ

В исходной документации введены alias `L01`, `U01`, но не до конца формализовано, как именно они появляются и какой объект считается источником истины.

Этот документ фиксирует минимальные правила для v1.

## 2. Правила для legal alias `Lxx`

### 2.1. Источник истины
Источником истины для legal alias является массив:

`ResearchBundle.legal_authorities`

### 2.2. Формат
- legal alias имеет вид `L01`, `L02`, ...
- один alias соответствует ровно одной паре `doc_id + anchor_id`
- один и тот же `doc_id + anchor_id` не должен повторяться под разными alias

### 2.3. Порядок
Для v1 нормативным считается порядок следования в `ResearchBundle.legal_authorities`.
Downstream-код не должен автоматически перенумеровывать legal aliases.

## 3. Правила для evidence alias `Uxx`

### 3.1. Источник истины
Источником истины для evidence alias является отдельный deterministic builder, который строится поверх `CaseIssueSheet` и `user_anchor_catalog`.

### 3.2. Минимальный алгоритм
В v1 builder должен:
1. взять все `EvidenceRef` из `CaseIssueSheet.timeline[*].evidence` и `CaseIssueSheet.money_facts[*].evidence`;
2. пройти их в порядке первого появления;
3. удалить дубликаты по `(doc_id, anchor_id)`;
4. назначить `U01`, `U02`, ...

### 3.3. Почему так
Это даёт:
- повторяемость;
- небольшое число U-alias;
- понятную связь между factual intake и memo writer.

## 4. Формирование `citation_register`

### 4.1. Источник
`StrategicMemo.citation_register` — источник истины для финального memo run.
Отдельный `citation_register.json` должен быть derivation of record из `memo.json`, а не независимым вторым источником истины.

### 4.2. Legal register item
Минимум полей:
- `ref_id`
- `doc_id`
- `anchor_id`
- `locator_label`
- `preview`

### 4.3. Evidence register item
Минимум полей:
- `ref_id`
- `doc_id`
- `anchor_id`
- `preview`

## 5. Валидация

Перед рендерингом `memo.md` обязательно проверить:
- все `legal_ref_ids` существуют в `citation_register.legal`;
- все `evidence_ref_ids` существуют в `citation_register.evidence`;
- в narrative text нет raw `doc_id` и raw `anchor_id`;
- нет дублирующих alias c разным payload.
