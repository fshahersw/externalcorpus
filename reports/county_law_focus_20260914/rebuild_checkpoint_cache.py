"""Conservative, content-verified no-change gate for the coordinated publisher.

This is a whole-checkpoint cache, not a per-step cache. It never establishes a
baseline from a pre-existing publication. The coordinator calls ``remember``
only after all seven steps pass while collector locks are held. Unknown or
changing inputs, a damaged baseline, and all source/output changes miss safely.

The registry intentionally includes entire source trees (even unrelated saved
material), all builder/helper code trees, SQLite WAL files, and published bytes.
It is broader than the seven builders need. Metadata can reject a cache hit;
it can NEVER accept one. Every accepted hit freshly hashes every registered
file. Keep this registry current when adding a builder input outside its roots.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import sys
import time

VERSION = 1
INPUT_TREES = (
    "sources", "corpus", "scripts", "pipeline", "reports/laws", "reports/geography",
)
OUTPUT_TREES = (
    "catalog", "delivery/focused_legal_corpus", "reports/counties/local_documents_20260914",
)
INPUT_FILES = (
    "REQUEST.md", "RUNBOOK.md", "reports/law_source_constraints.json",
    "reports/county_law_focus_20260914/scope.json",
    "reports/county_law_focus_20260914/DATA_QUALITY.md",
    "reports/county_law_focus_20260914/rebuild_focused_package.py",
    "reports/county_law_focus_20260914/rebuild_checkpoint_cache.py",
    "delivery/ui-sketch/build_data.py",
)
OUTPUT_FILES = (
    "README.md", "reports/remaining_resume_20260913/scope.json", "delivery/ui-sketch/data.js",
)
IGNORED_NAMES = {"__pycache__", ".crawler.lock"}
DEFAULT_BASELINE = "reports/county_law_focus_20260914/rebuild_cache/last_validated.json"


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value):
    return hashlib.sha256(packed(value)).hexdigest()


def _ignored(path):
    # SQLite SHM is coordination state. WAL contains actual committed data and
    # MUST be included; do not extend this exclusion to WAL/journal files.
    return path.name in IGNORED_NAMES or path.name.endswith(".sqlite3-shm")


def _stat(path):
    value = path.stat()
    return _stat_value(value)


def _stat_value(value):
    # Windows DirEntry.stat does not supply the same inode value as Path.stat.
    # These fields gate races/reject cache candidates; acceptance also requires
    # a fresh content digest, so inode is neither needed nor trusted here.
    return [value.st_size, value.st_mtime_ns, value.st_ctime_ns]


def hash_file(path, expected=None):
    before = _stat(path)
    if expected is not None and before != expected:
        raise RuntimeError("A registered file changed before hashing")
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            sha.update(block)
    if _stat(path) != before:
        raise RuntimeError("A registered file changed while hashing")
    return sha.hexdigest()


class CheckpointCache:
    def __init__(self, root, *, input_trees=INPUT_TREES, output_trees=OUTPUT_TREES,
                 input_files=INPUT_FILES, output_files=OUTPUT_FILES, baseline=DEFAULT_BASELINE):
        self.root = Path(root).resolve()
        self.input_trees = tuple(input_trees)
        self.output_trees = tuple(output_trees)
        self.input_files = tuple(input_files)
        self.output_files = tuple(output_files)
        self.baseline = self.root / baseline
        self.baseline.resolve().relative_to(self.root)
        self.registry = {
            "version": VERSION, "input_trees": self.input_trees, "output_trees": self.output_trees,
            "input_files": self.input_files, "output_files": self.output_files,
            "ignored_names": sorted(IGNORED_NAMES), "ignore_sqlite_shared_memory": True,
        }

    def _path(self, name):
        path = self.root / name
        path.resolve().relative_to(self.root)
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise RuntimeError("Links/junctions require explicit input review")
        return path

    def inventory(self, inputs_only=False):
        """Enumerate names too: additions/deletions cannot hide behind old hashes."""
        rows = {}
        trees = self.input_trees if inputs_only else self.input_trees + self.output_trees
        files = self.input_files if inputs_only else self.input_files + self.output_files

        def add(path):
            relative = path.relative_to(self.root).as_posix()
            self._path(relative)
            if path.is_file():
                rows[relative] = {"kind": "file", "stat": _stat(path)}
            elif path.is_dir():
                rows[relative] = {"kind": "directory"}
            elif not path.exists():
                rows[relative] = {"kind": "missing"}
            else:
                raise RuntimeError("Unsupported registered input type")

        for name in trees:
            base = self._path(name)
            add(base)
            if not base.is_dir():
                continue
            pending = [base]
            while pending:
                current = pending.pop()
                # DirEntry.stat uses the information supplied by Windows'
                # directory enumeration. Avoid resolving 100,000 full paths
                # repeatedly; each parent is checked before it is traversed.
                with os.scandir(current) as scanned:
                    entries = sorted(scanned, key=lambda entry: entry.name)
                for entry in entries:
                    path = Path(entry.path)
                    if _ignored(path):
                        continue
                    info = entry.stat(follow_symlinks=False)
                    if entry.is_symlink() or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        raise RuntimeError('Links/junctions require explicit input review')
                    relative = path.relative_to(self.root).as_posix()
                    if stat.S_ISDIR(info.st_mode):
                        rows[relative] = {'kind': 'directory'}
                        pending.append(path)
                    elif stat.S_ISREG(info.st_mode):
                        rows[relative] = {'kind': 'file', 'stat': _stat_value(info)}
                    else:
                        raise RuntimeError('Unsupported registered input type')
        for name in files:
            add(self._path(name))
        return dict(sorted(rows.items()))

    def runtime(self):
        # Include actual imported helper bytes, not just top-level builder names.
        # Registered source trees cover helpers not imported until a build step.
        local_modules, runtime_modules = {}, {}
        for module in list(sys.modules.values()):
            value = getattr(module, "__file__", None)
            if not value:
                continue
            path = Path(value)
            if path.suffix == ".pyc" and path.parent.name == "__pycache__":
                source = path.parent.parent / (path.name.split(".")[0] + ".py")
                if source.exists():
                    path = source
            if path.is_file():
                try:
                    relative = path.resolve().relative_to(self.root).as_posix()
                    local_modules[relative] = hash_file(path)
                except ValueError:
                    runtime_modules[str(path.resolve())] = hash_file(path)
        return {"python": sys.version, "platform": platform.platform(),
                "executable": str(Path(sys.executable).resolve()),
                "executable_sha256": hash_file(Path(sys.executable)),
                "local_imported_helpers": dict(sorted(local_modules.items())),
                "runtime_imported_helpers": dict(sorted(runtime_modules.items()))}

    def fingerprint(self, inventory=None):
        started = time.perf_counter()
        inventory = inventory if inventory is not None else self.inventory()
        files = [(name, row) for name, row in inventory.items() if row["kind"] == "file"]

        def one(item):
            name, row = item
            return name, {"bytes": row["stat"][0], "sha256": hash_file(self.root / name, row["stat"])}

        # A small pool amortizes Windows open latency without saturating disk.
        with ThreadPoolExecutor(max_workers=4) as workers:
            hashes = dict(workers.map(one, files))
        if self.inventory() != inventory:
            raise RuntimeError("Registered namespace changed during fingerprint")
        material = {"registry": self.registry, "files": hashes,
                    "nonfiles": {name: row for name, row in inventory.items() if row["kind"] != "file"}}
        return {"sha256": digest(material), "files": hashes, "inventory": inventory,
                "registry_sha256": digest(self.registry), "file_count": len(files),
                "bytes_hashed": sum(row["stat"][0] for _, row in files),
                "elapsed_seconds": round(time.perf_counter() - started, 6)}

    def check(self):
        started = time.perf_counter()
        try:
            if not self.baseline.is_file():
                return {"hit": False, "reason": "no_validated_baseline"}
            baseline = json.loads(self.baseline.read_text(encoding="utf-8"))
            if baseline.get("schema_version") != VERSION or baseline.get("validated") is not True:
                return {"hit": False, "reason": "untrusted_or_unsupported_baseline"}
            receipt = self._path(baseline["receipt"])
            if hash_file(receipt) != baseline["receipt_sha256"]:
                return {"hit": False, "reason": "validation_receipt_changed"}
            proof = json.loads(receipt.read_text(encoding="utf-8"))
            if proof.get("validated") is not True or len(proof.get("steps", [])) != 7 or any(step.get("exit_code") != 0 for step in proof["steps"]):
                return {"hit": False, "reason": "validation_receipt_not_a_passing_full_build"}
            if digest(self.registry) != baseline["fingerprint"]["registry_sha256"]:
                return {"hit": False, "reason": "input_registry_changed"}
            inventory = self.inventory()
            # Fast reject only. Same size/time is never sufficient for a hit.
            if inventory != baseline["fingerprint"]["inventory"]:
                return {"hit": False, "reason": "registered_input_or_output_metadata_changed"}
            fresh = self.fingerprint(inventory)
            if fresh["sha256"] != baseline["fingerprint"]["sha256"]:
                return {"hit": False, "reason": "registered_input_or_output_bytes_changed"}
            # Dynamic import population differs before/after a full run. Compare
            # all previously imported helpers directly, including any outside
            # the broad code roots, instead of requiring identical sys.modules.
            runtime = baseline["runtime"]
            current_runtime = self.runtime()
            for key in ("python", "platform", "executable", "executable_sha256"):
                if runtime[key] != current_runtime[key]:
                    return {"hit": False, "reason": "runtime_changed"}
            for name, expected in runtime["local_imported_helpers"].items():
                if hash_file(self._path(name)) != expected:
                    return {"hit": False, "reason": "imported_helper_changed"}
            for name, expected in runtime["runtime_imported_helpers"].items():
                if hash_file(Path(name)) != expected:
                    return {"hit": False, "reason": "runtime_helper_changed"}
            return {"hit": True, "reason": "all_registered_bytes_match_validated_checkpoint",
                    "baseline_receipt": baseline["receipt"], "fingerprint_sha256": fresh["sha256"],
                    "files_freshly_hashed": fresh["file_count"], "bytes_freshly_hashed": fresh["bytes_hashed"],
                    "elapsed_seconds": round(time.perf_counter() - started, 6)}
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            return {"hit": False, "reason": "cache_unavailable_full_build_required", "error_type": type(error).__name__}

    def remember(self, receipt, inputs_before):
        """Only called after a passing full build; never bless an old package."""
        receipt = Path(receipt)
        proof = json.loads(receipt.read_text(encoding="utf-8"))
        if proof.get("validated") is not True or len(proof.get("steps", [])) != 7 or any(step.get("exit_code") != 0 for step in proof["steps"]):
            raise ValueError("A passing seven-step receipt is required")
        if self.inventory(inputs_only=True) != inputs_before:
            raise RuntimeError("Source/code inputs changed during publication; cache baseline not written")
        fingerprint = self.fingerprint()
        if self.inventory(inputs_only=True) != inputs_before:
            raise RuntimeError("Source/code inputs changed while establishing baseline")
        value = {"schema_version": VERSION, "validated": True,
                 "receipt": receipt.resolve().relative_to(self.root).as_posix(),
                 "receipt_sha256": hash_file(receipt), "runtime": self.runtime(), "fingerprint": fingerprint}
        self.baseline.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.baseline.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
        temporary.replace(self.baseline)
        return {"written": True, "file_count": fingerprint["file_count"],
                "bytes_hashed": fingerprint["bytes_hashed"], "elapsed_seconds": fingerprint["elapsed_seconds"]}
