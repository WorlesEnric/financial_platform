from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.identity.models import (
    IdentityDocument,
    IdentityDocumentStatus,
    IdentityDocumentType,
    IdentityVerification,
    VerificationMethod,
)


class VerificationResult:
    def __init__(
        self,
        success: bool,
        verification: Optional[IdentityVerification] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.verification = verification
        self.error = error


class DocumentValidationResult:
    def __init__(
        self,
        is_valid: bool,
        errors: List[str],
        document: Optional[IdentityDocument] = None,
    ) -> None:
        self.is_valid = is_valid
        self.errors = errors
        self.document = document


class VerificationService:
    def __init__(self) -> None:
        self._codes: Dict[str, Tuple[str, datetime]] = {}

    def verify_email(
        self,
        verification: IdentityVerification,
        code: str,
        expected_code: str,
    ) -> VerificationResult:
        if verification.is_locked:
            return VerificationResult(
                success=False,
                verification=verification,
                error="Verification locked due to too many attempts",
            )

        if code != expected_code:
            verification.record_attempt(success=False, reason="Invalid verification code")
            return VerificationResult(
                success=False,
                verification=verification,
                error="Invalid verification code",
            )

        verification.record_attempt(success=True)
        return VerificationResult(success=True, verification=verification)

    def verify_sms(
        self,
        verification: IdentityVerification,
        code: str,
        expected_code: str,
    ) -> VerificationResult:
        return self.verify_email(verification, code, expected_code)

    def verify_totp(
        self,
        verification: IdentityVerification,
        code: str,
        expected_code: str,
    ) -> VerificationResult:
        return self.verify_email(verification, code, expected_code)

    def verify_document(
        self,
        document: IdentityDocument,
        verifier_id: str,
        is_valid: bool,
        rejection_reason: Optional[str] = None,
    ) -> DocumentValidationResult:
        if document.is_expired:
            document.status = IdentityDocumentStatus.EXPIRED
            return DocumentValidationResult(
                is_valid=False,
                errors=["Document has expired"],
                document=document,
            )

        if document.is_verified:
            return DocumentValidationResult(
                is_valid=True,
                errors=[],
                document=document,
            )

        if is_valid:
            document.status = IdentityDocumentStatus.VERIFIED
            document.verified_by = verifier_id
            document.verified_at = datetime.now(timezone.utc)
            return DocumentValidationResult(is_valid=True, errors=[], document=document)
        else:
            document.status = IdentityDocumentStatus.REJECTED
            document.rejection_reason = rejection_reason
            return DocumentValidationResult(
                is_valid=False,
                errors=[rejection_reason or "Document verification failed"],
                document=document,
            )

    def validate_document_number(
        self,
        document_type: IdentityDocumentType,
        document_number: str,
    ) -> bool:
        if not document_number:
            return False
        min_len, max_len = {
            IdentityDocumentType.PASSPORT: (6, 20),
            IdentityDocumentType.DRIVERS_LICENSE: (8, 18),
            IdentityDocumentType.NATIONAL_ID: (5, 20),
            IdentityDocumentType.TAX_ID: (9, 11),
            IdentityDocumentType.COMPANY_REGISTRATION: (6, 30),
        }.get(document_type, (1, 50))
        return min_len <= len(document_number.strip()) <= max_len

    def generate_verification_code(self, length: int = 6) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(length))

    def generate_totp_secret(self) -> str:
        return secrets.token_hex(20)

    def send_verification_code(
        self,
        method: VerificationMethod,
        recipient: str,
        code: str,
    ) -> None:
        key = f"{method.value}:{recipient}"
        self._codes[key] = (code, datetime.now(timezone.utc) + timedelta(minutes=10))

    def verify_code(
        self,
        method: VerificationMethod,
        recipient: str,
        code: str,
    ) -> bool:
        key = f"{method.value}:{recipient}"
        stored = self._codes.get(key)
        if stored is None:
            return False
        expected_code, expires_at = stored
        if datetime.now(timezone.utc) > expires_at:
            self._codes.pop(key, None)
            return False
        if not secrets.compare_digest(code, expected_code):
            return False
        self._codes.pop(key, None)
        return True

    def check_identity_documents_complete(
        self,
        documents: List[IdentityDocument],
        required_types: Optional[List[IdentityDocumentType]] = None,
    ) -> bool:
        if required_types is None:
            required_types = [IdentityDocumentType.PASSPORT, IdentityDocumentType.NATIONAL_ID]
        verified_types = {
            d.document_type
            for d in documents
            if d.status == IdentityDocumentStatus.VERIFIED and not d.is_expired
        }
        return all(t in verified_types for t in required_types)
