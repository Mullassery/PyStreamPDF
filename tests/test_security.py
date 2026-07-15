import pytest
import streampdf


def test_is_encrypted_normal_pdf(simple_pdf):
    """Test that normal PDFs are not encrypted"""
    is_enc = streampdf._core.PyPdfDocument.is_encrypted(simple_pdf)
    assert is_enc is False


def test_open_nonencrypted_with_password(simple_pdf):
    """Test opening unencrypted PDF with password succeeds"""
    doc = streampdf._core.PyPdfDocument.open_with_password(simple_pdf, "wrong_password")
    assert doc is not None
    assert doc.page_count >= 1


def test_permissions_normal_pdf(simple_pdf):
    """Test getting permissions from normal PDF"""
    perms = streampdf._core.PyPdfDocument.permissions(simple_pdf)
    assert perms is not None
    assert isinstance(perms, streampdf._core.PyPdfPermissions)


def test_permissions_fields(simple_pdf):
    """Test that permissions have correct fields"""
    perms = streampdf._core.PyPdfDocument.permissions(simple_pdf)
    assert hasattr(perms, "can_copy")
    assert hasattr(perms, "can_print")
    assert hasattr(perms, "can_modify")
    assert hasattr(perms, "can_annotate")
    assert isinstance(perms.can_copy, bool)
    assert isinstance(perms.can_print, bool)
    assert isinstance(perms.can_modify, bool)
    assert isinstance(perms.can_annotate, bool)


def test_fingerprint_consistent(simple_pdf):
    """Test fingerprint is consistent for same file"""
    doc1 = streampdf.open(simple_pdf)
    fp1 = doc1.fingerprint()

    doc2 = streampdf.open(simple_pdf)
    fp2 = doc2.fingerprint()

    assert fp1 == fp2


def test_fingerprint_is_string(simple_pdf):
    """Test that fingerprint returns string"""
    doc = streampdf.open(simple_pdf)
    fp = doc.fingerprint()
    assert isinstance(fp, str)
    assert len(fp) > 0
