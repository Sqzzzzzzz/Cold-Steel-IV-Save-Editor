import re
from pathlib import Path
from unittest.mock import patch
import pytest
from PySide6.QtCore import Qt,QPoint,QTimer
from PySide6.QtTest import QTest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication,QAbstractButton,QLabel,QMenu
from qt_window import MainWindow
from qt_backend import EditorCore
from qt_errors import error_text
from preview_demo import synthetic_demo_save


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app,tmp_path,monkeypatch):
    monkeypatch.setenv('APPDATA',str(tmp_path/'profile'))
    core=EditorCore();core.settings['auto_latest']=False
    core.base={20:{'id':20,'name':'Предмет','description':'Описание','category':'consumable','_locale':'ru'},
               60:{'id':60,'name':'Материал','description':'Материал','category':'material','_locale':'ru'}}
    core.english={20:{'id':20,'name':'Item','description':'Description','category':'consumable'},
                  60:{'id':60,'name':'Material','description':'Material','category':'material'}}
    core.rebuild_catalog();source=tmp_path/'save001.dat';source.write_bytes(synthetic_demo_save());core.open_file(source)
    with patch.object(MainWindow,'initial_load',lambda self:None):w=MainWindow(core)
    w.resize(1536,864);w.show();app.processEvents()
    yield w
    core.reset();w._quantity_user_edited=False;w.close();w.deleteLater();app.processEvents()


def test_real_widgets_edit_undo_and_language(window,app):
    w=window;before=w.core.save.bytes();w.show_section('catalog');w.show_item(20)
    w.qty.setValue(7);w.apply_single()
    assert w.core.quantity(20)==7
    w.undo();assert w.core.save.bytes()==before
    w.qty.setValue(25);w.lang.setCurrentIndex(1);app.processEvents()
    assert w.qty.value()==25 and w.core.save.bytes()==before
    assert 'Cold Steel IV' in w.windowTitle() and 'COLD STEEL IV' in w.subtitle.text()
    assert w.item_name.text()=='Item'
    assert w.cat_table.horizontalHeader().sectionsMovable() is False


def test_navigation_sorting_and_search_do_not_modify_save(window,app):
    w=window;before=w.core.save.bytes()
    for section in ('tools','inventory','catalog'):
        w.show_section(section);app.processEvents()
    w.cat_search.setText('Предмет');QTest.qWait(250);app.processEvents()
    assert w.cat_table.rowCount()==1
    w.cat_search.clear();w.cat_table.sortItems(0,Qt.SortOrder.DescendingOrder);app.processEvents()
    assert w.core.save.bytes()==before


def test_table_sorting_is_independent_and_matches_header(window):
    w=window;before=w.core.save.bytes()
    def ids(table):
        return [table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in range(table.rowCount())]
    w.cat_table.horizontalHeader().sectionClicked.emit(1)
    catalog_ids=ids(w.cat_table)
    assert catalog_ids==sorted(catalog_ids,reverse=True)
    w.inv_table.horizontalHeader().sectionClicked.emit(3)
    w.inv_table.horizontalHeader().sectionClicked.emit(3)
    inventory_ids=ids(w.inv_table)
    w.show_section('inventory');w.show_section('catalog')
    assert ids(w.cat_table)==catalog_ids
    assert ids(w.inv_table)==inventory_ids
    assert w.cat_table.horizontalHeader().sortIndicatorOrder()==Qt.SortOrder.DescendingOrder
    assert w.inv_table.horizontalHeader().sortIndicatorOrder()==Qt.SortOrder.DescendingOrder
    w.cat_table.horizontalHeader().sectionClicked.emit(1)
    assert ids(w.cat_table)==sorted(catalog_ids)
    assert ids(w.inv_table)==inventory_ids
    assert w.core.save.bytes()==before


