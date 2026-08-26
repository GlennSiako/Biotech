"""Stage 2a: fetch structure files from RCSB, with an on-disk cache.

Cached by PDB ID so a re-run of a campaign does not re-download, and so a run is
replayable offline from its cache directory.

mmCIF is the default rather than PDB format: the legacy PDB format cannot
represent large structures or chain identifiers longer than one character, and
RCSB no longer guarantees a PDB-format file exists for every entry.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

log = logging.getLogger(__name__)

RCSB_FILE = "https://files.rcsb.org/download/{pdb_id}.{fmt}"
DEFAULT_CACHE = Path("data/structures")


class FetchError(RuntimeError):
    """Raised when a structure file cannot be retrieved."""


def fetch_structure(
    pdb_id: str,
    *,
    fmt: str = "cif",
    cache_dir: Path = DEFAULT_CACHE,
    session: requests.Session | None = None,
    timeout: float = 60.0,
    retries: int = 3,
    force: bool = False,
) -> Path:
    """Download a structure file, returning the local path.

    Returns the cached copy unless `force` is set.
    """
    pdb_id = pdb_id.upper()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{pdb_id}.{fmt}"

    if path.exists() and path.stat().st_size > 0 and not force:
        log.debug("using cached %s", path)
        return path

    url = RCSB_FILE.format(pdb_id=pdb_id, fmt=fmt)
    sess = session or requests.Session()
    last: Exception | None = None

    for attempt in range(retries):
        try:
            resp = sess.get(url, timeout=timeout)
            resp.raise_for_status()
            # Write via a temporary file so an interrupted download never leaves
            # a truncated file that a later run would treat as a valid cache hit.
            tmp = path.with_suffix(path.suffix + ".part")
            tmp.write_bytes(resp.content)
            tmp.replace(path)
            log.info("fetched %s (%d bytes)", pdb_id, len(resp.content))
            return path
        except requests.RequestException as exc:
            last = exc
            if attempt < retries - 1:
                delay = 2 ** attempt
                log.warning("fetch of %s failed (%s); retrying in %ss", pdb_id, exc, delay)
                time.sleep(delay)

    raise FetchError(f"could not fetch {pdb_id}: {last}") from last
