import pytest

from src.opencode_client.files import File, FileInfo, Match


def test_file() -> None:
    c = File(added=1, path="/hello/world.txt", removed=0, status="added")
    assert (
        c.added == 1
        and c.path == "/hello/world.txt"
        and c.removed == 0
        and c.status == "added"
    )
    with pytest.raises(TypeError):
        File(**{"added": 1})  # type: ignore
    with pytest.raises(TypeError):
        File(
            **{  # type: ignore
                "added": 1,
                "path": "hello",
                "removed": 0,
                "status": "deleted",
                "hello": "ciao",
            }
        )


def test_file_info() -> None:
    c = FileInfo(
        name="hello",
        path="./hello.txt",
        absolute="/absolute/hello.txt",
        type="file",
        ignored=False,
    )
    assert (
        c.name == "hello"
        and c.path == "./hello.txt"
        and c.absolute == "/absolute/hello.txt"
        and c.type == "file"
        and not c.ignored
    )
    with pytest.raises(TypeError):
        FileInfo(**{"name": "hello"})  # type: ignore
    with pytest.raises(TypeError):
        FileInfo(
            **{  # type: ignore
                "name": "hello",
                "path": "./hello.txt",
                "absolute": "/absolute/hello.txt",
                "type": "file",
                "ignored": False,
                "hello": "ciao",
            }
        )


def test_match() -> None:
    c = Match(
        path={"text": "hello.txt"},
        lines=1,
        line_number=0,
        absolute_offset=10,
        submatches=[],
    )
    assert (
        c.path == {"text": "hello.txt"}
        and c.lines == 1
        and c.line_number == 0
        and c.absolute_offset == 10
        and c.submatches == []
    )
    with pytest.raises(TypeError):
        Match(**{"path": {"text": "hello.txt"}})  # type: ignore
    with pytest.raises(TypeError):
        Match(
            **{  # type: ignore
                "path": {"text": "hello.txt"},
                "lines": 1,
                "line_number": 0,
                "absolute_offset": 10,
                "submatches": [],
                "hello": "ciao",
            }
        )
