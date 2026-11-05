# Third-party notices

The project code retains its existing MIT license in `LICENSE`. That license does not relicense the following components or game assets. Full runtime license texts are supplied in `LICENSES/` in the Windows distribution.

| Component | Release build | License / source |
|---|---|---|
| CPython | 3.14 series | PSF license and included third-party notices; [source](https://github.com/python/cpython/tree/3.14) |
| PySide6 Essentials / Shiboken | 6.11.3 | LGPL v3 / GPL alternatives as stated upstream; [source](https://github.com/pyside/pyside-setup/tree/v6.11.3), [licensing](https://doc.qt.io/qtforpython-6/licenses.html) |
| Qt | 6.11.3 | LGPL v3 and component-specific licenses; [Qt source](https://github.com/qt/qtbase/tree/v6.11.3), [third-party code](https://doc.qt.io/qt-6/qtcore-attribution.html) |
| Pillow | 12.3.0 | HPND-style Pillow/PIL license and bundled library notices; [source](https://github.com/python-pillow/Pillow/tree/12.3.0) |
| PyInstaller bootloader | 6.22.3 | GPL v2 with the upstream bootloader exception; [source](https://github.com/pyinstaller/pyinstaller/tree/v6.22.3) |
| Original window icon | Installed Tcl/Tk icon | Tcl/Tk license; original artwork retained |

The Qt/Python libraries are bundled as runtime components; their source is available from the linked upstream projects. The editor's source and checked build instructions are available in this repository. To use modified runtime libraries, build the application from source with the replacement libraries; adjust the release dependency pins when doing so. This project does not restrict debugging or modification of those libraries under their applicable licenses.

The original game names, artwork and texts belong to their respective rights holders, including Nihon Falcom and NIS America. They are not covered by the project's MIT license. See `assets/ARTWORK.md` and `icons/original/sources.json` in the source repository for provenance. No affiliation or endorsement is implied.

This distribution uses core GUI, image and supporting Qt modules. The included upstream license directory preserves additional license texts used by Qt components; inclusion of a license text does not mean that every corresponding optional module is bundled.

Русский: MIT распространяется только на код проекта. У Python, Qt/PySide6, Pillow, загрузчика PyInstaller и игровых изображений собственные условия. Тексты лицензий находятся в `LICENSES/`; исходники библиотек доступны по ссылкам выше. Исходная лицензия проекта не изменена.
