# MVP DoD Audit

## Scope
Audit against `docs/TECH_SPEC_MVP.md` section 11 (Definition of Done) plus UX scenario 2.2(3) run comparison.

## DoD Matrix

| DoD criterion | Status | Evidence (tests/files/artifacts) | Comment / risk |
|---|---|---|---|
| 1) Upload 2+ docs (PDF/DOCX), assign `doc_id`, persist originals | done | `tests/test_pipeline_ocr_stage.py::test_pipeline_ocr_stage_persists_documents_and_artifacts` (PDF + DOCX, `doc_id` and `original_path` checks) | Uses extension-based fixture files in tests; real malformed documents are handled by OCR/parse error taxonomy. |
| 2) OCR via Mistral with saved artifacts (`raw_response.json`, `combined.md`, `tables/`, `images/`) | done | `tests/test_mistral_ocr_client.py::test_mistral_ocr_client_saves_expected_artifacts`; `app/ocr_client/mistral_ocr.py` | `tables/` depends on `table_format`; covered by dedicated tests including `table_format=none`. |
| 3) `user_content` packed strictly as `<BEGIN_DOCUMENTS> ... <END_DOCUMENTS>` | done | `tests/test_pack_documents.py::test_pack_documents_wraps_markdown_in_expected_markers`; `app/pipeline/pack_documents.py` | Placeholders for tables/images are preserved by design. |
| 4) OpenAI provider (gpt-5.1/5.2), reasoning effort switch, strict JSON schema | done | `tests/test_openai_client.py` (payload strict schema + tools disabled + reasoning mapping), `app/llm_client/openai_client.py` | Live provider availability depends on external API credentials/network at runtime. |
| 5) Google provider (Gemini Pro/Flash), system instruction, strict JSON schema | done | `tests/test_gemini_client.py` (JSON schema + system instruction + thinking mapping), `app/llm_client/gemini_client.py` | Model IDs are config-driven (`app/config/providers.yaml`) and can be updated without code changes. |
| 6) LLM response validated via jsonschema, errors shown | done | `tests/test_validate_output.py`; `tests/test_orchestrator_full_pipeline.py::test_full_pipeline_schema_invalid_marks_run_failed_and_persists_validation`; `app/ui/gradio_app.py` | Semantic invariants are also enforced (item uniqueness/rules). |
| 7) Metrics (tokens/cost/timings) shown in UI and saved to SQLite | done | `tests/test_orchestrator_full_pipeline.py::test_full_pipeline_success_persists_artifacts_db_and_metrics`; `tests/test_storage_repo.py`; `tests/test_gradio_smoke.py` | Cost accuracy depends on static `pricing.yaml` updates. |
| 8) Run history with loading previous run | done | `tests/test_gradio_smoke.py::test_history_load_returns_saved_run_bundle_with_progress_and_log`; `app/ui/gradio_app.py` | Missing artifact files are handled via safe readers and user-friendly fallback text. |
| UX 2.2(3) Run comparison for outputs/metrics | done | `app/ui/run_comparison.py`; `tests/test_run_comparison.py`; `tests/test_gradio_smoke.py::test_compare_history_runs_returns_diff_for_two_runs` | Deterministic JSON-friendly diff includes checklist/gaps/questions/metrics + change counters. |

## Conclusion
- Blocking gaps: none.
- MVP DoD status: **ready**.

## Known Limits
1. End-to-end tests use mocked OCR/LLM providers; live API contract health is runtime-dependent.
2. Context-size guard is char-based (`context_char_limit`) and conservative vs provider tokenization.
3. Local artifacts may contain sensitive data by design; retention/deletion is operator responsibility.
