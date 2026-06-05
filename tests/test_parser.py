"""parser 模块的单元测试"""
import io
from parser.factory import ParserFactory
from parser.pdf_parser import PDFParser
from parser.docx_parser import DOCXParser
from parser.models import ParsedSection, ParsedDocument


class TestParserFactory:
    """测试解析器工厂"""

    def test_factory_returns_pdf_parser_for_pdf_file(self):
        file = io.BytesIO(b"dummy")
        file.name = "test.pdf"
        parser = ParserFactory.get_parser(file)
        assert isinstance(parser, PDFParser)

    def test_factory_returns_docx_parser_for_docx_file(self):
        file = io.BytesIO(b"dummy")
        file.name = "test.docx"
        parser = ParserFactory.get_parser(file)
        assert isinstance(parser, DOCXParser)

    def test_factory_raises_for_unsupported_type(self):
        file = io.BytesIO(b"dummy")
        file.name = "test.txt"
        try:
            ParserFactory.get_parser(file)
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass

    def test_factory_handles_case_insensitivity(self):
        file = io.BytesIO(b"dummy")
        file.name = "TEST.PDF"
        parser = ParserFactory.get_parser(file)
        assert isinstance(parser, PDFParser)


class TestParserModels:
    """测试数据模型"""

    def test_parsed_section_creation(self):
        section = ParsedSection(title="标题", content="内容", page=1, level=1)
        assert section.title == "标题"
        assert section.content == "内容"
        assert section.page == 1
        assert section.level == 1
        assert str(section) == "ParsedSection(title='标题', content='内容', page=1, level=1)"

    def test_parsed_document_creation(self):
        section = ParsedSection(title=None, content="段落内容", page=1, level=0)
        doc = ParsedDocument(
            doc_id="abc123",
            filename="test.pdf",
            total_pages=5,
            sections=[section],
        )
        assert doc.doc_id == "abc123"
        assert doc.filename == "test.pdf"
        assert doc.total_pages == 5
        assert len(doc.sections) == 1
        assert doc.sections[0].content == "段落内容"
