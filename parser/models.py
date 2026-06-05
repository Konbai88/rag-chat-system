from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedSection:
    title:Optional[str]
    content:str
    page:int
    level:int

@dataclass
class ParsedDocument:
    doc_id:str
    filename:str
    total_pages:int
    sections:list[ParsedSection]
