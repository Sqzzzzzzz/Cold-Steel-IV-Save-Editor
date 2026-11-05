# Cold Steel IV Inventory Editor — Quick start

English · Русский: QUICK_START_RU.md

1. Extract the entire ZIP and run `CS4_Inventory_Editor.exe`. Python is not required.
2. Close the game and back up your saves outside its save directory.
3. Select your NISA PC game installation root containing `data`, or use automatic discovery.
4. Open a compatible `saveXXX.dat`, select an item, enter its quantity and click **Apply quantity**.
5. Review the changes and choose **Save a copy…** before overwriting any original.
6. If needed, place the edited copy in the game's save directory under a game-recognized `saveXXX.dat` name. Keep the original backup.

Requires 64-bit Windows 10/11 and your own installed NISA PC edition of Trails of Cold Steel IV. Supported saves: uncompressed GameData (3, 2), 1,463,976 bytes. Console/CLE formats are unsupported. Game tables and personal saves are not included.

Typical save folder: `%USERPROFILE%\Saved Games\FALCOM\ed8_psv4`.
Settings/cache: `%APPDATA%\CS4InventoryEditor_BETA` (retained for compatibility).

Switch EN/RU at the top of the window. If a localization patch replaced the English table, use **Tools → Import English catalog** with an original `t_item_en.tbl`.

The EXE is unsigned. Verify the ZIP SHA-256 against the separate `SHA256SUMS.txt` downloaded from the same release. Do not disable security software to run an unverified download.

Documentation, updates and issues:
https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor.

The project's MIT license does not cover bundled third-party libraries or game artwork. See LICENSE, THIRD_PARTY_NOTICES.md and LICENSES/.
