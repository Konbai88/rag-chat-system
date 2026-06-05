from typing import Union
from io import IOBase
from parser.base import BaseParser
from parser.models import ParsedDocument, ParsedSection
from utils.md5 import get_string_md5


class TXTParser(BaseParser):
    """TXT 文件解析器：按行分段"""

    def parse(self, file: Union[IOBase, str]) -> ParsedDocument:
        """读取 TXT 文件内容，每行作为一个分段"""
        content = _read_file(file)

        doc_id = get_string_md5(getattr(file, "name", str(file)))
        filename = getattr(file, "name", str(file))
        lines = content.splitlines()
        total_lines = len([l for l in lines if l.strip()])

        sections: list[ParsedSection] = []
        idx = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            idx += 1
            sections.append(
                ParsedSection(title=None, content=stripped, page=idx, level=0)
            )

        return ParsedDocument(doc_id, filename, total_lines, sections)


def _read_file(file: Union[IOBase, str]) -> str:
    """从文件对象或路径读取文本内容"""
    if isinstance(file, str):
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    # IOBase 对象（来自 Streamlit 上传）
    content = file.read()
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="ignore")
    return content
