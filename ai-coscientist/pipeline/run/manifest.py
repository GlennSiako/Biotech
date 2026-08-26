"""Run manifests.

Section 5.2 of the plan requires every run to be replayable from its manifest
alone. That is only true if the manifest records what was chosen *and why the
alternatives were not* -- a manifest listing only the winner cannot explain a
campaign that went wrong.
"""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 1


@dataclass
class RunManifest:
    run_id: str
    created_at: str
    query: str
    region: tuple[int, int] | None
    target: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] | None = None
    chosen: dict[str, Any] | None = None
    preparation: dict[str, Any] | None = None
    structure_file: str | None = None
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": MANIFEST_VERSION,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "query": self.query,
            "region": list(self.region) if self.region else None,
            "target": self.target,
            "candidates": self.candidates or [],
            "chosen": self.chosen,
            "preparation": self.preparation,
            "structure_file": self.structure_file,
            "errors": self.errors or [],
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
        }

    def write(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "manifest.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=False))
        return path
