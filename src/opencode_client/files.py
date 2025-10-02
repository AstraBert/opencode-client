from typing import Literal, Any
from dataclasses import dataclass


FileOperation = Literal["read", "get_status", "search_by_text", "search_by_name"]


@dataclass
class File:
    added: int
    path: str
    removed: int
    status: Literal["added", "deleted", "modified"]


@dataclass
class Match:
    path: str
    lines: Any
    line_number: int
    absolute_offset: int
    submatches: Any


@dataclass
class FileInfo:
    name: str
    path: str
    absolute: str
    type: Literal["file", "directory"]
    ignored: bool
