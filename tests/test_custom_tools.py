import pytest
import os

from pathlib import Path
from src.opencode_client.custom_tools import CustomTool


def test_custom_tool_validation() -> None:
    ct = CustomTool(
        name="say_hello",
        description="a tool to say hello",
        fn="return `hello ${args.name}!`",
        args={
            "name": {
                "description": "the name of the person to say hello to",
                "type": "string",
            }
        },
    )
    assert ct.name == "say_hello"
    assert ct.description == "a tool to say hello"
    assert ct.fn == "return `hello ${args.name}!`"
    assert ct.args == {
        "name": {
            "description": "the name of the person to say hello to",
            "type": "string",
        }
    }
    ctd = {
        "name": "say_hello",
        "description": "a tool to say hello",
        "fn": "return `hello ${args.name}!`",
        "args": {
            "name": {
                "description": "the name of the person to say hello to",
                "type": "string",
            }
        },
    }
    ct = CustomTool(**ctd)  # type: ignore
    assert ct.name == "say_hello"
    assert ct.description == "a tool to say hello"
    assert ct.fn == "return `hello ${args.name}!`"
    assert ct.args == {
        "name": {
            "description": "the name of the person to say hello to",
            "type": "string",
        }
    }
    with pytest.raises(TypeError):
        ctd = {"name": "say_hello", "description": "a tool to say hello"}
        CustomTool(**ctd)  # type: ignore


def test_custom_tool_to_file() -> None:
    if Path(".opencode/tool/say_bye.ts").exists():
        os.remove(".opencode/tool/say_bye.ts")
    ct = CustomTool(
        name="say Bye",
        description="a tool to say bye",
        fn="return `bye ${args.name}!`",
        args={
            "name": {
                "description": "the name of the person to say bye to",
                "type": "string",
            }
        },
    )
    ct.to_file()
    assert (
        Path(".opencode/tool/say_bye.ts").exists()
        and Path(".opencode/tool/say_bye.ts").is_file()
    )
    if not Path(".opencode/tool/say_hello.ts").exists():
        Path(".opencode/tool/say_hello.ts").touch(mode=777)
    ct = CustomTool(
        name="say_hello",
        description="a tool to say hello",
        fn="return `hello ${args.name}!`",
        args={
            "name": {
                "description": "the name of the person to say hello to",
                "type": "string",
            }
        },
    )
    with pytest.raises(ValueError):
        ct.to_file()
