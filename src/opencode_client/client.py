import httpx
import warnings

from dataclasses import asdict
from typing import AsyncIterator, Optional, Union, List
from contextlib import asynccontextmanager
from .session import Session, UserMessage, AssistantMessage, TextPart, FilePart
from .files import FileOperation, File, Match, ReadFile

class OpenCodeClient:
    def __init__(self, base_url: str, model_provider: str, model: str, timeout: int = 600) -> None:
        self.base_url = base_url
        self.model_provider = model_provider
        self.model = model
        self.timeout = timeout
        self._current_session: Optional[Session] = None
        self.chat_history: List[Union[UserMessage, AssistantMessage]] = []
    
    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            yield client

    async def create_current_session(self, title: Optional[str] = None, parent_id: Optional[str] = None) -> Session:
        async with self._get_client() as client:
            res = await client.post("/session", json={"parentID": parent_id or "", "title": title})
            res.raise_for_status()
            self._current_session = Session(**res.json())
            return self._current_session
    
    async def list_sessions(self) -> list[Session]:
        async with self._get_client() as client:
            res = await client.get("/session")
            res.raise_for_status()
            payload = res.json()
            sessions = []
            for session in payload:
                sessions.append(Session(**session))
            return sessions
    
    async def _delete_session(self, session_id: str):
        async with self._get_client() as client:
            res = await client.delete(f"/session/{session_id}")
            res.raise_for_status()

    async def _update_session(self, session_id: str, title: str):
        async with self._get_client() as client:
            res = await client.patch(f"/session/{session_id}", json={"title": title})
            res.raise_for_status()

    async def _abort_session(self, session_id: str):
        async with self._get_client() as client:
            res = await client.post(f"/session/{session_id}/abort")
            res.raise_for_status()

    async def _send_message_to_session(self, session_id: str, message: UserMessage) -> AssistantMessage:
        async with self._get_client() as client:
            res = await client.post(f"/session/{session_id}/message", json=asdict(message))
            res.raise_for_status()
            return AssistantMessage(**res.json())

    async def _perform_file_operation(self, operation: FileOperation, query: Optional[str] = None) -> Union[List[File], List[Match], List[str], ReadFile]:
        if not query and operation != "get_status":
            raise ValueError(f"Operation {operation} requires a query value.")
        async with self._get_client() as client:
            if operation == "get_status":
                res = await client.get("/file/status")
                res.raise_for_status()
                files = []
                for f in res.json():
                    files.append(File(**f))
                return files
            elif operation == "read":
                res = await client.get(f"/file?path={query}")
                res.raise_for_status()
                return ReadFile(**res.json())
            elif operation == "search_by_name":
                res = await client.get(f"/find/file?query={query}")
                res.raise_for_status()
                return res.json()
            else:
                res = await client.get(f"/find?pattern={query}")
                res.raise_for_status()
                matches = []
                for match in res.json():
                    matches.append(Match(**match))
                return matches

    async def delete_session(self, session_id: Optional[str] = None) -> None:
        session_id = session_id or (self._current_session.id if self._current_session else None)
        if not session_id:
            raise ValueError("No session ID provided and no session ID available from current session")
        await self._delete_session(session_id)
    
    async def update_session(self, session_id: Optional[str] = None, title: Optional[str] = None) -> None:
        if not title:
            return
        else:
            session_id = session_id or (self._current_session.id if self._current_session else None)
            if not session_id:
                raise ValueError("No session ID provided and no session ID available from current session")
            await self._update_session(session_id, title)
    
    async def abort_session(self, session_id: Optional[str] = None) -> None:
        session_id = session_id or (self._current_session.id if self._current_session else None)
        if not session_id:
            raise ValueError("No session ID provided and no session ID available from current session")
        await self._abort_session(session_id)

    async def send_message(self, text: Union[str, List[str]], file: Optional[Union[str, List[str]]] = None, system_message: Optional[str] = None, session_id: Optional[str] = None) -> AssistantMessage:
        session_id = session_id or (self._current_session.id if self._current_session else None)
        if not session_id:
            raise ValueError("No session ID provided and no session ID available from current session")
        parts = []
        if isinstance(text, list):
            for t in text:
                parts.append(TextPart.from_string(t))
        else:
            parts.append(TextPart.from_string(text))
        if file:
            if isinstance(file, list):
                for f in file:
                    if f.startswith(("http://", "https://", "ftp://", "file://")):
                        parts.append(FilePart.from_url(f))
                    else:
                        try:
                            parts.append(FilePart.from_file(f))
                        except ValueError as e:
                            warnings.warn(f"It was not possible to include file {f} as FilePart because of: {e}")
                            continue
            else:
                if file.startswith(("http://", "https://", "ftp://", "file://")):
                    parts.append(FilePart.from_url(file))
                else:
                    try:
                        parts.append(FilePart.from_file(file))
                    except ValueError as e:
                        warnings.warn(f"It was not possible to include file {file} as FilePart because of: {e}")
        user_message = UserMessage(modelID=self.model, providerID=self.model_provider, parts=parts, system=system_message)
        self.chat_history.append(user_message)    
        assistant_message = await self._send_message_to_session(session_id=session_id, message=user_message)
        self.chat_history.append(assistant_message)
        return assistant_message
    
    async def search_file_by_name(self, name: str) -> List[str]:
        return await self._perform_file_operation(operation="search_by_name", query=name) # type: ignore


    async def search_file_by_text(self, pattern: str) -> List[Match]:
        return await self._perform_file_operation(operation="search_by_text", query=pattern) # type: ignore
        

    async def read_file(self, path: str) -> ReadFile:
        return await self._perform_file_operation(operation="read", query=path) # type: ignore

    async def get_files_status(self) -> List[File]:
        return await self._perform_file_operation(operation="get_status") # type: ignore

    




    