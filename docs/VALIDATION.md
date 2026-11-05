# Validation / Проверки

**v1.0.0 · 5 November / 5 ноября 2026**

| Check / Проверка | Result / Результат |
|---|---|
| Full local regression suite / Полный локальный набор | **109 passed / прошли**, 1 skipped / пропущен; exit code 0 |
| Source self-test / Самопроверка исходников | Passed / Пройдена |
| Windows EXE self-test / Самопроверка EXE | Passed, frozen runtime / Пройдена, упакованный runtime |
| EXE demo / Демо EXE | Exit code / Код завершения **0** |
| Original icon / Исходная иконка | **13** matching frames / совпадающих кадров |
| EXE metadata / Метаданные EXE | **1.0.0**, Windows GUI, x64 |
| PNG manifest / Реестр PNG | **146** verified hashes / проверенных хешей |
| Master quartz / Мастер-кварцы | **31** images / изображение, **62** normal/EX entries / записи |
| In-game verification / Проверка в игре | Owner confirmed edited-save loading and correct items / Владелец подтвердил загрузку изменённого сохранения и правильность предметов |
| Installed game scan / Сканирование установленной игры | **14** tables / таблиц, **1,825** entries / записей |
| Master icons in RU/EN / Иконки мастер-кварцев RU/EN | **124** checks / проверки |
| Dependency check / Проверка зависимостей | `pip check`: no broken requirements / нарушений нет |

Local environment / Локальная среда: Windows 11, x64 Python 3.14.4, PySide6 6.11.3, Pillow 12.3.0, PyInstaller 6.22.3.

Machine-readable self-checks: [source](validation/source-selftest.json), [Windows EXE](validation/windows-selftest.json).

## Release checks / Релизные проверки

The checked build runs the full suite and source self-test, creates the EXE, verifies its original icon, GUI subsystem and version metadata, and runs the frozen self-test/demo from a temporary working directory with Python/development directories removed from PATH. Only then does it package an allowlisted ZIP and SHA-256 checksum.

Сборка выполняет полный набор тестов и самопроверку исходников, проверяет иконку, версию и GUI-режим EXE. Самопроверки EXE запускаются вне исходников, с отдельным APPDATA и без Python/среды разработки в PATH. Затем создаются ZIP по разрешённому списку файлов и SHA-256.

GitHub Actions also checks Python 3.10/3.14 on Windows and runs the same checked build. Its actual status is available in [Windows release runs](https://github.com/Sqzzzzzzz/Cold-Steel-IV-Save-Editor/actions/workflows/windows.yml). A matching version tag can publish only after required jobs succeed. A failed build or test prevents asset publication.

Independent release audit found and verified fixes for retained modal dialogs/menus, malformed catalog character metadata, and an unowned startup timer surviving its window. The timer keeps the same 360 ms delay. No theme, geometry, font or artwork changes were made.

Независимый аудит выявил удержание закрытых диалогов/меню, повреждённые метаданные персонажа и отложенный таймер, переживавший окно. Исправления проверены регрессионными тестами; задержка таймера 360 мс сохранена. Оформление не менялось.

## Earlier performance measurements / Предыдущие измерения

The interface optimization stage recorded three comparable process runs, six identical RU/EN screenshot pairs, and a 500-cycle stress scenario. These are historical measurements for that stage, not new v1.0.0 benchmarks: [report](INTERFACE_OPTIMIZATION_RU.md), [raw results](validation/ui-optimization.json).

## Limits / Ограничения

- The optional reference-save regression test skips without `CS4_REFERENCE_SAVE`; no personal save is bundled.
- In-game verification was reported by the project owner; the automated tests use synthetic saves.
- A separate Windows VM with Python uninstalled was not available. Isolated frozen-executable checks and hosted Windows builds cover runtime packaging, but do not replace every possible clean-machine configuration.
- Unsigned application; all game builds, mods, DPI settings and many-hour sessions have not been exhaustively tested.

Один необязательный тест пропущен без эталонного файла. Игровую проверку подтвердил владелец проекта; автоматические тесты используют искусственные сохранения. Отдельная Windows VM без установленного Python недоступна. Не заявляется проверка всех модов, DPI и многочасовых сценариев.
