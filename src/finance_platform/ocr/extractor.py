from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Pattern, Tuple

from finance_platform.logging import get_logger
from finance_platform.ocr.models import (
    ExtractedFields,
    OcrConfidence,
    OcrDocumentType,
    OcrField,
    OcrFieldType,
    OcrResult,
)

logger = get_logger(__name__)


class FieldExtractor:

    VENDOR_PATTERNS: List[Pattern] = [
        re.compile(r"(?:vendor|supplier|seller|from|company|bill\s*from)\s*[:\-]?\s*(.+)", re.IGNORECASE),
        re.compile(r"^(?:vendor|supplier|seller)\s*$", re.IGNORECASE | re.MULTILINE),
    ]

    INVOICE_NUMBER_PATTERNS: List[Pattern] = [
        re.compile(r"(?:invoice\s*(?:#|no|number|num|nr|id))\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/\-_.]{2,30})", re.IGNORECASE),
        re.compile(r"(?:inv\s*(?:#|no|number)?)\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/\-_.]{2,30})", re.IGNORECASE),
        re.compile(r"(?:receipt\s*(?:#|no|number))\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/\-_.]{2,30})", re.IGNORECASE),
    ]

    DATE_PATTERNS: List[Pattern] = [
        re.compile(r"(?:invoice|receipt|bill|date|issued|dated)\s*(?:date)?\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", re.IGNORECASE),
        re.compile(r"(?:date)\s*[:\-]?\s*(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})", re.IGNORECASE),
        re.compile(r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})", re.IGNORECASE),
        re.compile(r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})", re.IGNORECASE),
    ]

    DUE_DATE_PATTERNS: List[Pattern] = [
        re.compile(r"(?:due\s*(?:date)?|payment\s*terms?|pay\s*by)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})", re.IGNORECASE),
        re.compile(r"(?:due\s*(?:date)?)\s*[:\-]?\s*(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})", re.IGNORECASE),
    ]

    TOTAL_PATTERNS: List[Pattern] = [
        re.compile(r"(?:total\s*(?:due|amount|paid|\.?$)|amount\s*due|grand\s*total|balance\s*due)\s*[:\-]?\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
        re.compile(r"(?:total)\s*[:\-]?\s*\$?\s*([\d,]+\.?\d{0,2})\s*$", re.IGNORECASE | re.MULTILINE),
    ]

    SUBTOTAL_PATTERNS: List[Pattern] = [
        re.compile(r"(?:subtotal|sub\s*total)\s*[:\-]?\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
    ]

    TAX_PATTERNS: List[Pattern] = [
        re.compile(r"(?:tax|vat|gst|hst|pst|sales\s*tax)\s*(?:amount|due|\.?$)?\s*[:\-]?\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
        re.compile(r"(?:tax|vat|gst|hst|pst)\s*(?:rate|%)\s*[:\-]?\s*([\d,]+\.?\d{0,2})\s*%", re.IGNORECASE),
    ]

    TAX_ID_PATTERNS: List[Pattern] = [
        re.compile(r"(?:tax\s*(?:id|identification|number|#|no)|ein|vat\s*(?:number|#|id)|abn|gst\s*(?:#|number|id))\s*[:\-]?\s*([A-Za-z0-9\-]+)", re.IGNORECASE),
    ]

    CURRENCY_PATTERNS: List[Pattern] = [
        re.compile(r"(?:currency|curr\.?)\s*[:\-]?\s*([A-Z]{3})", re.IGNORECASE),
    ]

    PO_NUMBER_PATTERNS: List[Pattern] = [
        re.compile(r"(?:p\.?o\.?\s*(?:#|number|no)|purchase\s*order\s*(?:#|number|no|num)?)\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9/\-_.]{2,20})", re.IGNORECASE),
    ]

    def __init__(self) -> None:
        self._patterns: Dict[str, List[Tuple[str, re.Pattern, float]]] = self._build_pattern_registry()

    def _build_pattern_registry(self) -> Dict[str, List[Tuple[str, re.Pattern, float]]]:
        return {
            "vendor_name": [
                ("VENDOR", p, 0.8) for p in self.VENDOR_PATTERNS
            ],
            "invoice_number": [
                ("INV_NUM", p, 0.9) for p in self.INVOICE_NUMBER_PATTERNS
            ],
            "invoice_date": [
                ("DATE", p, 0.8) for p in self.DATE_PATTERNS
            ],
            "due_date": [
                ("DUE", p, 0.85) for p in self.DUE_DATE_PATTERNS
            ],
            "total_amount": [
                ("TOTAL", p, 0.9) for p in self.TOTAL_PATTERNS
            ],
            "subtotal": [
                ("SUBTOTAL", p, 0.85) for p in self.SUBTOTAL_PATTERNS
            ],
            "tax_amount": [
                ("TAX", p, 0.85) for p in self.TAX_PATTERNS
            ],
            "vendor_tax_id": [
                ("TAX_ID", p, 0.8) for p in self.TAX_ID_PATTERNS
            ],
            "currency": [
                ("CURRENCY", p, 0.7) for p in self.CURRENCY_PATTERNS
            ],
            "purchase_order_number": [
                ("PO", p, 0.85) for p in self.PO_NUMBER_PATTERNS
            ],
        }

    def extract_all(self, text: str, doc_type: OcrDocumentType = OcrDocumentType.OTHER) -> ExtractedFields:
        fields = ExtractedFields()
        text = text.strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for field_name, patterns in self._patterns.items():
            best_match, best_val = self._match_patterns(text, lines, patterns)
            if best_val is not None:
                ocr_field = OcrField(
                    name=field_name,
                    value=best_val,
                    field_type=self._get_field_type(field_name),
                    confidence=best_match[2] if best_match else 0.5,
                    raw_text=best_val,
                )
                setattr(fields, field_name, ocr_field)

        return fields

    def _match_patterns(
        self,
        text: str,
        lines: List[str],
        patterns: List[Tuple[str, Pattern, float]],
    ) -> Tuple[Optional[Tuple[str, Pattern, float]], Optional[str]]:
        best_confidence = 0.0
        best_value: Optional[str] = None
        best_match: Optional[Tuple[str, Pattern, float]] = None

        for label, pattern, base_conf in patterns:
            for match in pattern.finditer(text):
                value = match.group(1).strip()
                conf = base_conf
                if len(value) > 3:
                    conf = min(1.0, conf + 0.05)
                if conf > best_confidence:
                    best_confidence = conf
                    best_value = value
                    best_match = (label, pattern, conf)

        return best_match, best_value

    def _get_field_type(self, field_name: str) -> OcrFieldType:
        type_map = {
            "vendor_name": OcrFieldType.TEXT,
            "vendor_address": OcrFieldType.ADDRESS,
            "vendor_tax_id": OcrFieldType.TAX_ID,
            "customer_name": OcrFieldType.TEXT,
            "customer_address": OcrFieldType.ADDRESS,
            "invoice_number": OcrFieldType.TEXT,
            "invoice_date": OcrFieldType.DATE,
            "due_date": OcrFieldType.DATE,
            "purchase_order_number": OcrFieldType.TEXT,
            "subtotal": OcrFieldType.CURRENCY,
            "tax_amount": OcrFieldType.CURRENCY,
            "tax_rate": OcrFieldType.PERCENTAGE,
            "discount_amount": OcrFieldType.CURRENCY,
            "total_amount": OcrFieldType.CURRENCY,
            "currency": OcrFieldType.TEXT,
            "payment_terms": OcrFieldType.TEXT,
        }
        return type_map.get(field_name, OcrFieldType.TEXT)


class InvoiceExtractor(FieldExtractor):

    INVOICE_SPECIFIC_PATTERNS: List[Pattern] = [
        re.compile(r"(?:payment\s*terms|terms)\s*[:\-]?\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:bank\s*(?:account|a/c|#)|account\s*(?:number|no|#))\s*[:\-]?\s*([\d\-]+)", re.IGNORECASE),
    ]

    def extract_all(self, text: str, doc_type: OcrDocumentType = OcrDocumentType.INVOICE) -> ExtractedFields:
        fields = super().extract_all(text, doc_type)
        text = text.strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        for pattern in self.INVOICE_SPECIFIC_PATTERNS:
            field_name = "payment_terms" if "terms" in pattern.pattern.lower() else "bank_account"
            if getattr(fields, field_name) is None:
                match = pattern.search(text)
                if match:
                    value = match.group(1).strip()
                    setattr(
                        fields, field_name,
                        OcrField(
                            name=field_name,
                            value=value,
                            field_type=OcrFieldType.TEXT if field_name == "payment_terms" else OcrFieldType.ACCOUNT_NUMBER,
                            confidence=0.7,
                            raw_text=value,
                        ),
                    )

        return fields


class ReceiptExtractor(FieldExtractor):

    RECEIPT_SPECIFIC_PATTERNS: List[Pattern] = [
        re.compile(r"(?:store|merchant|location|branch)\s*[:\-]?\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:cashier|teller|operator|sales\s*assoc)\s*(?:#|no|id)?\s*[:\-]?\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:tip|gratuity)\s*[:\-]?\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
        re.compile(r"(?:change|change\s*due)\s*[:\-]?\s*\$?([\d,]+\.?\d{0,2})", re.IGNORECASE),
    ]

    def extract_all(self, text: str, doc_type: OcrDocumentType = OcrDocumentType.RECEIPT) -> ExtractedFields:
        fields = super().extract_all(text, doc_type)
        text = text.strip()

        for pattern in self.RECEIPT_SPECIFIC_PATTERNS:
            match = pattern.search(text)
            if match:
                raw_val = match.group(0).strip()
                val = match.group(1).strip()
                if "tip" in pattern.pattern or "change" in pattern.pattern:
                    fields.additional_fields["tip"] = OcrField(
                        name="tip",
                        value=val,
                        field_type=OcrFieldType.CURRENCY,
                        confidence=0.7,
                        raw_text=raw_val,
                    )
                elif "store" in pattern.pattern:
                    if fields.vendor_name is None:
                        fields.vendor_name = OcrField(
                            name="vendor_name",
                            value=val,
                            field_type=OcrFieldType.TEXT,
                            confidence=0.7,
                            raw_text=raw_val,
                        )

        return fields
