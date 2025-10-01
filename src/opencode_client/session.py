import os
import mimetypes

from dataclasses import dataclass, field
from typing import List, Union, Dict, TypedDict
from pathlib import Path

class Time(TypedDict):
    created: int
    updated: int

@dataclass
class Session:
    id: str
    title: str 
    version: str
    projectID: str
    directory: str
    time: Time
    parentID: str = ""

@dataclass
class TextPart:
    text: str
    type: str = "text"

    @classmethod
    def from_string(cls, string: str):
        return cls(text=string)

@dataclass
class FileSourceText:
    end: int
    start: int
    value: str

    @classmethod
    def from_file(cls, file: str):
        with open(file, "r") as f:
            content = f.read()
        return cls(start=0, end=len(content), value=content)

@dataclass 
class FileSource:
    path: str
    text: FileSourceText
    type: str = "file"

    @classmethod
    def from_file(cls, file: str):
        return cls(path=file, text=FileSourceText.from_file(file), type="file")

def _raw_guess_mimetypes(file: str):
    mime_type, _ = mimetypes.guess_type(file)
    return mime_type

@dataclass
class FilePart:
    mime: str
    url: str
    type: str = "file"
    id: str = ""
    filename: str = ""
    source: FileSource | dict = field(default_factory=dict)

    @classmethod
    def from_file(cls, file: str):
        abs_path = str(Path(file).resolve())
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            mimetype = _raw_guess_mimetypes(abs_path)
            if not mimetype:
                raise ValueError("It was not possible to guess the mimetype for your file from the provided path")
            if not mimetype.startswith("text/"):
                raise ValueError(f"Unsopported type: {mimetype}")
            return cls(mime=mimetype, url="file://"+abs_path, type="file", filename=file, source=FileSource.from_file(abs_path))
        else:
            raise ValueError("The provided file does not exist")
    
    @classmethod
    def from_url(cls, url: str):
        mimetype = _raw_guess_mimetypes(url)
        if not mimetype:
            raise ValueError("It was not possible to guess the mimetype for your file from the provided URL")
        return cls(url=url, mime=mimetype)
        
@dataclass
class UserMessage:
    modelID: str
    providerID: str
    parts: List[Union[TextPart, FilePart]]
    messageID: str = ""
    mode: str = "build"
    system: str = ""
    tools: Dict[str, bool] = field(default_factory=dict)

class AssistantMessageInfoPath(TypedDict):
    cwd: str
    root: str

class  AssistantMessageInfoTokensCache(TypedDict):
    read: int
    write: int

class AssistantMessageInfoTokens(TypedDict):
    input: int
    output: int
    reasoning: int
    cache: AssistantMessageInfoTokensCache

class AssistantMessageInfoTime(TypedDict):
    started: int
    completed: int

class AssistantMessageInfo(TypedDict):
    id: str
    system: list[str]
    mode: str
    path: AssistantMessageInfoPath
    cost: int | float
    tokens: AssistantMessageInfoTokens
    modelID: str
    providerID: str
    time: AssistantMessageInfoTime
    sessionID: str

class AssistantMessageStepStart(TypedDict):
    id: str
    messageID: str
    sessionID: str
    type: str

class AssistantMessageStepFinish(TypedDict):
    id: str
    messageID: str
    sessionID: str
    type: str
    tokens: AssistantMessageInfoTokens

class AssistantMessageStepWithText(TypedDict):
    id: str
    messageID: str
    sessionID: str
    type: str
    text: str

@dataclass 
class AssistantMessage:
    info: AssistantMessageInfo
    parts: List[Union[AssistantMessageStepStart, AssistantMessageStepWithText, AssistantMessageStepFinish]]
    bloked: bool
