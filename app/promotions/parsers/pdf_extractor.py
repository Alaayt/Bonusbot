import io

from pypdf import PdfReader


def extract_text_from_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text).strip()


def extract_text_from_pdf_path(path: str) -> str:
    with open(path, "rb") as f:
        return extract_text_from_pdf_bytes(f.read())
