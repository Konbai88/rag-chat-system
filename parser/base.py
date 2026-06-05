from abc import ABC, abstractmethod
from parser.models import ParsedDocument


class BaseParser(ABC):
    """解析器抽象基类"""

    @abstractmethod
    def parse(self, file) -> ParsedDocument:
        """解析文件，返回结构化文档"""
        ...
