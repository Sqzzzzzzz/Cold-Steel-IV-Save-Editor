<div align="center">

# Cold Steel IV · Inventory Editor

**A Windows inventory and save editor for Trails of Cold Steel IV — NISA PC**

[![Release](https://img.shields.io/badge/release-v1.0.0-b8212f)](https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor./releases/latest)
![Windows x64](https://img.shields.io/badge/Windows-x64-3278c8)
![Languages](https://img.shields.io/badge/interface-EN%20%2F%20RU-8b5cf6)
[![Code license](https://img.shields.io/badge/code-MIT-6b7280)](LICENSE)

**English** · [Русский](README_RU.md)

[Download v1.0.0](https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor./releases/tag/v1.0.0) · [Getting started](#getting-started) · [Compatibility](#compatibility) · [Troubleshooting](#troubleshooting)

<img src="docs/screenshots/catalog-en.png" alt="The real English item catalog and item details" width="1100">

</div>

Browse the installed game's item catalog, edit inventory quantities, and review changes before saving. The editor uses the existing Crimson Steel interface with original game artwork. Screenshots show the real application with demonstration data.

> **Back up your saves first.** Use **Save a copy…** for your first edit. Close the game while editing, and keep an untouched copy outside the game's save directory.

## Features

| Area | What you can do |
|---|---|
| Inventory & catalog | Search names, IDs and descriptions; filter by category, source, ownership and favorites |
| Editing | Set quantities from 0 to 99, add or remove items, and apply changes to multiple selections |
| Review & recovery | Review pending changes, undo edits, reset to the loaded file, compare saves and export CSV |
| File protection | Save separate copies; overwrite with a backup; reject unsupported formats and externally modified files |
| Languages | English and Russian interface, separate catalog translations and English-catalog import |
| Artwork | 31 native CS4 master-quartz images covering all 62 normal/EX entries |
| Game discovery | Detect the installed game or select its folder; scan base-game and DLC item tables |

## Download

Open the **[latest release](https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor./releases/latest)** and download:

- `Cold_Steel_IV_Inventory_Editor_v1.0.0_Windows_x64.zip` — the complete application.
- `SHA256SUMS.txt` — the archive checksum.

The ZIP contains the EXE, English/Russian quick-start instructions, license notices and version information. **Python is not required.** GitHub's automatically generated source archives are for developers.

To verify the download in PowerShell:

```powershell
Get-FileHash .\Cold_Steel_IV_Inventory_Editor_v1.0.0_Windows_x64.zip -Algorithm SHA256
```

Compare the result with `SHA256SUMS.txt` from the same release.

## Getting started

1. Extract the entire ZIP to a writable folder.
2. Run `CS4_Inventory_Editor.exe`.
3. Let the editor find the game, or select the installation root containing `data`.
4. Open `saveXXX.dat`, or use **Latest save**.
5. Select an item, enter a quantity, and click **Apply quantity**.
6. Review the changes and choose **Save a copy…**. Entering a quantity alone does not apply it.

Typical save location: `%USERPROFILE%\Saved Games\FALCOM\ed8_psv4`.
An edited copy may need a game-recognized `saveXXX.dat` filename to appear in the game's load menu; preserve your original before placing it there.

Settings and catalog caches remain in `%APPDATA%\CS4InventoryEditor_BETA` for compatibility with earlier previews. The folder name is retained deliberately; updating does not discard your existing catalog or preferences.

## Compatibility

| Requirement | Details |
|---|---|
| Windows | Windows 10/11, 64-bit; local validation on Windows 11 and automated Windows builds |
| Game | The Legend of Heroes: Trails of Cold Steel IV, **NISA PC edition** |
| Save | Uncompressed GameData **(3, 2)**, exactly **1,463,976 bytes** |
| Catalog | Installed game tables such as `t_item.tbl` / `t_item_en.tbl`, including installed DLC tables |
| Internet | Needed to download the release; normal editing and local scans work offline |

PS4, Switch, CLE and incompatible save layouts are rejected. This editor changes inventory items, not character stats, story flags or every resource counter.

The game tables and personal saves are **not included**. You need your own installed game for a complete catalog. The built-in artwork is already bundled; extraction tools are not needed for normal use.

## Languages

Choose **English** or **Русский** at the top of the window. Item text comes from your local game tables and cached translations. Russian fallback names and descriptions are supplied for 103 standard DLC items.

If a localization patch replaced the original English table, import an original `t_item_en.tbl` using **Tools → Import English catalog**. Russian entries are preserved. Missing translations are marked with their source language rather than invented.

## Screenshots

### Russian interface

<img src="docs/screenshots/inventory-ru.png" alt="The real Russian inventory interface and master-quartz artwork" width="1100">

<details>
<summary>All 31 native CS4 master-quartz images</summary>

<img src="docs/screenshots/master-quartz.png" alt="The 31 original master-quartz images" width="1024">

Normal and EX versions share the corresponding master's image.

</details>

## Known limitations

- Compatibility is limited to the validated NISA PC save layout. Other builds and mods may be rejected.
- Some non-master item families use shared CS3 category artwork.
- Translations depend on the game files available locally; not every modded item has a translation.
- The executable is not code-signed. Windows may show a publisher/reputation prompt; verify the source and checksum before deciding whether to run it.
- The owner confirmed that an edited save loads in CS4 and that the edited items are correct. This does not establish compatibility with every game revision or mod.

## Troubleshooting

| Problem | What to check |
|---|---|
| Game not found | Select the installation root containing `data`, not the save folder |
| English item names remain Russian | Import the original English table; a localization patch may have replaced it |
| File is rejected | Confirm the edition, save size and checksum; keep the original and report the exact error |
| Edited copy is not listed by the game | Check its folder and `saveXXX.dat` filename, with the game closed |
| Overwrite is blocked | The source may have changed since loading; save a separate copy and reload deliberately |
| EXE does not start | Extract the ZIP first; use the x64 build; check Windows Security history and report the exact message |

Report reproducible problems in [Issues](https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor./issues). Include the version, Windows version, steps and a screenshot. Do not attach personal saves or copyrighted game tables publicly.

## Development

Use 64-bit **Python 3.10–3.14**; release builds use Python 3.14.

```powershell
git clone https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor..git Cold-Steel-IV-Save-Editor
cd Cold-Steel-IV-Save-Editor
py -3.14 -m venv .qt-preview-venv
.\.qt-preview-venv\Scripts\python.exe -m pip install -r requirements-release.txt
.\.qt-preview-venv\Scripts\python.exe tools\build_release.py
```

The build runs tests, source and frozen self-checks, verifies the original icon and EXE version, and packages the ZIP. Outputs: `dist/` and `release/`. `Build_Qt_Preview_EXE.bat` and `Собрать_EXE.bat` remain available as convenience launchers.

GitHub Actions checks pull requests and `main`, then builds and publishes matching `vMAJOR.MINOR.PATCH` tags only after the required jobs pass. See [Contributing](CONTRIBUTING.md), [validation](docs/VALIDATION.md), [changelog](CHANGELOG.md), and [release notes](docs/releases/v1.0.0.md).

## Credits & license

CS4 adaptation: [Sqzzzzzzz](https://github.com/Sqzzzzzzz). Interface based on the [CS3 Inventory Editor](https://github.com/Sqzzzzzzz/Cold-Steel-3-Inventory-Editor-RU-ENG-). Technical references: [SenPatcher](https://github.com/AdmiralCurtiss/SenPatcher) and [save-converters](https://github.com/ItsAllAboutTheCode/save-converters).

The existing [MIT license](LICENSE) covers the project code. Dependency licenses and game artwork have separate terms; see [third-party notices](THIRD_PARTY_NOTICES.md) and [artwork provenance](assets/ARTWORK.md).

Unofficial project; not affiliated with Nihon Falcom or NIS America.
