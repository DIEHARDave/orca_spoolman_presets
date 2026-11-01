# Orca Spoolman Presets

An OrcaSlicer plugin for Moonraker printers that track their spools in [Spoolman](https://github.com/Donkie/Spoolman).

- **Sync slots:** for each lane the printer reports, it selects *your* filament preset for that slot. It uses the spool loaded in the lane, not just its material, so a spool of Sunlu HS PLA+ 2.0 gets your tuned "Sunlu HS PLA+ 2.0" preset instead of Generic PLA.
- **Create missing presets:** for Spoolman filaments OrcaSlicer has no preset for, it creates presets you can tune. Each one is named after the vendor and product line, for example "Jayo PLA", inherits the closest built-in preset, and takes its temperatures and density from Spoolman.

## Requirements

- An OrcaSlicer build with Python plugins (2.5 alpha or later).
- A printer whose Moonraker publishes `lane_data` with a `spool_id` per lane, for example through AFC, zmod_afclite, FF_NFC, Happy Hare or HelixScreen.
- Moonraker with a `[spoolman]` section. The plugin reaches Spoolman only through Moonraker's `/server/spoolman/proxy`.

## Install

1. Download `orca_spoolman_presets.py`.
2. In OrcaSlicer, open **Plugins**, choose **Install local plugin** and pick the file.
3. Run **Orca Spoolman Presets** from the Plugins dialog.
4. Enter the printer's Moonraker URL, for example `http://10.0.1.107:7125`, and click **Save**.

OrcaSlicer asks once for permission to reach that host, and once to write the preset bundle.

## Sync slots

1. Run OrcaSlicer's own filament sync first. It sets the number of slots. The printer must be connected: if the sync button does nothing, check that the printer's host includes Moonraker's port, for example `10.0.1.107:7125`.
2. Click **Sync slots from printer**. Lane 0 goes to slot 1, lane 1 to slot 2, and so on.
3. Selecting a preset gives the slot that preset's default color. Run OrcaSlicer's sync again with **Preferences → Filament sync mode** set to **Color only** to get the spools' colors back. OrcaSlicer builds whose plugin API has `set_slot_color` don't need this step: the plugin sets each slot to its lane's color itself.

The preset for each spool is the first one that applies:

1. The `orca_preset` extra field on the spool, then on its filament. It names a preset exactly; the " @Printer" suffix is optional. To use it, add a text extra field with the key `orca_preset` under Spoolman's Settings → Extra fields.
2. The preset whose name, without any " @Printer" suffix, is the longest whole-word prefix of
   - `<vendor> <filament name>`, for example "Sunlu HS PLA+ 2.0 Olive Green", or
   - `<vendor> <material> <filament name>`, for example "Epelay PLA+ Green".

   If neither matches, the filament name alone is tried against your own presets and the ones this plugin created, so a preset named "Soleyin Ultra PLA" without its vendor still matches "Soleyin Ultra PLA Ocean Blue".

   Case doesn't matter. On a tie, your own preset wins over a preset this plugin created, which wins over a built-in one. Only presets compatible with the selected printer and shown in the filament list count.

So name your presets after the product line, as Spoolman's vendor and filament names spell it:

| Spoolman vendor / filament | Preset it selects |
|---|---|
| Sunlu / HS PLA+ 2.0 Olive Green | Sunlu HS PLA+ 2.0 |
| Sunlu / HS PLA+ White | Sunlu HS PLA+ |
| Sunlu / PLA+ 2.0 Black | Sunlu PLA+ 2.0, else the built-in SUNLU PLA+ 2.0 |
| Epelay / Green (material PLA+) | Epelay PLA+ |

The selections are ordinary slot choices in the project, as if you had picked them by hand.

## Create missing presets

**Find missing presets** lists the Spoolman filaments that no preset matches. They are grouped by a proposed name: the vendor plus the product line, with color words dropped. For example "HS PLA+ 2.0 Olive Green" becomes "Sunlu HS PLA+ 2.0", and "Black" with material PLA+ becomes "Sunlu PLA+". You can edit the names before creating.

Each new preset:

- **inherits a built-in preset meant for any printer:** the vendor's own preset for that material when OrcaSlicer has one (the one sharing the most words with the line and adding the fewest others), otherwise Generic \<material\>. A printer-specific parent is used only when nothing else exists, because the new preset would then show up only for that printer;
- **takes from Spoolman:** the nozzle temperature, the bed temperature (smooth and textured plates), density and diameter, using the most common values among the filaments in the group;
- **is saved to** the local preset bundle `user/<your preset folder>/_local/spoolman/filament/`, which OrcaSlicer loads immediately.

Bundle presets are read-only templates. To tune one, edit it and save it as your own preset, either with the same name or as "Name @Printer". Your copy then wins the match. To remove a created preset, delete its file from the bundle folder and restart OrcaSlicer.

## Development

The matching and naming logic are plain functions, tested without OrcaSlicer:

```
python -m unittest discover -s tests
```

## License

GPL-3.0. See [LICENSE](LICENSE).
