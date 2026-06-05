from parser.base import BaseParser
from parser.models import ParsedDocument, ParsedSection
from utils.md5 import get_string_md5
import fitz


class PDFParser(BaseParser):
    """PDF 文件解析器"""

    def parse(self, file) -> ParsedDocument:
        doc = fitz.open(file)
        page_num = 1
        doc_id = get_string_md5(getattr(file, "name", str(file)))
        filename = getattr(file, "name", str(file))
        total_pages = len(doc)
        sections: list[ParsedSection] = []
        for page in doc:
            text = page.get_text()
            if not text.strip():
                continue
            sections.append(
                ParsedSection(title=None, content=text, page=page_num, level=0)
            )
            page_num += 1
        return ParsedDocument(doc_id, filename, total_pages, sections)
