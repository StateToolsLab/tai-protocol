#!/usr/bin/env python3
"""Archive an issued TAI Task verbatim, without overwriting or performing Git actions.

Python 3.9+, standard library only. The input uses a flat UTF-8 frontmatter subset.
A trusted --expected-sha256 checks the upstream original; without it, only the local
snapshot is verified. The caller must serialize Task updates and perform Gate/reset.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple


class ArchiveError(ValueError):
    """An invalid Task, integrity failure, or conflicting archive."""


@dataclass(frozen=True)
class ArchiveResult:
    path: Path
    sha256: str
    created: bool


def task_identity(data: bytes) -> Tuple[str, int]:
    """Read identifiers without normalizing or rewriting the original bytes."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise ArchiveError("UTF-8 BOM is not supported; resolve encoding before issuance")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArchiveError("Task must be valid UTF-8") from exc
    if "\x00" in text:
        raise ArchiveError("Task contains a NUL byte")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ArchiveError("Task must start with a frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ArchiveError("Task frontmatter is not closed") from exc
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([a-z_][a-z0-9_]*):[ \t]*(.*)", line)
        if not match:
            raise ArchiveError("Only flat frontmatter fields are supported")
        key, value = match.groups()
        if key in fields:
            raise ArchiveError("Duplicate frontmatter field: " + key)
        # Comments are parsed for validation only; the archive retains them exactly.
        fields[key] = re.split(r"[ \t]+#", value, maxsplit=1)[0].strip()
    task_id = fields.get("task_id", "")
    revision = fields.get("revision", "")
    if not re.fullmatch(r"T-[0-9]{3,}", task_id):
        raise ArchiveError("task_id must be T- followed by at least three digits")
    if not re.fullmatch(r"[1-9][0-9]*", revision):
        raise ArchiveError("revision must be a positive integer without leading zeroes")
    if fields.get("status") != "active":
        raise ArchiveError("Only issued status: active Tasks are archived, not placeholders")
    if not "\n".join(lines[end + 1:]).strip():
        raise ArchiveError("Task body is empty")
    return task_id, int(revision)


def _existing_matches(path: Path, data: bytes) -> bool:
    if path.is_symlink():
        raise ArchiveError("Refusing a symlink archive destination: " + str(path))
    if not path.exists():
        return False
    if not path.is_file() or path.read_bytes() != data:
        raise ArchiveError("Archive conflict; refusing to overwrite: " + str(path))
    return True


def archive_task(
    source: Path,
    archive_dir: Path,
    expected_sha256: Optional[str] = None,
) -> ArchiveResult:
    """Publish a byte-identical snapshot, or accept an identical existing snapshot.

    A hard link publishes a completed temporary file without replacing an existing
    name. Unsupported filesystems fail closed. This is not a distributed lock or
    a defense against an adversary modifying the surrounding filesystem.
    """
    source = Path(source)
    archive_dir = Path(archive_dir)
    if source.is_symlink():
        raise ArchiveError("Refusing a symlink Task source")
    data = source.read_bytes()
    task_id, revision = task_identity(data)
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
            raise ArchiveError("Expected SHA256 must contain exactly 64 hexadecimal characters")
        if digest != expected_sha256.lower():
            raise ArchiveError("Task does not match the trusted expected SHA256")
    if archive_dir.is_symlink():
        raise ArchiveError("Refusing a symlink archive directory")
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / (task_id + "_task_r" + str(revision) + ".md")
    if _existing_matches(target, data):
        return ArchiveResult(target, digest, False)

    temporary = None
    created = False
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".tai-task-", dir=str(archive_dir), delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if source.is_symlink() or source.read_bytes() != data:
            raise ArchiveError("Task changed during archiving; serialize Task updates")
        try:
            os.link(str(temporary), str(target))
            created = True
        except FileExistsError:
            if not _existing_matches(target, data):
                raise ArchiveError("Archive destination changed concurrently")
        if not _existing_matches(target, data):
            raise ArchiveError("Archive verification failed")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return ArchiveResult(target, digest, created)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, default=Path(".ai/task.md"))
    parser.add_argument("--archive-dir", type=Path, default=Path(".ai/archive"))
    parser.add_argument("--expected-sha256", help="SHA256 from an independent, trusted issuance record")
    args = parser.parse_args(argv)
    try:
        result = archive_task(args.task, args.archive_dir, args.expected_sha256)
    except (ArchiveError, OSError, ValueError) as exc:
        print("tai archive: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps({
        "path": str(result.path),
        "sha256": result.sha256,
        "created": result.created,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
