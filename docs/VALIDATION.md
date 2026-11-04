# Validation / Проверки

**0.1.2-preview · 4 November / 4 ноября 2026**

## Results / Результаты

| Check / Проверка | Result / Результат |
|---|---|
| Regression suite / Регрессионные тесты | **84 passed / прошли**, 1 skipped / пропущен |
| Source self-test / Самопроверка исходной программы | Passed / Пройдена |
| Windows EXE self-test / Самопроверка Windows EXE | Passed / Пройдена |
| Packaged demo / Демо собранной программы | Exit code / Код завершения **0** |
| Bundled PNG hashes / Хеши PNG | **146** matched / совпали |
| Native CS4 master textures / Исходные текстуры мастер-кварцев CS4 | **31** |
| Master entries / Записи мастер-кварцев | **62** normal + EX / обычные + EX |
| RU/EN master-icon checks / Проверки иконок RU/EN | **124**, no empty slots / без пустых слотов |
| Installed game scan / Сканирование установленной игры | **14** tables / таблиц, **1825** entries / записей |
| English names and descriptions / Английские названия и описания | **1825** entries; no Cyrillic leaks / без кириллицы |

Environment / Среда: **Windows 11, Python 3.14.4, PySide6 6.11.3, PyInstaller 6.22.3**.

Machine-readable self-test evidence: [source](validation/source-selftest.json), [Windows executable](validation/windows-selftest.json).

## Coverage / Что проверено

- CRC, format validation, atomic batch edits and unchanged non-inventory bytes.
- Save copies, no-overwrite behavior, backups, external-change protection and undo.
- Unicode paths, CSV export, language switching, sorting, filters and real Qt controls.
- Native master artwork, normal/EX names, manual-image priority and incomplete English-cache recovery.
- Bounded PKA/LZ4/BC7 extraction, SHA-256 provenance and invalid-input handling.

Проверены CRC, формат, атомарность массовых правок, сохранность данных вне инвентаря, копии, резервное копирование, защита от внешних изменений и отмена. Проверки интерфейса охватывают Unicode-пути, CSV, языки, сортировку, фильтры, мастер-кварцы и восстановление английского кэша.

## Remaining limits / Что ещё не проверено

Loading an edited save in CS4 itself is pending. The optional public reference-save test skips when `CS4_REFERENCE_SAVE` is unavailable. No personal save is bundled. Non-master artwork can use shared CS3 family images. This is a preview, not a claim of compatibility with every game build or mod.

Загрузка изменённого сохранения самой игрой ещё не проверена. Один тест пропущен из-за отсутствия эталона `CS4_REFERENCE_SAVE`. Личные сохранения в проект не включены. Для предметов, не являющихся мастер-кварцами, могут использоваться общие иконки CS3. Это предварительная версия; совместимость со всеми сборками игры и модами не заявляется.
