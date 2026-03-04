from __future__ import annotations

import json
import os
from pathlib import Path


class PinStorage:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._pins: set[str] = set()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text())
                self._pins = set(data.get("pinned", []))
            except (json.JSONDecodeError, KeyError):
                self._pins = set()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"pinned": sorted(self._pins)}))
        os.rename(tmp, self._path)

    def list_pins(self) -> set[str]:
        return set(self._pins)

    def add(self, session_id: str) -> None:
        self._pins.add(session_id)
        self._save()

    def remove(self, session_id: str) -> None:
        self._pins.discard(session_id)
        self._save()
