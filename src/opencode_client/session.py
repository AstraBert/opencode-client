import os
import mimetypes

from dataclasses import dataclass, field, asdict
from typing import List, Union, TypedDict, Any, Optional
from typing_extensions import NotRequired
from pathlib import Path
from .custom_tools import CustomTool


class Time(TypedDict):
    created: int
    updated: int


class ToolsDict(TypedDict):
    bash: NotRequired[bool]
    edit: NotRequired[bool]
    write: NotRequired[bool]
    read: NotRequired[bool]
    grep: NotRequired[bool]
    glob: NotRequired[bool]
    list: NotRequired[bool]
    patch: NotRequired[bool]
    todowrite: NotRequired[bool]
    todoread: NotRequired[bool]
    webfetch: NotRequired[bool]


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
    def from_string(cls, string: str) -> "TextPart":
        return cls(text=string)


@dataclass
class FileSourceText:
    end: int
    start: int
    value: str

    @classmethod
    def from_file(cls, file: str) -> "FileSourceText":
        with open(file, "r") as f:
            content = f.read()
        return cls(start=0, end=len(content), value=content)


@dataclass
class FileSource:
    path: str
    text: FileSourceText
    type: str = "file"

    @classmethod
    def from_file(cls, file: str) -> "FileSource":
        return cls(path=file, text=FileSourceText.from_file(file), type="file")


def _raw_guess_mimetypes(file: str) -> Optional[str]:
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
    def from_file(cls, file: str) -> "FilePart":
        abs_path = str(Path(file).resolve())
        if os.path.exists(abs_path) and os.path.isfile(abs_path):
            mimetype = _raw_guess_mimetypes(abs_path)
            if not mimetype:
                raise ValueError(
                    "It was not possible to guess the mimetype for your file from the provided path"
                )
            if not mimetype.startswith("text/"):
                raise ValueError(f"Unsopported type: {mimetype}")
            return cls(
                mime=mimetype,
                url="file://" + abs_path,
                type="file",
                filename=file,
                source=FileSource.from_file(abs_path),
            )
        else:
            raise ValueError("The provided file does not exist")

    @classmethod
    def from_url(cls, url: str) -> "FilePart":
        mimetype = _raw_guess_mimetypes(url)
        if not mimetype:
            raise ValueError(
                "It was not possible to guess the mimetype for your file from the provided URL"
            )
        return cls(url=url, mime=mimetype)


@dataclass
class UserMessage:
    modelID: str
    providerID: str
    parts: List[Union[TextPart, FilePart]]
    messageID: str = ""
    mode: str = "build"
    system: str = ""
    tools: Optional[ToolsDict] = None
    custom_tools: List[CustomTool] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tools is None:
            self.tools = {}
        if len(self.custom_tools) > 0:
            for tool in self.custom_tools:
                tool.to_file()
                self.tools[tool.name.lower().replace(" ", "_")] = True  # type: ignore
            self.custom_tools.clear()

    def to_dict(self) -> dict[str, Any]:
        dct = asdict(self)
        dct.pop("custom_tools")
        return dct

    @classmethod
    def from_dict(cls, dct: dict) -> "UserMessage":
        if "custom_tools" not in dct:
            dct["custom_tools"] = []
        return cls(**dct)

    def to_string(self, include_system_prompt: bool = False) -> str:
        s = "<user>"
        if include_system_prompt and self.system:
            s += f"\n\t<system>{self.system}</system>\n"
        for part in self.parts:
            if isinstance(part, TextPart):
                s += f"\n\t<text>{part.text}</text>\n"
            else:
                if part.source != {}:
                    if isinstance(part.source, FileSource):
                        file_content = part.source.text.value
                    else:
                        file_content = part.source.get("text", {}).get("value", "")
                else:
                    file_content = part.filename if part.filename else part.url
                s += f"\n\t<file>{file_content}</file>\n"
        s += "</user>"
        return s


class AssistantMessageInfoPath(TypedDict):
    cwd: str
    root: str


class AssistantMessageInfoTokensCache(TypedDict):
    read: int
    write: int


class AssistantMessageInfoTokens(TypedDict):
    input: int
    output: int
    reasoning: int
    cache: AssistantMessageInfoTokensCache


class AssistantMessageInfoTime(TypedDict):
    started: int
    completed: NotRequired[int]


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
    error: NotRequired[Any]
    summary: NotRequired[bool]


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
    parts: List[
        Union[
            AssistantMessageStepStart,
            AssistantMessageStepWithText,
            AssistantMessageStepFinish,
        ]
    ] = field(default_factory=list)
    blocked: bool = False

    def to_string(self, include_system_prompt: bool = False) -> str:
        s = "<assistant>"
        if include_system_prompt:
            for text in self.info["system"]:
                s += f"\n\t<system>{text}</system>\n"
        for part in self.parts:
            if "text" in part:
                if part["type"] == "reasoning":
                    s += f"\n\t<reasoning>{part['text']}</reasoning>\n"  # type: ignore
                else:
                    s += f"\n\t<answer>{part['text']}</answer>\n"  # type: ignore
        s += "</assistant>"
        return s
