# GnmScale Game Profiles

*[Italiano](README.it.md)*

Per-game settings profiles for **GnmScale**, the PS4 homebrew app and GoldHEN
plugin for upscaling and frame generation. These are the profiles chosen by
the developer. The app downloads them from this repository, and you can pick
one from the app or from the in-game menu.

This repository holds only the profiles. GnmScale itself is distributed
separately.

## Using the profiles

1. Open GnmScale and select a game.
2. Go to the **Profiles** tab and choose **Download developer profiles**. This
   downloads every published profile for every game in one file and replaces
   the developer profiles you downloaded before.
3. Highlight a profile and press **X** to apply it. The app saves it as that
   game's settings, so it is active the next time you start the game.

In game, open the GnmScale menu (L3 + R3 by default). The **Profiles** tab
lists the same profiles; press → on one to apply it while you play.

Your own profiles (created in the app or with "Save as new profile" in game)
are stored separately and a download never touches them.

Profiles marked **To verify** have not been tested on a console by the author
yet. They are a starting point, not a guarantee. See [GAMES.md](GAMES.md) for
the full list.

## Layout

```
games/
  <game>/                one folder per game, named [a-z0-9_-]
    game.ini             the game's name and all its TITLE_IDs
    <profile>.ini        one file per profile
templates/               copy these to start a new game or profile
tools/build_bundle.py    validates everything and builds the bundle
dist/profiles.bundle     what the app downloads (generated, do not edit)
GAMES.md                 list of games and profiles (generated)
```

A profile applies to every TITLE_ID in its game's `game.ini`, so regional
editions share one set of files.

### game.ini

```ini
name=Bloodborne
title_ids=CUSA00900,CUSA00207,CUSA03173,CUSA03023
```

### Profile files

```ini
name=Performance
description=Frame generation 2x: from 30 to 60 fps on screen.
author=FrankBarretta
order=1
status=untested

sr=1
model=fsr1-rcas
fg_mult=2
fg_flow_scale=35
```

| Key | Meaning |
|---|---|
| `name` | Shown in the app and in game. Required, max 47 bytes. |
| `description` | One line, max 255 bytes. Shown under the profile. |
| `author` | Optional. |
| `order` | Position in the list (lower first). |
| `status` | `tested` once verified on a console, otherwise `untested`. |

Everything else is a setting, with the same keys and values as GnmScale's
`config.ini`. A profile sets only the keys it lists, and every other setting
of the game stays as it is.

| Setting | Values |
|---|---|
| `sr` | 1 upscaling on, 0 off |
| `model` | `fbsr3-pico-sharp-femto`, `fbsr3-pico-sharp-fast-femto`, `fbsr3-pico-fidelity-femto`, `fsr1-rcas`, `fbsr-v2` |
| `intensity` | 0.00 – 10.00 (1.00 = as trained; above that extrapolates) |
| `fps_cap` | 0 (game decides), 20, 30, 60 |
| `overlay` | status badge, 0/1 |
| `mem_auto`, `mem_garlic_mb` | memory budget: 1 = computed by the app; 0 + MiB to set it by hand |
| `out_mode` | 0 copy into the game's buffer, 1 flip GnmScale's buffer |
| `fence` | 0/1 |
| `menu_key` | `l3r3`, `l1r1`, `l2r2`, `touchpad`, `off` |
| `fsr_denoise` | FSR only, 0/1 |
| `fg_mult` | frame generation: 0 off, 2, 3 |
| `fg_flow_scale` | 35 – 100, steps of 5 |
| `fg_hud`, `fg_quadratic`, `fg_prior`, `fg_zero_motion`, `fg_edges`, `fg_refine` | 0/1 |
| `fg_in_place` | force frame generation in place, 0/1 |
| `fg_reserve_early` | experimental early reservation, 0/1 |
| `fg_hudfix`, `fg_hudfix_hudless`, `fg_hudfix_ext`, `fg_hudfix_source`, `fg_hudfix_compose` | 0/1 |
| `fg_hudfix_fill` | 4, 8, 16 |
| `fg_hudfix_sens`, `fg_hudfix_resp` | 0 – 2 |
| `fg_hudfix_cutoff` | 0 – 32 |
| `fg_hudfix_hole` | 0 – 8 |
| `fg_frame_border` | 0 – 256 px |
| `fbsr_scale` | 1.0 – 4.0 (FBSR-v2) |
| `fbsr_proc` | 1 – 4 |
| `fbsr_band` | 16, 32, 64, 128, 256 |
| `fbsr_detail`, `fbsr_sharpen`, `fbsr_denoise`, `fbsr_deartifact`, `fbsr_antialias`, `fbsr_ao`, `fbsr_gi`, `fbsr_reflections`, `fbsr_bloom` | 0.00 – 1.00 |
| `fbsr_shadows`, `fbsr_highlights`, `fbsr_clarity`, `fbsr_contrast`, `fbsr_saturation`, `fbsr_vibrance`, `fbsr_temperature`, `fbsr_tint`, `fbsr_gamma` | -1.00 – 1.00 |
| `fbsr_exposure` | -2.00 – 2.00 EV |

Diagnostic keys (`stage`, `fg_debug`, ...) and the interface language are not
allowed in a profile. The app ignores them and the validator rejects them.

## Adding or changing profiles

1. Copy `templates/` into `games/<game>/` (or edit an existing file).
2. Run `python tools/build_bundle.py`. It validates every file, then rebuilds
   `dist/profiles.bundle` and `GAMES.md`. Fix anything it reports.
3. Commit everything, including `dist/` and `GAMES.md`.

On every push to `main`, the GitHub Action runs the same script, and rebuilds
and commits the bundle if you forgot to. On a pull request it only validates.
The app always downloads
`https://raw.githubusercontent.com/FrankBarretta/GnmScale-Game-Profiles/main/dist/profiles.bundle`.

### Bundle format

Plain UTF-8 text, one profile after another:

```
@bundle 1
@generated 2026-10-07
@game bloodborne CUSA00900,CUSA00207,CUSA03173,CUSA03023
name=Bloodborne
@profile bloodborne performance
name=Performance
...
@end
```

Before replacing anything, the app checks the whole file: the header, the
TITLE_IDs, the file names and that each profile belongs to the game above it.
If the file is truncated or invalid, the profiles already on the console stay
as they are.
