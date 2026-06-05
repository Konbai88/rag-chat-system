from typing import Union
from io import IOBase
from parser.base import BaseParser
from parser.pdf_parser import PDFParser
from parser.docx_parser import DOCXParser


class ParserFactory:
    """解析器工厂：根据文件类型返回对应解析器"""

    @staticmethod
    def get_parser(file: Union[IOBase, str]) -> BaseParser:
        """根据文件后缀返回对应的解析器实例"""
        filename = getattr(file, "name", str(file))
        filename = filename.lower()
        if filename.endswith(".pdf"):
            return PDFParser()
        elif filename.endswith(".docx"):
            return DOCXParser()
        else:
            raise ValueError(f"不支持该文件类型 {filename}")
