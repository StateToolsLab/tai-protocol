#!/usr/bin/env python3
"""Archive TAI Task/Report originals, without overwriting or performing Git actions.

Python 3.9+, standard library only. The input uses a flat UTF-8 frontmatter subset.
A trusted --expected-sha256 checks the upstream original; without it, only the local
snapshot is verified. --report enables paired Gate archival (17-J). The caller must
serialize window updates and commit both archives with both resets. This helper
never resets windows, approves a Gate, runs Git, or starts a Worker.
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
from typing import Dict, Optional, Sequence, Tuple


class ArchiveError(ValueError):
    """An invalid document, integrity failure, or conflicting archive."""


@dataclass(frozen=True)
class ArchiveResult:
    path: Path
    sha256: str
    created: bool


def _document_fields(data: bytes) -> Dict[str, str]:
    """Parse validation fields only; never serialize or normalize archived bytes."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise ArchiveError("UTF-8 BOM is not supported; resolve encoding before issuance")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArchiveError("Document must be valid UTF-8") from exc
    if "\x00" in text:
        raise ArchiveError("Document contains a NUL byte")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ArchiveError("Document must start with a frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ArchiveError("Document frontmatter is not closed") from exc
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
    if not "\n".join(lines[end + 1:]).strip():
        raise ArchiveError("Document body is empty")
    return fields


def _identity(fields: Dict[str, str]) -> Tuple[str, int]:
    task_id = fields.get("task_id", "")
    revision = fields.get("revision", "")
    if not re.fullmatch(r"T-[0-9]{3,}", task_id):
        raise ArchiveError("task_id must be T- followed by at least three digits")
    if not re.fullmatch(r"[1-9][0-9]*", revision):
        raise ArchiveError("revision must be a positive integer without leading zeroes")
    return task_id, int(revision)


def task_identity(data: bytes) -> Tuple[str, int]:
    """Validate an issued Task while preserving its original bytes."""
    fields = _document_fields(data)
    identity = _identity(fields)
    if fields.get("status") != "active":
        raise ArchiveError("Only issued status: active Tasks are archived, not placeholders")
    return identity


def report_identity(data: bytes) -> Tuple[str, int]:
    """Validate a returned Git-adapter Report, not its acceptance or provenance."""
    fields = _document_fields(data)
    identity = _identity(fields)
    if fields.get("status") not in {"completed", "blocked", "failed"}:
        raise ArchiveError("Only returned Reports are archived, not placeholders")
    if fields.get("branch") != "claude/" + identity[0]:
        raise ArchiveError("Report branch must match its Task ID")
    if not re.fullmatch(r"[0-9a-fA-F]{7}", fields.get("commit", "")):
        raise ArchiveError("Report commit must be the seven-digit implementation/base SHA")
    return identity


def _existing_matches(path: Path, data: bytes) -> bool:
    if path.is_symlink():
        raise ArchiveError("Refusing a symlink archive destination: " + str(path))
    if not path.exists():
        return False
    if not path.is_file() or path.read_bytes() != data:
        raise ArchiveError("Archive conflict; refusing to overwrite: " + str(path))
    return True


def _read_source(source: Path) -> bytes:
    if source.is_symlink() or not source.is_file():
        raise ArchiveError("Source must be a regular, non-symlink file: " + str(source))
    return source.read_bytes()


def _digest(data: bytes, expected: Optional[str]) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if expected is not None:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ArchiveError("Expected SHA256 must contain exactly 64 hexadecimal characters")
        if digest != expected.lower():
            raise ArchiveError("Document does not match the trusted expected SHA256")
    return digest


def _target(archive_dir: Path, identity: Tuple[str, int], kind: str) -> Path:
    if archive_dir.is_symlink():
        raise ArchiveError("Refusing a symlink archive directory")
    return archive_dir / (identity[0] + "_" + kind + "_r" + str(identity[1]) + ".md")


def _publish(source: Path, target: Path, data: bytes, digest: str) -> ArchiveResult:
    """Publish one complete file with no overwrite; the pair is not a transaction."""
    if _read_source(source) != data:
        raise ArchiveError("Document changed during archiving; serialize window updates")
    archive_dir = target.parent
    if archive_dir.is_symlink():
        raise ArchiveError("Refusing a symlink archive directory")
    archive_dir.mkdir(parents=True, exist_ok=True)
    if _existing_matches(target, data):
        return ArchiveResult(target, digest, False)

    temporary = None
    created = False
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".tai-archive-", dir=str(archive_dir), delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if _read_source(source) != data:
            raise ArchiveError("Document changed during archiving; serialize window updates")
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


def archive_task(
    source: Path,
    archive_dir: Path,
    expected_sha256: Optional[str] = None,
) -> ArchiveResult:
    """Task-only preservation before Report arrival; not sufficient for Gate reset."""
    source, archive_dir = Path(source), Path(archive_dir)
    data = _read_source(source)
    identity = task_identity(data)
    digest = _digest(data, expected_sha256)
    return _publish(source, _target(archive_dir, identity, "task"), data, digest)


def archive_pair(
    task: Path,
    report: Path,
    archive_dir: Path,
    expected_task_sha256: Optional[str] = None,
    expected_report_sha256: Optional[str] = None,
) -> Tuple[ArchiveResult, ArchiveResult]:
    """Validate both inputs/conflicts first, then preserve both originals (17-J).

    Single-writer, quiescent windows and a hard-link-capable filesystem required.
    An I/O failure may leave one valid archive. Do not reset either window or
    commit a partial pair. Reconcile and retry; identical archives are accepted.
    No body rewriting, status changes, Git operations, or acceptance decision.
    """
    task, report, archive_dir = Path(task), Path(report), Path(archive_dir)
    task_data, report_data = _read_source(task), _read_source(report)
    identity = task_identity(task_data)
    if report_identity(report_data) != identity:
        raise ArchiveError("Task and Report task_id/revision must match before archiving")
    inputs = (
        (task, _target(archive_dir, identity, "task"), task_data,
         _digest(task_data, expected_task_sha256)),
        (report, _target(archive_dir, identity, "report"), report_data,
         _digest(report_data, expected_report_sha256)),
    )
    # Detect known conflicts before even creating the archive directory.
    for source, target, data, _ in inputs:
        if source.resolve() == target.resolve():
            raise ArchiveError("Source and archive destination must differ")
        _existing_matches(target, data)
    results = tuple(_publish(*item) for item in inputs)
    # Recheck BOTH source snapshots and archives before reporting pair success.
    for source, target, data, _ in inputs:
        if _read_source(source) != data or not _existing_matches(target, data):
            raise ArchiveError("Pair changed during archiving; keep both windows for recovery")
    return results[0], results[1]


def _result_dict(result: ArchiveResult) -> dict:
    return {"path": str(result.path), "sha256": result.sha256, "created": result.created}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, default=Path(".ai/task.md"))
    parser.add_argument("--archive-dir", type=Path, default=Path(".ai/archive"))
    parser.add_argument("--expected-sha256", help="SHA256 from an independent, trusted issuance record")
    parser.add_argument("--report", type=Path,
                        help="Also archive this Report with the Task; required for Gate cleanup")
    parser.add_argument("--expected-report-sha256",
                        help="SHA256 of the Report bytes from the verified Report commit")
    args = parser.parse_args(argv)
    if args.expected_report_sha256 is not None and args.report is None:
        parser.error("--expected-report-sha256 requires --report")
    try:
        if args.report is None:
            output = _result_dict(archive_task(args.task, args.archive_dir, args.expected_sha256))
        else:
            task, report = archive_pair(args.task, args.report, args.archive_dir,
                                        args.expected_sha256, args.expected_report_sha256)
            output = {"task": _result_dict(task), "report": _result_dict(report)}
    except (ArchiveError, OSError, ValueError) as exc:
        print("tai archive: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
