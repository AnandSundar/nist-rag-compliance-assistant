import pypdf
from config import settings


def load_pdf() -> str:
    reader = pypdf.PdfReader(settings.pdf_path)
    num_pages = len(reader.pages)
    print(f"Loading PDF with {num_pages} pages...")

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    full_text = "\n".join(text_parts)
    print(f"Extracted {len(full_text)} characters from {num_pages} pages")
    return full_text
