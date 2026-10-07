"""Probe 06 — clarify flow: the agent calls the clarify tool → `clarify` server→client request
with questions[]; client answers {answers}. Captures to .probe/captures/p06-clarify.jsonl.

Run from repo root:  uv run --with websockets scripts/probe/p06_clarify.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from gw import GW, Capture, ev_type, load_base_url, load_token

ROOT = pathlib.Path(__file__).resolve().parents[2]


def short(obj, n=400):
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


async def main() -> None:
    cap = Capture()
    async with GW(load_base_url(ROOT), load_token(ROOT), cap) as gw:
        await gw.next_event(timeout=15)
        await gw.rpc("client.capabilities", {"server_requests": True})
        created = await gw.rpc("session.create", {"title": "probe-clarify"})
        sid = (created.get("result") or {}).get("session_id")

        await gw.rpc("prompt.submit", {
            "session_id": sid,
            "text": "Call the clarify tool right now with exactly these 2 questions: "
                    "qid 'color', question 'Pick a color', choices ['red','green','blue'], single-select; "
                    "qid 'nickname', question 'What nickname should I use for you?', no choices (free text). "
                    "After I answer, repeat my two answers back verbatim in one short sentence.",
        })

        req_task = asyncio.ensure_future(gw.next_server_request(timeout=120))
        done_task = asyncio.ensure_future(gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120))
        await asyncio.wait({req_task, done_task}, return_when=asyncio.FIRST_COMPLETED)
        if req_task.done():
            done_task.cancel()
            req = req_task.result()
            print("CLARIFY REQUEST:", short(req, 700))
            questions = (req.get("params") or {}).get("questions", [])
            answers = {q["qid"]: (q.get("choices") or ["PROBE_FREE_TEXT_123"])[1]
                       if q.get("choices") else "PROBE_FREE_TEXT_123" for q in questions}
            print("ANSWERING:", answers)
            await gw.answer_server_request(req, {"answers": answers})
            events = await gw.collect_until(lambda e: ev_type(e) == "message.complete", timeout=120)
            complete = [e for e in events if ev_type(e) == "message.complete"][-1]
            print("FINAL TEXT:", repr((complete.get("params") or {}).get("payload", {}).get("text", "")[:300]))
        else:
            req_task.cancel()
            complete = [e for e in done_task.result() if ev_type(e) == "message.complete"][-1]
            print("NO CLARIFY — textual end:", repr((complete.get("params") or {}).get("payload", {}).get("text", "")[:200]))

        cap.dump_jsonl(ROOT / ".probe" / "captures" / "p06-clarify.jsonl")
        print("CAPTURE WRITTEN:", len(cap.frames), "frames")


if __name__ == "__main__":
    asyncio.run(main())
