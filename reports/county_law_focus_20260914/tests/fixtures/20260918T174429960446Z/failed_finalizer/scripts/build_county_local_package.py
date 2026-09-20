from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
    with (ROOT/"fixture_county_build_calls.txt").open("a",encoding="utf-8") as recorded:
        recorded.write("build called\n")
