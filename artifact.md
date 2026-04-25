# Step Deliverable: `step.task-1777008735841.ocr_model`

## Created Artifact

**File:** `src/finance_platform/models/ocr_record.py`

Contains three Pydantic model classes that the `models/__init__.py` (line 32) already imports as `OcrRecord` — renamed here to clarify the spec's distinct tables:

| Class | Spec Requirement | Table / Purpose |
|---|---|---|
| `OcrExtractionResult` (§"ocr_extraction_results") | Preserve raw + confidence + structured_json; versioned with `is_latest` flag | Core OCR extraction result record, extends `TimestampMixin` |
| `ExpenseDocument` (§"expense_documents") | `file_sha256` hash, append-only, separate `approved_file_url`/`voided_file_url` | Document storage record with SHA256 integrity |
| `ExpenseFieldConfirmation` (§"expense_field_confirmations") | OCR vs confirmed value tracking; never overwrite user-confirmed values | Stores user-confirmed field values alongside OCR originals |

## Acceptance Contract Coverage

- **Monetary fields**: No monetary fields in OCR models (OCR extracts text/confidence, not amounts).
- **OCR results never overwrite user-confirmed values**: `ExpenseFieldConfirmation` stores both `ocr_value` and `confirmed_value`; `OcrExtractionResult` is versioned with `is_latest` flag and `version_number`.
- **Raw text + confidence + structured_json**: `OcrExtractionResult` includes `raw_text`, `confidence_overall`/`confidence_text`/`confidence_layout`/`confidence_field_extraction`, and `structured_json`.
- **Append-only documents**: `ExpenseDocument` has `is_append_only=True` default, `file_sha256` for integrity.
- **Watermark URLs**: `approved_file_url`, `voided_file_url`, `approved_file_sha256`, `voided_file_sha256` on `ExpenseDocument`.

## Conventions Followed

- Uses `from __future__ import annotations`, `TimestampMixin` from `models.base`, `pydantic.Field` with validation constraints.
- `company_id` on every cross-company table.
- `id: str` inherited from `BaseModel` (UUID string).
- `metadata: Dict[str, Any] = Field(default_factory=dict)` consistent with expense/approval models.
- No `test_*` files, no SQLAlchemy/SQLModel — uses Pydantic `BaseModel` consistent with existing `models/` convention.
