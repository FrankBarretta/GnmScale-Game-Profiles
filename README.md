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

## Adding a profile

1. In `games/`, make a folder for the game, named with the game's title and
   its TITLE_IDs (every edition that should get the same profiles):

   ```
   games/Bloodborne [CUSA00900 CUSA00207 CUSA03173 CUSA03023]/
   ```

2. Put the profile in it as an `.ini` file. The file name is the name shown
   on the console:

   ```
   games/Bloodborne [CUSA00900 CUSA00207 CUSA03173 CUSA03023]/PS4 Slim - Frame Gen.ini
   ```

   The content is a GnmScale `config.ini` (`key=value`), so you can copy the
   game's config from the console as it is. Keys a profile does not carry
   (language, diagnostics) are ignored by the app.

3. Commit and push to `main`. The GitHub Action builds
   `dist/profiles.bundle` and `GAMES.md`, and the app downloads the new
   profile the next time you choose **Download developer profiles**.

That is all. A profile sets only the keys it lists, and every other setting of
the game stays as it is.

### Optional lines

You can add these to a profile file:

```ini
description=Frame generation 2x: from 30 to 60 fps on screen.
author=FrankBarretta
order=1
status=tested
```

| Key | Meaning |
|---|---|
| `name` | Overrides the file name as the shown name (max 47 bytes). |
| `description` | One line, max 255 bytes. Shown under the profile. |
| `author` | Who made it. |
| `order` | Position in the list (lower first; otherwise by name). |
| `status` | `tested` once verified on a console. |

### Checking locally

`python tools/build_bundle.py` does what the Action does: it reports any
problem (no TITLE_ID in the folder name, the same TITLE_ID in two games, a
name too long) and rebuilds `dist/profiles.bundle` and `GAMES.md`. You do not
have to run it. On a pull request the Action only checks.

The app always downloads
`https://raw.githubusercontent.com/FrankBarretta/GnmScale-Game-Profiles/main/dist/profiles.bundle`
(do not edit it by hand).

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
