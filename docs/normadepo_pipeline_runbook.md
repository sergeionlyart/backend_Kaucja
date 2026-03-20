# NormaDepo Pipeline Runbook

## Core modes

- `full`: пройти discovery + ingest + classification + call A + call B для выбранного среза.
- `new`: обработать новые или изменившиеся документы; completed annotatable документы skip'аются только при совпадении `source.file_sha256` и `annotation.analysis_fingerprint`.
- `rerun --rerun-scope failed`: поднять документы со статусами `failed` и `partial`; partial с готовым call A возобновляются со стадии `annotate_ru`.
- `rerun --rerun-scope stale`: переработать документы с изменённым файлом или изменившимся effective analysis fingerprint.
- `rerun --rerun-scope doc-id --only-doc-id <path>`: прогнать один документ по относительному POSIX-path.

## Safe dry-run

```bash
python scripts/annotate_legal_docs.py \
  --config config/pipeline.yaml \
  --mode new \
  --limit 3 \
  --dry-run
```

- dry-run не пишет в Mongo и не вызывает реальный LLM;
- `rerun --dry-run` использует repository lookup только если Mongo доступен.

## Useful flags

- `--only-doc-id`: обработать один документ.
- `--from-relative-path`: начать детерминированный проход с указанного relative path.
- `--force-classifier-fallback`: выполнить best-effort diagnostic fallback classifier поверх уже найденного rule-based route. Основной маршрут остаётся rule-based даже при timeout, low-confidence или несовпадении fallback verdict.
- `--log-level {DEBUG,INFO,WARNING,ERROR}`: минимальный уровень JSONL-лога.
- `--dry-run` нельзя комбинировать с `--force-classifier-fallback`, чтобы сохранить zero-LLM dry-run invariant.

## Logs

- каждый запуск пишет `logs/<run_id>.jsonl`;
- каждая строка содержит `timestamp`, `level`, `run_id`, `doc_id`, `stage`, `event`, `message`, `error`, `details`;
- summary всегда выводится в stdout как JSON.

## Safe rerun notes

- `annotation.original` не теряется, если падает translation stage B;
- terminal `processing.last_success_at` обновляется только на `completed` annotatable документах и terminal non-target skip;
- forced fallback diagnostics не меняют canonical classification без отдельно утверждённой политики override;
- для live smoke лучше использовать отдельную Mongo collection через `--mongo-collection`, чтобы не смешивать smoke и рабочие записи.
- `translation_ru_max_output_tokens` теперь имеет один явный contract: example/default config использует `24000`, и runtime отправляет ровно это настроенное значение без скрытого auto-floor.
- значения ниже `24000` для `translation_ru_max_output_tokens` теперь отклоняются в config validation, потому что live smoke показал риск `llm_incomplete` на stage B при меньшем бюджете.
- discovery heuristics опираются на body/content markers и не должны повышать `url_count` из metadata URLs до `discovery_reference` для source-backed legal excerpts.

## Live smoke pattern

```bash
set -a
source .env
set +a

python scripts/annotate_legal_docs.py \
  --config config/pipeline.yaml \
  --mode full \
  --only-doc-id pl_acts/05_pl_lex_118.md \
  --mongo-collection documents_live_smoke_local \
  --log-level INFO

python scripts/annotate_legal_docs.py \
  --config config/pipeline.yaml \
  --mode new \
  --only-doc-id pl_acts/05_pl_lex_118.md \
  --mongo-collection documents_live_smoke_local \
  --log-level INFO
```
