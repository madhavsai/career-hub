"""
Career Hub - a single local UI over the freelancing and job-search research
already in this workspace.

Content is static (built by build_content.py). The only thing this server owns
is the tracker state: a status and a note per company, platform or role, kept
in state.json beside this file.

    uvicorn main:app --reload --port 8020
"""

import json
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"
STATE_FILE = BASE / "state.json"

STATUSES = ["interested", "applied", "in-progress", "rejected", "closed"]

app = FastAPI(title="Career Hub")

# state.json is rewritten whole on every change; it is a few KB at most, and a
# lock keeps two quick clicks from interleaving writes.
_lock = threading.Lock()


def load_state():
    if not STATE_FILE.exists():
        return {"items": {}}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Never lose the file to a parse error - move it aside and start clean.
        STATE_FILE.replace(STATE_FILE.with_suffix(".json.corrupt"))
        return {"items": {}}
    data.setdefault("items", {})
    return data


def save_state(state):
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_FILE)


class Item(BaseModel):
    key: str = Field(min_length=1, max_length=400)
    label: str = Field(default="", max_length=400)
    section: str = Field(default="", max_length=120)
    status: str = ""
    note: str = Field(default="", max_length=4000)


@app.get("/api/state")
def get_state():
    return load_state()


@app.post("/api/state")
def upsert_item(item: Item):
    if item.status and item.status not in STATUSES:
        raise HTTPException(400, "unknown status: %s" % item.status)
    with _lock:
        state = load_state()
        if not item.status and not item.note.strip():
            state["items"].pop(item.key, None)          # cleared - drop the row
        else:
            state["items"][item.key] = {
                "label": item.label,
                "section": item.section,
                "status": item.status,
                "note": item.note,
            }
        save_state(state)
        return state


@app.delete("/api/state/{key:path}")
def delete_item(key: str):
    with _lock:
        state = load_state()
        state["items"].pop(key, None)
        save_state(state)
        return state


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/", StaticFiles(directory=STATIC), name="static")
