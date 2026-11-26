#!/usr/bin/env python3
"""Build dist/profiles.bundle and GAMES.md from the folders under games/.

    games/
      Bloodborne [CUSA00900 CUSA00207]/     one folder per game: name + TITLE_IDs
        PS4 Slim - Ultra Quality.ini        one file per profile: the file name is
        PS4 Slim - Frame Gen.ini            the name shown on the console

A profile file is a GnmScale config.ini (key=value). Copy it as it is: keys the
app does not take in a profile (language, diagnostics, ...) are ignored by the
app. Optional lines: name=, description=, author=, order=, status=tested.

    python tools/build_bundle.py            rebuild dist/ and GAMES.md
    python tools/build_bundle.py --check    exit 1 if dist/ or GAMES.md is stale

You do not have to run it: on every push to main the GitHub Action does.
Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"
DIST = ROOT / "dist" / "profiles.bundle"
GAMES_MD = ROOT / "GAMES.md"

# Limits of the app (common/config/be_profile.h / be_profile.c).
TITLE_ID = re.compile(r"\b([A-Za-z]{4}[0-9]{5})\b")
SLUG_MAX = 39
MAX_IDS = 16
NAME_MAX = 47
DESC_MAX = 255
PROFILE_MAX = 8000


def slugify(text: str) -> str:
    """'PS4 Slim - Frame Gen' -> 'ps4-slim-frame-gen' (the app wants [a-z0-9_-])."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:SLUG_MAX].strip("-")


def load_profile(path: Path, problems: list[str]):
    where = path.relative_to(ROOT).as_posix()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        problems.append(f"{where}: not UTF-8")
        return None
    meta = {"name": path.stem, "order": 1000, "status": "untested"}
    lines, seen = [], set()
    for raw in text.splitlines():
        line = raw.strip()
        # Comments, [sections] and '@' (a bundle directive) are not settings.
        if not line or line[0] in "#;[@" or "=" not in line:
            continue
        k, v = (s.strip() for s in line.split("=", 1))
        if not k or k in seen:
            continue
        seen.add(k)
        if k == "name" and v:
            meta["name"] = v
        elif k == "order":
            try:
                meta["order"] = int(v)
            except ValueError:
                problems.append(f"{where}: order must be a whole number")
        elif k == "status":
            meta["status"] = v
        elif k == "description" and len(v.encode()) > DESC_MAX:
            problems.append(f"{where}: description longer than {DESC_MAX} bytes")
        if k != "name":
            lines.append(f"{k}={v}")
    lines.insert(0, f"name={meta['name']}")
    if len(meta["name"].encode()) > NAME_MAX:
        problems.append(f"{where}: name longer than {NAME_MAX} bytes")
    if len(lines) <= 1:
        problems.append(f"{where}: no settings")
    if sum(len(x) + 1 for x in lines) > PROFILE_MAX:
        problems.append(f"{where}: profile too large")
    slug = slugify(path.stem)
    if not slug:
        problems.append(f"{where}: the file name needs at least one letter or digit")
        return None
    return {"slug": slug, "lines": lines, **meta}


def load_game(gdir: Path, problems: list[str]):
    where = gdir.relative_to(ROOT).as_posix()
    ids = [m.upper() for m in TITLE_ID.findall(gdir.name)]
    name = re.sub(r"\s+", " ", TITLE_ID.sub("", gdir.name))
    name = re.sub(r"[\[\](),]", " ", name).strip(" -_")
    name = re.sub(r"\s+", " ", name)
    if not ids:
        problems.append(f"{where}: put the TITLE_IDs in the folder name, "
                        f"e.g. 'Bloodborne [CUSA00900 CUSA00207]'")
        return None
    if len(ids) > MAX_IDS:
        problems.append(f"{where}: at most {MAX_IDS} TITLE_IDs")
    if len(set(ids)) != len(ids):
        problems.append(f"{where}: a TITLE_ID appears twice")
    game = {"slug": slugify(name) or ids[0].lower(), "name": name or ids[0],
            "ids": ids, "profiles": [], "where": where}
    for pfile in sorted(gdir.glob("*.ini")):
        prof = load_profile(pfile, problems)
        if prof:
            game["profiles"].append(prof)
    if not game["profiles"]:
        problems.append(f"{where}: no .ini profiles in the folder")
    slugs = [p["slug"] for p in game["profiles"]]
    for s in sorted({s for s in slugs if slugs.count(s) > 1}):
        problems.append(f"{where}: two profile file names give the same id '{s}'")
    game["profiles"].sort(key=lambda p: (p["order"], p["name"]))
    return game


