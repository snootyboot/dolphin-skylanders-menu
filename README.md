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
| D-pad or left stick | Move around the grid (hold to scroll) |
| L1 / R1 | Change slot: Slot 1, Slot 2, Slot 3 (Items) |
| Cross | Place the highlighted figure on the selected slot |
| Triangle | Remove the figure from the selected slot |
| Circle | Close |

Slots 1 and 2 list characters and sidekicks: a **Recent** row first (the newest figure of each
element plus the newest sidekick, 9 at most), then one group per element, then sidekicks.
Slot 3 lists magic items and adventure packs (and traps, if you have Trap Team files).

Every Spyro's Adventure figure is listed. Figures marked **NEW** have no file yet; one is created
in your Skylanders folder (`%AppData%\Dolphin Emulator\Skylanders`) the first time you place it.
Placing a figure that's already in another slot moves it over.

**Portraits:** put `Portraits\<Name>.png` (transparent background) in the Skylanders folder and
it's drawn over the figure's element colour. Figures without one show their initials.
Recently used figures are remembered in `QuickMenuRecent.txt` in the same folder.

The game keeps running behind the menu but ignores controller input until it closes.

The buttons are rebindable under **Options → Hotkey Settings → USB Emulation Devices**.
Requires **Tools → Emulated Skylanders Portal → Emulate Skylander Portal** to be on.

Dolphin is licensed under GPLv2+; this patch is too.
