from __future__ import annotations
import hashlib
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1024 * 1024

def sha256_for_file(path: str | Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    file_path = Path(path)
    digest = hashlib.sha256()

    with file_path.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()
