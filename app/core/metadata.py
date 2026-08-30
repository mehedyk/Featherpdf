"""
core/metadata.py
Metadata read/write and password-protected save.
"""
import pymupdf

STANDARD_FIELDS = ["title", "author", "subject", "keywords", "creator", "producer"]


def get_display_metadata(pdf_doc):
    meta = pdf_doc.get_metadata()
    return {k: meta.get(k, "") for k in STANDARD_FIELDS}


def update_metadata(pdf_doc, fields: dict):
    meta = pdf_doc.get_metadata()
    meta.update({k: v for k, v in fields.items() if k in STANDARD_FIELDS})
    pdf_doc.set_metadata(meta)


def save_with_password(pdf_doc, path, user_password, owner_password=None):
    """Save an encrypted copy; does not affect the currently open in-memory doc's password state."""
    perm = int(
        pymupdf.PDF_PERM_ACCESSIBILITY
        | pymupdf.PDF_PERM_PRINT
        | pymupdf.PDF_PERM_COPY
        | pymupdf.PDF_PERM_ANNOTATE
    )
    encrypt_meth = pymupdf.PDF_ENCRYPT_AES_256
    pdf_doc.doc.save(
        path,
        encryption=encrypt_meth,
        owner_pw=owner_password or user_password,
        user_pw=user_password,
        permissions=perm,
        garbage=4,
        deflate=True,
    )
