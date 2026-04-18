from pypdf import PdfReader

def extract_pdf_text(file_path: str) -> str:
    """
    🧠 提取PDF文本内容
    """
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text