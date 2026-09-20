from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def finalize(scope,persist_scope=True):
    scope["fixture_value"]="new build value"
    if persist_scope:
        (ROOT/"reports/remaining_resume_20260913/scope.json").write_text("build-owned partial scope")
    raise RuntimeError("fixture finalizer failed")
