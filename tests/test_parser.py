"""parser 模块的单元测试"""
import io
from parser.factory import ParserFactory
from parser.pdf_parser import PDFParser
from parser.docx_parser import DOCXParser
from parser.models import ParsedSection, ParsedDocument
from parser.txt_parser import TXTParser


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

    def test_factory_returns_txt_parser_for_txt_file(self):
        file = io.BytesIO(b"hello world")
        file.name = "test.txt"
        parser = ParserFactory.get_parser(file)
        assert isinstance(parser, TXTParser)

    def test_factory_raises_for_unsupported_type(self):
        file = io.BytesIO(b"dummy")
        file.name = "test.xyz"
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


class TestTXTParser:
    """测试 TXT 解析器"""

    def test_parse_simple_text(self):
        file = io.BytesIO("第一行\n第二行\n第三行".encode("utf-8"))
        file.name = "test.txt"
        parser = TXTParser()
        doc = parser.parse(file)
        assert doc.filename == "test.txt"
        assert doc.total_pages == 3
        assert len(doc.sections) == 3
        assert doc.sections[0].content == "第一行"
        assert doc.sections[1].content == "第二行"
        assert doc.sections[2].content == "第三行"

    def test_parse_skips_empty_lines(self):
        file = io.BytesIO("行1\n\n\n行2".encode("utf-8"))
        file.name = "test.txt"
        parser = TXTParser()
        doc = parser.parse(file)
        assert len(doc.sections) == 2
        assert doc.sections[0].content == "行1"
        assert doc.sections[1].content == "行2"

    def test_file_path_string(self):
        import tempfile, os
        path = os.path.join(tempfile.gettempdir(), "_rag_test_tmp.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("从文件路径读取")
        parser = TXTParser()
        doc = parser.parse(path)
        assert doc.total_pages == 1
        assert doc.sections[0].content == "从文件路径读取"
        os.remove(path)


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
