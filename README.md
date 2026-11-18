# Dolphin 2609b + Skylanders Quick Menu

Personal build of [Dolphin](https://github.com/dolphin-emu/dolphin) 2609b with an in-game,
controller-driven menu for swapping Skylanders on the emulated Portal of Power.

- `skylanders-quick-menu.patch` — the source changes (applied on top of tag `2609b`).
- `.github/workflows/build.yml` — builds Windows x64 on every push to `main` and publishes a
  Release with `Dolphin-2609b-SkylandersMenu.zip`.

## Controls (DualSense, player 1 / `SDL/0`)

| Button | Action |
|---|---|
| PS | Open / close the menu |
| D-pad or left stick ↑↓ | Browse figures (hold to scroll) |
| D-pad or left stick ←→ | Choose Slot 1 / Slot 2 |
| Cross | Place the highlighted figure on the chosen slot (or remove, on the top row) |
| Circle | Close |

The game keeps running behind the menu, but it ignores controller input until the menu closes.
Picking a figure that's already in the other slot moves it over.
The list shows every Spyro's Adventure figure (characters, sidekicks, magic items, adventure packs)
plus any other files in your Skylanders collection folder (`%AppData%\Dolphin Emulator\Skylanders`).
Figures marked **NEW** have no file yet; one is created in that folder the first time you place it.

The buttons are rebindable under **Options → Hotkey Settings → USB Emulation Devices**.
Requires **Tools → Emulated Skylanders Portal → Emulate Skylander Portal** to be on.

Dolphin is licensed under GPLv2+; this patch is too.
