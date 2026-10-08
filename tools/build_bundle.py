#!/usr/bin/env python3
"""Validate every profile under games/ and build dist/profiles.bundle.

The GnmScale app downloads dist/profiles.bundle (one file, one request) and
installs it on the console. This script is the only thing that writes it.

    python tools/build_bundle.py            validate + rebuild dist/ and GAMES.md
    python tools/build_bundle.py --check    validate only; exit 1 if dist/ is stale

Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"
DIST = ROOT / "dist" / "profiles.bundle"
GAMES_MD = ROOT / "GAMES.md"

SLUG = re.compile(r"^[a-z0-9_-]{1,39}$")
TITLE_ID = re.compile(r"^[A-Z]{4}[0-9]{5}$")
MAX_IDS = 16
NAME_MAX = 47     # bytes, UTF-8 (BE_PROFILE_NAME_LEN - 1)
DESC_MAX = 255    # bytes, UTF-8 (BE_PROFILE_DESC_LEN - 1)
PROFILE_MAX = 8000

# --- what a profile may contain ----------------------------------------------
# Must match the key list in the app (common/be_profile.c, kKeys + fbsr_*).
# The app ignores keys it does not know; this script refuses them, so a typo
# never ships as a setting that silently does nothing.

MODELS = {
    "fbsr3-pico-sharp-femto",
    "fbsr3-pico-sharp-fast-femto",
    "fbsr3-pico-fidelity-femto",
    "fsr1-rcas",
    "fbsr-v2",
    "fbsr-v3",
}
MENU_KEYS = {"l3r3", "l1r1", "l2r2", "touchpad", "off"}

BOOL = ("bool",)


def ints(*allowed):
    return ("set", set(allowed))


def rng(lo, hi, step=1):
    return ("range", lo, hi, step)


def frng(lo, hi):
    return ("float", lo, hi)


SETTINGS = {
    "model": ("enum", MODELS),
    "sr": BOOL,
    "intensity": frng(0.0, 10.0),
    "fps_cap": ints(0, 20, 30, 60),
    "overlay": BOOL,
    "mem_auto": BOOL,
    "mem_garlic_mb": rng(2, 1024),
    "out_mode": BOOL,
    "fence": BOOL,
    "menu_key": ("enum", MENU_KEYS),
    "fsr_denoise": BOOL,
    "fg_mult": ints(0, 2, 3),
    "fg_flow_scale": rng(35, 100, 5),
    "fg_hud": BOOL,
    "fg_quadratic": BOOL,
    "fg_prior": BOOL,
    "fg_zero_motion": BOOL,
    "fg_edges": BOOL,
    "fg_refine": BOOL,
    "fg_reserve_early": BOOL,
    "fg_in_place": BOOL,
    "fg_hudfix": BOOL,
    "fg_hudfix_hudless": BOOL,
    "fg_hudfix_fill": ints(4, 8, 16),
    "fg_hudfix_sens": rng(0, 2),
    "fg_hudfix_resp": rng(0, 2),
    "fg_hudfix_ext": BOOL,
    "fg_hudfix_source": BOOL,
    "fg_hudfix_compose": BOOL,
    "fg_hudfix_cutoff": rng(0, 32),
    "fg_hudfix_hole": rng(0, 8),
    "fg_frame_border": rng(0, 256),
    "fbsr_scale": frng(1.0, 4.0),
    "fbsr_proc": rng(1, 4),
    "fbsr_band": ints(16, 32, 64, 128, 256),
}
# FBSR-v2 controls: fbsr_<name>, same names and ranges as the app.
for _k in ("detail", "sharpen", "denoise", "deartifact", "antialias", "ao", "gi",
           "reflections", "bloom"):
    SETTINGS["fbsr_" + _k] = frng(0.0, 1.0)
for _k in ("shadows", "highlights", "clarity", "contrast", "saturation", "vibrance",
           "temperature", "tint", "gamma"):
    SETTINGS["fbsr_" + _k] = frng(-1.0, 1.0)
SETTINGS["fbsr_exposure"] = frng(-2.0, 2.0)

META = {"name", "description", "author", "order", "status"}
STATUS = {"tested", "untested"}


class Problems:
    def __init__(self):
        self.items: list[str] = []

    def add(self, path: Path, line: int | None, msg: str):
        where = path.relative_to(ROOT).as_posix() + (f":{line}" if line else "")
        self.items.append(f"{where}: {msg}")


def check_value(key: str, val: str) -> str | None:
    spec = SETTINGS[key]
    kind = spec[0]
    try:
        if kind == "bool":
            return None if val in ("0", "1") else "must be 0 or 1"
        if kind == "enum":
            return None if val in spec[1] else f"must be one of {sorted(spec[1])}"
        if kind == "set":
            return None if int(val) in spec[1] else f"must be one of {sorted(spec[1])}"
        if kind == "range":
            v = int(val)
            lo, hi, step = spec[1], spec[2], spec[3]
            if not lo <= v <= hi or (v - lo) % step:
                return f"must be {lo}..{hi}" + (f" in steps of {step}" if step > 1 else "")
            return None
        if kind == "float":
            v = float(val)
            return None if spec[1] <= v <= spec[2] else f"must be {spec[1]}..{spec[2]}"
    except ValueError:
        return "not a number"
    return "unknown type"


def parse_ini(path: Path, probs: Problems):
    """key=value lines, '#' and ';' comments. Returns [(line, key, value)]."""
    out = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        probs.add(path, None, "not UTF-8")
        return out
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("@"):
            probs.add(path, n, "lines may not start with '@' (bundle directive)")
            continue
        if "=" not in line:
            probs.add(path, n, "expected key=value")
            continue
        k, v = line.split("=", 1)
        out.append((n, k.strip(), v.strip()))
    return out


def load_game(gdir: Path, probs: Problems):
    if not SLUG.match(gdir.name):
        probs.add(gdir, None, "folder name must be [a-z0-9_-], max 39 characters")
        return None
    gini = gdir / "game.ini"
    if not gini.exists():
        probs.add(gdir, None, "missing game.ini")
        return None
    game = {"slug": gdir.name, "name": "", "ids": [], "profiles": []}
    for n, k, v in parse_ini(gini, probs):
        if k == "name":
            game["name"] = v
        elif k == "title_ids":
            ids = [x.strip() for x in v.split(",") if x.strip()]
            bad = [x for x in ids if not TITLE_ID.match(x)]
            if bad:
                probs.add(gini, n, f"bad TITLE_ID {bad} (four capitals + five digits)")
            game["ids"] = ids
        else:
            probs.add(gini, n, f"unknown key '{k}' (game.ini has name and title_ids)")
    if not game["name"]:
        probs.add(gini, None, "missing name")
    if not game["ids"]:
        probs.add(gini, None, "missing title_ids")
    if len(game["ids"]) > MAX_IDS:
        probs.add(gini, None, f"at most {MAX_IDS} title_ids")
    if len(set(game["ids"])) != len(game["ids"]):
        probs.add(gini, None, "duplicate title_ids")

    for pfile in sorted(gdir.glob("*.ini")):
        if pfile.name == "game.ini":
            continue
        prof = load_profile(pfile, probs)
        if prof:
            game["profiles"].append(prof)
    if not game["profiles"]:
        probs.add(gdir, None, "no profiles")
    game["profiles"].sort(key=lambda p: (p["order"], p["name"]))
    return game


def load_profile(pfile: Path, probs: Problems):
    slug = pfile.stem
    if not SLUG.match(slug):
        probs.add(pfile, None, "file name must be [a-z0-9_-].ini, max 39 characters")
        return None
    prof = {"slug": slug, "name": "", "order": 1000, "status": "untested", "lines": []}
    seen = set()
    nsettings = 0
    for n, k, v in parse_ini(pfile, probs):
        if k in seen:
            probs.add(pfile, n, f"'{k}' appears twice")
        seen.add(k)
        if k in META:
            if k == "name":
                prof["name"] = v
                if len(v.encode()) > NAME_MAX:
                    probs.add(pfile, n, f"name longer than {NAME_MAX} bytes")
            elif k == "description" and len(v.encode()) > DESC_MAX:
                probs.add(pfile, n, f"description longer than {DESC_MAX} bytes")
            elif k == "order":
                try:
                    prof["order"] = int(v)
                except ValueError:
                    probs.add(pfile, n, "order must be an integer")
            elif k == "status":
                if v not in STATUS:
                    probs.add(pfile, n, f"status must be one of {sorted(STATUS)}")
                prof["status"] = v
        elif k in SETTINGS:
            err = check_value(k, v)
            if err:
                probs.add(pfile, n, f"{k}={v}: {err}")
            nsettings += 1
        else:
            probs.add(pfile, n, f"unknown key '{k}'")
        prof["lines"].append(f"{k}={v}")
    if not prof["name"]:
        probs.add(pfile, None, "missing name")
    if nsettings == 0:
        probs.add(pfile, None, "no settings")
    if sum(len(x) + 1 for x in prof["lines"]) > PROFILE_MAX:
        probs.add(pfile, None, "profile too large")
    return prof


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


def strip_generated(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.startswith("@generated")) + "\n"


def bundle_text(body: str, date: str) -> str:
    return (
        "# GnmScale game profiles - generated by tools/build_bundle.py, do not edit.\n"
        "# Source: https://github.com/FrankBarretta/GnmScale-Game-Profiles\n"
        f"@bundle 1\n@generated {date}\n" + body
    )


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
    ap.add_argument("--check", action="store_true", help="validate only; fail if dist/ is stale")
    args = ap.parse_args()

    probs = Problems()
    games = []
    for gdir in sorted(p for p in GAMES.iterdir() if p.is_dir()) if GAMES.exists() else []:
        g = load_game(gdir, probs)
        if g:
            games.append(g)
    owners: dict[str, str] = {}
    for g in games:
        for tid in g["ids"]:
            if tid in owners:
                probs.add(GAMES / g["slug"], None, f"{tid} already belongs to {owners[tid]}")
            owners[tid] = g["slug"]
    if not games:
        probs.add(GAMES, None, "no games")

    if probs.items:
        print("\n".join(probs.items), file=sys.stderr)
        print(f"\n{len(probs.items)} problem(s)", file=sys.stderr)
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