def test_language_keeps_pending_flag_for_default_quantity(window,app):
    w=window
    w.core.base[42]={'id':42,'name':'New item','category':'consumable'}
    w.core.rebuild_catalog();w.update_tables();w.show_item(42)
    before=w.core.save.bytes()
    w.qty.setValue(2);w.qty.setValue(1)
    assert w.has_pending_quantity()
    w.lang.setCurrentIndex(1);app.processEvents()
    assert w.qty.value()==1 and w.has_pending_quantity()
    from qt_changes_dialog import ChangesDialog
    dialog=ChangesDialog(w,'copy')
    assert 'has not been applied' in dialog.note.text()
    dialog.deleteLater()
    assert w.core.save.bytes()==before


def test_quantity_context_menu_opens(window):
    shown=[]
    def choose_quantity():
        menus=window.qty.findChildren(QMenu)
        for menu in menus:
            if menu.isVisible():
                shown.append([x.text() for x in menu.actions()])
                menu.actions()[-1].trigger()
                menu.close()
    QTimer.singleShot(50,choose_quantity)
    window.qty.customContextMenuRequested.emit(QPoint(0,0))
    assert shown==[['1','10','50','99']]
    assert window.qty.value()==99


def test_english_controls_and_crc_error_are_localized(window,app):
    window.lang.setCurrentIndex(1);app.processEvents()
    for obj in window.findChildren(QLabel)+window.findChildren(QAbstractButton)+window.findChildren(QAction):
        if obj in (window.rail_folder,window.save_line):continue
        value=(obj.text() if hasattr(obj,'text') else '')+' '+obj.toolTip()
        assert not re.search('[А-Яа-яЁё]',value),value
    assert 'checksum mismatch' in error_text('Контрольная сумма CS4 не совпадает; файл повреждён или изменён','en')


def test_all_category_icons_have_artwork_instead_of_diamond(window):
    from PySide6.QtWidgets import QTreeWidgetItemIterator
    from qt_hud_widgets import hud_icon
    from categories import CATEGORY_NAMES
    diamond=hud_icon('unknown',25).pixmap(25,25).toImage()
    seen=set()
    for tree in (window.cat_tree,window.inv_tree):
        iterator=QTreeWidgetItemIterator(tree)
        while iterator.value():
            item=iterator.value();seen.add(item.data(0,Qt.ItemDataRole.UserRole))
            assert not item.icon(0).isNull()
            assert item.icon(0).pixmap(25,25).toImage()!=diamond,item.text(0)
            iterator+=1
    assert set(CATEGORY_NAMES)<=seen


def test_master_category_and_items_do_not_use_empty_slot(window):
    from PySide6.QtWidgets import QTreeWidgetItemIterator
    from catalog_core import resource_path
    from PySide6.QtGui import QIcon
    empty=QIcon(str(resource_path('icons/original/Master (Sen III Slot).png'))).pixmap(25,25).toImage()
    iterator=QTreeWidgetItemIterator(window.cat_tree)
    while iterator.value():
        item=iterator.value()
        if item.data(0,Qt.ItemDataRole.UserRole)=='quartz_master':
            assert item.icon(0).pixmap(25,25).toImage()!=empty
            assert item.icon(0).pixmap(25,25).toImage()==window._icon(None,{'category':'quartz_master','name':'Emblem'}).pixmap(25,25).toImage()
            assert window._icon_sources[None].path.name=='Emblem (Sen IV MQ).png'
            assert item.icon(0).pixmap(25,25,QIcon.Mode.Selected).toImage()==item.icon(0).pixmap(25,25,QIcon.Mode.Normal).toImage()
            break
        iterator+=1
    else:pytest.fail('Master category is missing')
    for item_id,name in [(3228,'Эрда'),(3268,'Эрда EX'),(3230,'Воден'),(3270,'Воден EX')]:
        icon=window._icon(item_id,{'category':'quartz_master','name':name})
        rendered=icon.pixmap(90,90).toImage()
        assert not rendered.isNull() and rendered.pixelColor(0,0).alpha()==0
        assert rendered.pixelColor(45,45).alpha()>0
        assert window._icon_sources[item_id].verified


def test_switching_to_english_refreshes_partial_cache(window,app):
    window.core.english={}
    with patch.object(window,'scan_game') as scan:
        window.lang.setCurrentIndex(1);app.processEvents()
        scan.assert_called_once_with(None,silent=True)
