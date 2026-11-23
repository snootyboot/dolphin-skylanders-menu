Skylanders Roguelike - dev tools build
======================================

This is a separate Dolphin install. Because of portable.txt, every setting, save and
Skylander file lives in the User folder next to Dolphin.exe. Your normal Dolphin, your
quick menu build and your Spyro's Adventure save are never touched.

Setup (once)
1. Extract this zip to its own folder (not inside your normal Dolphin folder).
2. Run Dolphin.exe and add your games folder under Config > Paths.
3. Controller: copy WiimoteNew.ini from %AppData%\Dolphin Emulator\Config\ into
   User\Config\ here. Don't copy Hotkeys.ini - it would unbind the dev tools keys.
4. Start Spyro's Adventure and begin a NEW game. This install has its own save, so every
   collectible is still in the levels.

Dev tools panel (top-left of the game screen)
  End (or Numpad 0)  capture the current step
  Page Down          skip the current step
  Delete             undo the last capture or skip
  Home               show or hide the panel
  Insert             record the watch list to a CSV file
  Page Up            reload session.txt and watch.txt

Follow the steps in the panel and press End after each one. When the panel says the
session is complete, close Dolphin. Captures are saved in
User\Roguelike\DevTools\Captures\ - tell Claude when you're done.

Rebind the keys under Options > Hotkey Settings > USB Emulation.
