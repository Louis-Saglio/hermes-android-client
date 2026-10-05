"""Minimal tui_gateway JSON-RPC-over-WebSocket client for live protocol probes.

Generic: reads base URL + session token from env or .probe/token. No machine-specific
values. Used by the pNN_*.py probe scenarios; captures are written raw (caller
sanitizes before publishing anything).

Frame shapes (verified in tui_gateway/ws.py):
- server event:  {"jsonrpc":"2.0","method":"event","params":{"type":<name>,"payload":{...}}}
- server→client request: {"jsonrpc":"2.0","id":"srq-N","method":<name>,"params":{...}}  (must be answered)
- rpc response:  {"jsonrpc":"2.0","result"|"error":...,"id":<id>}
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import time

from typing import Any

import websockets


def load_token(repo_root: pathlib.Path) -> str:
    if tok := os.environ.get("GATEWAY_TOKEN"):
        return tok.strip()
    return (repo_root / ".probe" / "token").read_text().strip()


def load_base_url(repo_root: pathlib.Path) -> str:
    return os.environ.get("GATEWAY_URL", "ws://127.0.0.1:9877/api/ws")


class Capture:
    """Append-only frame log with monotonic timestamps."""

    def __init__(self) -> None:
        self.frames: list[dict] = []

    def add(self, direction: str, frame: dict) -> None:
        self.frames.append({"t": round(time.monotonic(), 3), "dir": direction, "frame": frame})

    def dump_jsonl(self, path: pathlib.Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            for entry in self.frames:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


class GW:
    def __init__(self, url: str, token: str, capture: Capture | None = None) -> None:
        self.url = f"{url}?token={token}" if "?" not in url else f"{url}&token={token}"
        self.capture = capture or Capture()
        self.ws = None
        self._pending: dict[str, asyncio.Future] = {}
        self._events: asyncio.Queue = asyncio.Queue()
        self._server_requests: asyncio.Queue = asyncio.Queue()
        self._reader: asyncio.Task | None = None

    async def __aenter__(self) -> "GW":
        self.ws = await websockets.connect(self.url, max_size=None)
        self._reader = asyncio.create_task(self._read_loop())
        return self

    async def __aexit__(self, *exc) -> None:
        if self._reader:
            self._reader.cancel()
        if self.ws:
            await self.ws.close()

    async def _read_loop(self) -> None:
        assert self.ws is not None
        try:
            async for raw in self.ws:
                frame = json.loads(raw)
                self.capture.add("in", frame)
                if "method" in frame and "id" in frame and frame.get("id") is not None and not str(frame["id"]).isdigit():
                    # server→client request (string id like "srq-7")
                    await self._server_requests.put(frame)
                elif "method" in frame:
                    await self._events.put(frame)
                else:
                    fut = self._pending.pop(str(frame.get("id")), None)
                    if fut and not fut.done():
                        fut.set_result(frame)
        except websockets.ConnectionClosed:
            pass

    async def rpc(self, method: str, params: dict | None = None, timeout: float = 30.0) -> dict:
        assert self.ws is not None
        req_id = str(int(time.time() * 1000) % 10**9) + "-" + method
        frame: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            frame["params"] = params
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        self.capture.add("out", frame)
        await self.ws.send(json.dumps(frame))
        return await asyncio.wait_for(fut, timeout)

    async def next_event(self, timeout: float = 30.0) -> dict:
        return await asyncio.wait_for(self._events.get(), timeout)

    async def next_server_request(self, timeout: float = 5.0) -> dict:
        return await asyncio.wait_for(self._server_requests.get(), timeout)

    async def answer_server_request(self, req: dict, result: dict) -> None:
        assert self.ws is not None
        frame = {"jsonrpc": "2.0", "id": req["id"], "result": result}
        self.capture.add("out", frame)
        await self.ws.send(json.dumps(frame))

    async def collect_until(self, pred, timeout: float = 60.0) -> list[dict]:
        """Drain events until pred(event) is true (that event included)."""
        out: list[dict] = []
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"collect_until timed out with {len(out)} events")
            ev = await self.next_event(timeout=remaining)
            out.append(ev)
            if pred(ev):
                return out


def ev_type(frame: dict) -> str:
    return (frame.get("params") or {}).get("type", "")