def bundle_body(games) -> str:
    out = []
    for g in games:
        out.append(f"@game {g['slug']} {','.join(g['ids'])}")
        out.append(f"name={g['name']}")
        for p in g["profiles"]:
            out.append(f"@profile {g['slug']} {p['slug']}")
            out.extend(p["lines"])
    out.append("@end")
    return "\n".join(out) + "\n"


def bundle_text(body: str, date: str) -> str:
    return (
        "# GnmScale game profiles - generated by tools/build_bundle.py, do not edit.\n"
        "# Source: https://github.com/FrankBarretta/GnmScale-Game-Profiles\n"
        f"@bundle 1\n@generated {date}\n" + body
    )


def strip_generated(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.startswith("@generated")) + "\n"


def games_md(games) -> str:
    rows = [
        "# Games",
        "",
        "Generated by `tools/build_bundle.py`. *Verified* means the author tested the "
        "profile on a console.",
        "",
        "| Game | TITLE_IDs | Profiles |",
        "|---|---|---|",
    ]
    for g in games:
        profs = ", ".join(
            p["name"] + (" (verified)" if p["status"] == "tested" else "") for p in g["profiles"]
        )
        rows.append(f"| {g['name']} | {', '.join(g['ids'])} | {profs} |")
    return "\n".join(rows) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if dist/ or GAMES.md is stale")
    args = ap.parse_args()

    problems: list[str] = []
    games = []
    dirs = sorted((p for p in GAMES.iterdir() if p.is_dir()), key=lambda p: p.name.lower()) \
        if GAMES.exists() else []
    for gdir in dirs:
        g = load_game(gdir, problems)
        if g:
            games.append(g)
    owners: dict[str, str] = {}
    for g in games:
        if g["slug"] in owners.values():
            problems.append(f"{g['where']}: another game folder has the same name")
        for tid in g["ids"]:
            if tid in owners:
                problems.append(f"{g['where']}: {tid} is also in games/{owners[tid]}")
            owners[tid] = g["slug"]
    if not games:
        problems.append("games/: no games")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(f"\n{len(problems)} problem(s)", file=sys.stderr)
        return 1

    body = bundle_body(games)
    old = DIST.read_text(encoding="utf-8") if DIST.exists() else ""
    stale = strip_generated(old) != strip_generated(bundle_text(body, ""))
    md = games_md(games)
    md_stale = (GAMES_MD.read_text(encoding="utf-8") if GAMES_MD.exists() else "") != md
    nprof = sum(len(g["profiles"]) for g in games)

    if args.check:
        if stale or md_stale:
            print("dist/profiles.bundle or GAMES.md is out of date: "
                  "run python tools/build_bundle.py", file=sys.stderr)
            return 1
        print(f"ok: {len(games)} games, {nprof} profiles, bundle up to date")
        return 0

    if stale:
        DIST.parent.mkdir(parents=True, exist_ok=True)
        today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        DIST.write_text(bundle_text(body, today), encoding="utf-8", newline="\n")
    if md_stale:
        GAMES_MD.write_text(md, encoding="utf-8", newline="\n")
    print(f"{len(games)} games, {nprof} profiles -> "
          f"{'dist/profiles.bundle rebuilt' if stale else 'bundle unchanged'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
