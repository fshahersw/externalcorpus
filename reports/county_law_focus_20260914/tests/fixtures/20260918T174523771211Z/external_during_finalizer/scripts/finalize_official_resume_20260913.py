from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def finalize(scope,persist_scope=True):
    target=ROOT/"reports/remaining_resume_20260913/scope.json"
    target.write_bytes(b"external user scope during finalizer")
    if persist_scope:
        target.write_bytes(b"incorrect overwritten build scope")
