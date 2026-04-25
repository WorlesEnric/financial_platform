from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from finance_platform.logging import get_logger
from finance_platform.ocr.models import (
    ExtractedFields,
    OcrField,
    OcrFieldType,
    OcrProcessingStatus,
    OcrResult,
)

logger = get_logger(__name__)


class OcrValidationResult:
    def __init__(
        self,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        field_results: Optional[Dict[str, bool]] = None,
    ) -> None:
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.field_results = field_results or {}

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "field_results": self.field_results,
        }


class FieldValidator:
    def validate(self, field: OcrField) -> Tuple[bool, Optional[str]]:
        if field.value is None or not field.value.strip():
            return False, "Field value is empty"

        validators = {
            OcrFieldType.DATE: self._validate_date,
            OcrFieldType.CURRENCY: self._validate_currency,
            OcrFieldType.NUMBER: self._validate_number,
            OcrFieldType.PERCENTAGE: self._validate_percentage,
            OcrFieldType.EMAIL: self._validate_email,
            OcrFieldType.PHONE: self._validate_phone,
            OcrFieldType.TAX_ID: self._validate_tax_id,
            OcrFieldType.ADDRESS: self._validate_address,
        }
        validator = validators.get(field.field_type)
        if validator:
            return validator(field.value)
        return True, None

    def _validate_date(self, value: str) -> Tuple[bool, Optional[str]]:
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y",
            "%m-%d-%Y", "%m-%d-%y", "%d-%m-%Y", "%d-%m-%y",
            "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y",
            "%B %d, %Y", "%d %B %Y", "%b %d, %Y", "%d %b %Y",
        ]
        for fmt in formats:
            try:
                datetime.strptime(value.strip(), fmt)
                return True, None
            except ValueError:
                continue
        return False, f"Unable to parse date: {value}"

    def _validate_currency(self, value: str) -> Tuple[bool, Optional[str]]:
        cleaned = value.replace(",", "").replace("$", "").replace(" ", "")
        try:
            float(cleaned)
            return True, None
        except ValueError:
            return False, f"Invalid currency value: {value}"

    def _validate_number(self, value: str) -> Tuple[bool, Optional[str]]:
        cleaned = value.replace(",", "").replace(" ", "")
        try:
            float(cleaned)
            return True, None
        except ValueError:
            return False, f"Invalid number: {value}"

    def _validate_percentage(self, value: str) -> Tuple[bool, Optional[str]]:
        cleaned = value.replace("%", "").replace(" ", "")
        try:
            num = float(cleaned)
            if 0 <= num <= 100:
                return True, None
            return False, f"Percentage out of range (0-100): {num}"
        except ValueError:
            return False, f"Invalid percentage: {value}"

    def _validate_email(self, value: str) -> Tuple[bool, Optional[str]]:
        import re
        pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if pattern.match(value.strip()):
            return True, None
        return False, f"Invalid email: {value}"

    def _validate_phone(self, value: str) -> Tuple[bool, Optional[str]]:
        import re
        digits = re.sub(r"\D", "", value)
        if 7 <= len(digits) <= 15:
            return True, None
        return False, f"Invalid phone number: {value}"

    def _validate_tax_id(self, value: str) -> Tuple[bool, Optional[str]]:
        cleaned = value.replace("-", "").replace(" ", "").upper()
        if len(cleaned) >= 4:
            return True, None
        return False, f"Tax ID too short: {value}"

    def _validate_address(self, value: str) -> Tuple[bool, Optional[str]]:
        if len(value.strip()) >= 10:
            return True, None
        return False, f"Address too short: {value}"


class OcrValidator:

    def __init__(self) -> None:
        self.field_validator = FieldValidator()

    def validate_result(self, result: OcrResult) -> OcrValidationResult:
        validation = OcrValidationResult()

        if result.processing_status == OcrProcessingStatus.FAILED:
            validation.add_error(f"OCR processing failed: {result.error_message or 'Unknown error'}")
            return validation

        if result.confidence.is_unreliable:
            validation.add_warning(f"Low overall confidence: {result.confidence.overall:.2f}")

        if not result.raw_text.strip():
            validation.add_error("No text was extracted from the document")
            return validation

        self._validate_extracted_fields(result.extracted_fields, validation)
        self._validate_consistency(result, validation)

        return validation

    def validate_for_auto_approval(self, result: OcrResult, min_confidence: float = 0.8) -> bool:
        if not result.confidence.is_reliable:
            return False
        if result.confidence.overall < min_confidence:
            return False
        validation = self.validate_result(result)
        if not validation.is_valid:
            return False
        return True

    def _validate_extracted_fields(self, fields: Any, validation: OcrValidationResult) -> None:
        if not fields:
            return

        for field_name in fields.model_fields_set:
            field = getattr(fields, field_name)
            if isinstance(field, OcrField):
                is_valid, error = self.field_validator.validate(field)
                validation.field_results[field_name] = is_valid
                field.validated = is_valid
                if not is_valid and error:
                    field.validation_errors.append(error)
                    validation.add_warning(f"Field '{field_name}' validation failed: {error}")
            elif isinstance(field, list):
                for item in field:
                    if isinstance(item, OcrField):
                        is_valid, error = self.field_validator.validate(item)
                        item.validated = is_valid
                        if not is_valid and error:
                            item.validation_errors.append(error)

    def _validate_consistency(self, result: OcrResult, validation: OcrValidationResult) -> None:
        fields = result.extracted_fields
        if not fields:
            return

        if fields.subtotal and fields.total_amount:
            try:
                sub = self._parse_amount(fields.subtotal.value or "0")
                tot = self._parse_amount(fields.total_amount.value or "0")
                tax = self._parse_amount(fields.tax_amount.value or "0") if fields.tax_amount else 0
                discount = self._parse_amount(fields.discount_amount.value or "0") if fields.discount_amount else 0
                if abs(tot - (sub + tax - discount)) > 0.02 and tot > 0:
                    validation.add_warning(
                        f"Total ({tot:.2f}) does not match subtotal + tax - discount ({sub + tax - discount:.2f})"
                    )
            except (ValueError, TypeError):
                pass

        if fields.invoice_date and fields.due_date:
            inv_date = self._try_parse_date(fields.invoice_date.value or "")
            due_date = self._try_parse_date(fields.due_date.value or "")
            if inv_date and due_date and due_date < inv_date:
                validation.add_warning("Due date is before invoice date")

    def _parse_amount(self, value: str) -> float:
        return float(value.replace(",", "").replace("$", "").strip())

    def _try_parse_date(self, value: str) -> Optional[datetime]:
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y",
            "%B %d, %Y", "%d %B %Y", "%b %d, %Y", "%d %b %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None
