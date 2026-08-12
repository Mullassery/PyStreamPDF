import pytest
import pystreampdf

from conftest import ENCRYPTED_PDF_CORRECT_PASSWORD, ENCRYPTED_PDF_WRONG_PASSWORD


# --- Normal (unencrypted) PDFs -------------------------------------------

def test_is_encrypted_normal_pdf(simple_pdf):
    """Test that normal PDFs are not encrypted"""
    is_enc = pystreampdf._core.PyPdfDocument.is_encrypted(simple_pdf)
    assert is_enc is False


def test_open_nonencrypted_with_password(simple_pdf):
    """Opening an unencrypted PDF with a password (any password, since none is
    required) should still succeed -- PDFium simply ignores the password."""
    doc = pystreampdf._core.PyPdfDocument.open_with_password(simple_pdf, "wrong_password")
    assert doc is not None
    assert doc.page_count >= 1


def test_permissions_normal_pdf(simple_pdf):
    """Test getting permissions from normal PDF"""
    perms = pystreampdf._core.PyPdfDocument.permissions(simple_pdf)
    assert perms is not None
    assert isinstance(perms, pystreampdf._core.PyPdfPermissions)


def test_permissions_fields(simple_pdf):
    """Test that permissions have correct fields"""
    perms = pystreampdf._core.PyPdfDocument.permissions(simple_pdf)
    assert hasattr(perms, "can_copy")
    assert hasattr(perms, "can_print")
    assert hasattr(perms, "can_modify")
    assert hasattr(perms, "can_annotate")
    assert isinstance(perms.can_copy, bool)
    assert isinstance(perms.can_print, bool)
    assert isinstance(perms.can_modify, bool)
    assert isinstance(perms.can_annotate, bool)


def test_permissions_normal_pdf_all_allowed(simple_pdf):
    """An unencrypted PDF has no security handler restricting anything, so
    every permission should genuinely be allowed."""
    perms = pystreampdf._core.PyPdfDocument.permissions(simple_pdf)
    assert perms.can_copy is True
    assert perms.can_print is True
    assert perms.can_modify is True
    assert perms.can_annotate is True


def test_fingerprint_consistent(simple_pdf):
    """Test fingerprint is consistent for same file"""
    doc1 = pystreampdf.open(simple_pdf)
    fp1 = doc1.fingerprint()

    doc2 = pystreampdf.open(simple_pdf)
    fp2 = doc2.fingerprint()

    assert fp1 == fp2


def test_fingerprint_is_string(simple_pdf):
    """Test that fingerprint returns string"""
    doc = pystreampdf.open(simple_pdf)
    fp = doc.fingerprint()
    assert isinstance(fp, str)
    assert len(fp) > 0


# --- Genuinely password-protected PDFs -----------------------------------

def test_is_encrypted_password_protected_pdf(encrypted_pdf):
    """A PDF encrypted with a user password must be reported as encrypted."""
    is_enc = pystreampdf._core.PyPdfDocument.is_encrypted(encrypted_pdf)
    assert is_enc is True


def test_open_encrypted_pdf_without_password_fails(encrypted_pdf):
    """Opening a password-protected PDF with no password must fail closed,
    not silently succeed with an unauthenticated parse."""
    with pytest.raises(Exception):
        pystreampdf._core.PyPdfDocument.open(encrypted_pdf)


def test_open_encrypted_pdf_wrong_password_fails(encrypted_pdf):
    """Opening a password-protected PDF with the WRONG password must fail
    closed -- this is the core regression test for the previous stub, which
    ignored the password entirely and parsed unauthenticated."""
    with pytest.raises(Exception):
        pystreampdf._core.PyPdfDocument.open_with_password(
            encrypted_pdf, ENCRYPTED_PDF_WRONG_PASSWORD
        )


def test_open_encrypted_pdf_correct_password_succeeds(encrypted_pdf):
    """Opening a password-protected PDF with the CORRECT password must
    succeed and yield real page content."""
    doc = pystreampdf._core.PyPdfDocument.open_with_password(
        encrypted_pdf, ENCRYPTED_PDF_CORRECT_PASSWORD
    )
    assert doc is not None
    assert doc.page_count >= 1


# --- Permission-restricted PDFs (owner-password-only protection) ---------

def test_is_encrypted_permission_restricted_pdf(permission_restricted_pdf):
    """A PDF protected only by an owner password (no user password required
    to open) is still, genuinely, an encrypted document."""
    is_enc = pystreampdf._core.PyPdfDocument.is_encrypted(permission_restricted_pdf)
    assert is_enc is True


def test_permissions_restricted_pdf_reports_real_restrictions(permission_restricted_pdf):
    """The permission flags for a genuinely restricted PDF must reflect the
    real restrictions (all disallowed here), not the old all-permissive
    default."""
    perms = pystreampdf._core.PyPdfDocument.permissions(permission_restricted_pdf)
    assert perms.can_copy is False
    assert perms.can_print is False
    assert perms.can_modify is False
    assert perms.can_annotate is False


def test_open_permission_restricted_pdf_without_password_succeeds(permission_restricted_pdf):
    """A document with an empty user password should still open without a
    password -- only the permissions are restricted, not access itself."""
    doc = pystreampdf._core.PyPdfDocument.open(permission_restricted_pdf)
    assert doc is not None
    assert doc.page_count >= 1


# --- Malformed / adversarial PDFs -----------------------------------------

def test_open_malformed_pdf_raises_not_fabricates(malformed_pdf):
    """A file that isn't valid PDF content must raise an error. It must NOT
    silently return a fabricated document with placeholder page content --
    this is the core regression test for the previous silent-fallback bug."""
    with pytest.raises(Exception):
        pystreampdf._core.PyPdfDocument.open(malformed_pdf)


def test_open_truncated_pdf_raises_not_fabricates(truncated_pdf):
    """A truncated/partial PDF (simulating an interrupted download or write)
    must raise an error rather than returning fabricated placeholder pages."""
    with pytest.raises(Exception):
        pystreampdf._core.PyPdfDocument.open(truncated_pdf)


def test_open_nonexistent_pdf_raises(tmp_path):
    """Opening a path that doesn't exist at all must raise, not fabricate."""
    missing = str(tmp_path / "does_not_exist_at_all.pdf")
    with pytest.raises(Exception):
        pystreampdf._core.PyPdfDocument.open(missing)


def test_open_deeply_nested_pdf_does_not_crash_process(deeply_nested_pdf):
    """A pathologically deeply-nested PDF object graph should either parse or
    raise a clean Python exception -- it must never crash/panic the whole
    process. (This file is also not a fully valid PDF -- no xref table --
    so an exception is the expected, correct outcome.)"""
    try:
        doc = pystreampdf._core.PyPdfDocument.open(deeply_nested_pdf)
        # If PDFium is lenient enough to parse it, that's fine too, as long
        # as we get real object back rather than a crash.
        assert doc is not None
    except Exception:
        pass
