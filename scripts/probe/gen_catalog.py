"""Generate docs/contract-catalog.md from tui_gateway.contracts (doc strings only —
schemas stay in the vendored OpenRPC JSON). Run with the Hermes repo on sys.path:

    <hermes-repo>/scripts/run-in-hermes-env python3 scripts/probe/gen_catalog.py <hermes-repo>

Grouped by namespace; METHODS + SERVER_REQUESTS + EVENTS tables from contracts/registry.py.
"""

import pathlib
import sys
from collections import defaultdict

REPO = sys.argv[1]
sys.path.insert(0, REPO)

from tui_gateway import contracts  # noqa: F401  (fills the registry tables)
from tui_gateway.contracts.registry import EVENTS, METHODS, SERVER_REQUESTS

OUT = pathlib.Path(__file__).resolve().parents[2] / "docs" / "contract-catalog.md"


def group(table):
    by_ns = defaultdict(list)
    for name, entry in sorted(table.items()):
        by_ns[name.split(".")[0]].append(entry)
    return by_ns


def render_table(title, table, kind):
    lines = [f"\n## {title} ({len(table)})\n"]
    for ns, entries in group(table).items():
        lines.append(f"\n### `{ns}.*`\n")
        for e in entries:
            doc = (e.doc or "").strip().splitlines()[0] if e.doc else "—"
            lines.append(f"- `{e.name}` — {doc}")
    return lines


head = [
    "# tui_gateway contract catalog",
    "",
    f"Extracted from `tui_gateway/contracts` (doc strings) — {len(METHODS)} RPC methods, "
    f"{len(SERVER_REQUESTS)} server→client requests, {len(EVENTS)} events. "
    "Param/result/payload schemas: see `gateway-contract.openrpc.json` (same source, official generator).",
    "Regenerate: `<hermes-repo>/scripts/run-in-hermes-env python3 scripts/probe/gen_catalog.py <hermes-repo>`",
]

lines = head
lines += render_table("RPC methods", METHODS, "method")
lines += render_table("Server→client requests", SERVER_REQUESTS, "server_request")
lines += render_table("Events", EVENTS, "event")

OUT.write_text("\n".join(lines) + "\n")
print(f"written {OUT} ({len(METHODS)} methods, {len(SERVER_REQUESTS)} server requests, {len(EVENTS)} events)")
