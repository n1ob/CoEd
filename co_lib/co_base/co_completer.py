from __future__ import annotations

import sys
from itertools import count
from typing import Union, List, Callable

from PySide2.QtCore import Qt, QRect, QModelIndex, Slot, Signal
from PySide2.QtGui import QKeyEvent, QStandardItemModel, QStandardItem, QFocusEvent, QMouseEvent
from PySide2.QtWidgets import QLineEdit, QCompleter, QWidget, QVBoxLayout, QApplication, QAbstractItemView, QTableWidget

from co_lib.co_base.co_logger import xp_worker, xp, flow
'''
Referencing objects
You can reference an object by its DataName or by its DataLabel. In the case of a DataLabel, it must be enclosed in 
double << and >> symbols, such as <<Label>>.

You can reference any numerical property of an object. For example, to reference a Cylinder's height, you may use 
Cylinder.Height or <<Long_name_of_cylinder>>.Height.

To reference list objects, use <<object_label>>.list[list_index] or object_name.list[list_index]. If you want for 
example to reference a constraint in a sketch, use <<MySketch>>.Constraints[16]. If you are in the same sketch you 
may omit its name and just use Constraints[16].
'''


# it = count()
# xp_worker.log_path_set('C:/Users/red/AppData/Roaming/JetBrains/PyCharmCE2021.2/scratches/coed.log')

SEPARATORS = ['~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')',
                   '+', '{', '}', '|', ':', '"', "'", "<", ">", "?", ",",
                   "/", ";", '[', ']', '\\', '\n', '\t', '=', '-', ' ', '']
# ".",


class Node:
    def __init__(self, s: str):
        self.parent: Union[Node, None] = None
        self.children: List[Node] = list()
        self.data: str = s

    def __str__(self) -> str:
        return f'{self.data} {[str(x) for x in self.children]}'

    def add_child(self, n: Node) -> Node:
        n.parent = self
        self.children.append(n)
        return n


class Root:
    def __init__(self, n=None):
        self.root_node: Union[Node, None] = n

    def __str__(self) -> str:
        return f'{self.root}'

    def root(self) -> Union[Node, None]:
        return self.root_node

    def add_root(self, n: Node) -> Node:
        self.root_node = n
        return n

    def sort(self):
        if self.root_node:
            self.sort_int(self.root_node)

    def sort_int(self, n: Node):
        n.children.sort(key=lambda no: no.data.lower())
        for x in n.children:
            self.sort_int(x)


class LineEdit(QLineEdit):

    def __init__(self, item, root: Node, parent):
        super(LineEdit, self).__init__()
        self.parent = parent
        self.item = item
        self.c = PathCompleter(root)
        self.c.setWidget(self)
        self.c.highlighted.connect(self.on_highlighted)
        self.c.activated.connect(self.on_insert_completion)
        self.cur_sel_prefix = ''
        self.trigger_key = Qt.Key_Space
        self.trigger_chars = 2
        self.auto_trigger = True
        # self.period_is_trigger = True
        self.p: QAbstractItemView = self.c.popup()
        # self.focus_out = f'background: #555555'
        # self.focus_in = f'background: #BBBBBB'
        # self.edit_focus_out = f'background: #00FF00'
        # self.edit_focus_in = f'background: #FF0000'
        self.backup = ''
        self.exp_eval = None
        self.exp_eval_passed = True
        self.exp_save = None
        self.exp_save_passed = True
        self.textEdited.connect(self.on_txt_edited)

    @flow
    def on_txt_edited(self, txt):
        self.exp_eval_passed = self.exp_eval(txt)

    @flow
    def on_ret_pressed(self):
        xp('on_ret_pressed')
        self.exp_save_passed = self.exp_save(self.item, self.text())

    @flow
    def set_exp_eval(self, func: Callable):
        self.exp_eval = func

    @flow
    def set_exp_save(self, func: Callable):
        self.exp_save = func

    @flow
    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        if not self.p.hasFocus():
            self.setReadOnly(True)
        # self.setStyleSheet(self.focus_out if self.isReadOnly() else self.edit_focus_out)

    @flow
    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        # self.setStyleSheet(self.focus_in if self.isReadOnly() else self.edit_focus_in)

    @flow
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        super().mouseDoubleClickEvent(event)
        self.setReadOnly(False)
        # self.setStyleSheet(self.edit_focus_in)

    @flow
    def keyPressEvent(self, event: QKeyEvent):
        xp('event', event.key())
        if self.isReadOnly():
            xp('isReadOnly')
            if event.key() in [Qt.Key_F2, Qt.Key_Enter, Qt.Key_Return]:
                xp('Qt.Key_F2, Qt.Key_Enter, Qt.Key_Return')
                self.setReadOnly(False)
                # self.setStyleSheet(self.edit_focus_in)
                return

        if not self.p.isVisible() and not self.isReadOnly():
            xp('~isReadOnly & ~isVisible')
            if event.key() in [Qt.Key_Up, Qt.Key_Down]:
                xp('Qt.Key_Up, Qt.Key_Down')
                return
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                xp('Qt.Key_Enter, Qt.Key_Return')
                if self.exp_eval_passed:
                    xp('eval_passed')
                    self.on_ret_pressed()
                    if self.exp_save_passed:
                        xp('save_passed')
                        self.backup = self.text()
                        self.parent: QWidget
                        self.parent.setFocus()
                    else:
                        xp('~save_passed')
                        return
                else:
                    xp('~eval_passed')
                return
            if event.key() in [Qt.Key_Escape]:
                xp('Qt.Key_Escape')
                self.setText(self.backup)
                self.parent: QWidget
                self.parent.setFocus()
                return

        super().keyPressEvent(event)

        if self.isReadOnly():
            xp('isReadOnly -> return')
            return

        if self.auto_trigger:
            xp('auto_trigger')
            self.detect_auto()

        if self.is_shortcut(event):
            xp('is_shortcut')
            self.cur_sel_prefix = self.get_prefix()
            xp(f'prefix <{self.cur_sel_prefix}>')
            if self.cur_sel_prefix:
                self.show_completions(self.cur_sel_prefix)
            else:
                self.show_completions('.')

        # if self.period_is_trigger:
        #     if event.key() == Qt.Key_Period:
        #         self.detect_period()
        # if self.c.popup().isVisible():
        #     if not self.c.currentCompletion():
        #         xp(next(it), '-> not currentCompletion')
        #         self.hide_pop()
        #     elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
        #         xp(next(it), '-> is_enter')
        #         self.hide_pop()
        #     elif event.key() in [Qt.Key_Escape, Qt.Key_Backtab, Qt.Key_Left, Qt.Key_Right]:
        #         xp(next(it), '-> is_escape')
        #         self.hide_pop()

    # @flow
    def is_shortcut(self, event: QKeyEvent):
        return (event.modifiers() & Qt.ControlModifier) and (event.key() == self.trigger_key)

    # @flow
    # def detect_period(self):
    #     self.hide_pop()
    #     p = self.get_prefix()
    #     if len(p) > 1:
    #         self.cur_sel_prefix = p
    #         self.show_completions(p)

    @flow
    def detect_auto(self):
        self.hide_pop()
        p = self.get_prefix()
        if len(p) >= self.trigger_chars:
            self.cur_sel_prefix = p
            self.show_completions(self.cur_sel_prefix)

    @flow
    def show_completions(self, completion_prefix):
        xp('completion_prefix', completion_prefix)
        self.c.setCompletionPrefix(completion_prefix)
        if self.c.currentCompletion():
            # self.c.popup().setCurrentIndex(self.c.completionModel().index(0, 0))
            p: QAbstractItemView = self.c.popup()
            cr: QRect = self.cursorRect()
            xp('cursorRect', cr)
            cr.setWidth(p.sizeHintForColumn(0) + p.verticalScrollBar().sizeHint().width())
            self.c.complete(cr)
            xp(f'popup hasFocus {self.p.hasFocus()}')

    @flow
    def on_insert_completion(self, completion):
        xp('completion', completion)
        cur_pos = self.cursorPosition()
        self.setSelection(cur_pos - len(self.cur_sel_prefix), len(self.cur_sel_prefix))
        self.insert(completion)
        self.hide_pop()

    # @flow
    def on_highlighted(self, completion):
        return ''

    @flow
    def hide_pop(self):
        if self.c.popup().isVisible():
            self.c.popup().hide()

    @flow
    def get_prefix(self):
        txt = self.text()
        cur_pos = self.cursorPosition()
        xp('ln txt', txt, 'cur pos', cur_pos)
        s = ''
        if txt:
            sep_before = -1
            for i in range(cur_pos - 1, 0, -1):
                if txt[i] in SEPARATORS:
                    sep_before = i
                    break
            if sep_before == -1:
                s = txt[:cur_pos]
            else:
                s = txt[sep_before + 1:cur_pos]
        xp('prefix out', s)
        return s


class TableLineEdit(LineEdit):
    edt_finished = Signal(object, object)
    ret_pressed = Signal(object, object)
    txt_edited = Signal(object, object, str)

    def __init__(self, item, comp_root: Node, driving: bool, parent):
        super().__init__(item, comp_root, parent)
        self.item = item
        self.setText(item.exp)
        self.editingFinished.connect(self.re_edt_finished)
        self.textEdited.connect(self.re_txt_edited)
        self.returnPressed.connect(self.re_ret_pressed)
        self.setReadOnly(True)
        self.setEnabled(driving)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        # self.completer = PathCompleter(comp_root)
        # self.setCompleter(self.completer)

    @Slot()
    def re_edt_finished(self):
        pt = self.pos()
        self.edt_finished.emit(self, pt)

    @Slot()
    def re_ret_pressed(self):
        pt = self.pos()
        self.ret_pressed.emit(self, pt)

    @Slot(str)
    def re_txt_edited(self, txt: str):
        pt = self.pos()
        self.txt_edited.emit(self, pt, txt)


class PathCompleter(QCompleter):

    PathRole = Qt.UserRole + 1

    def __init__(self, root):
        super(PathCompleter, self).__init__()
        self.create_model(root)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        # self.completer.setFilterMode(Qt.MatchContains)
        self.setFilterMode(Qt.MatchStartsWith)
        self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        # x: QAbstractItemView = self.popup()

    @flow
    def create_model(self, data):
        model = QStandardItemModel(self)
        self.add_items(model, data)
        self.setModel(model)

    @flow
    def add_items(self, parent, root: Node, path=''):
        item = QStandardItem()
        item.setText(root.data)
        data = f'{path}.{root.data}' if path else f'{root.data}'
        item.setData(data, PathCompleter.PathRole)
        parent.appendRow(item)
        for x in root.children:
            self.add_items(item, x, data)

    @flow
    def splitPath(self, path: str):
        xp('path in:', path, 'prefix:', self.completionPrefix(), 'comp:', self.currentCompletion())
        if not path.startswith('.'):
            path = '.' + path
        xp('path out', path.split('.'))
        return path.split('.')

    @flow
    def pathFromIndex(self, idx):
        idx: QModelIndex
        xp('idx in:', idx.row(), 'data out:', idx.data(PathCompleter.PathRole))
        return idx.data(PathCompleter.PathRole)


if __name__ == "__main__":

    ro = Root(Node(''))
    r = ro.root()
    r3 = r.add_child(Node('obj14'))
    r1 = r.add_child(Node('tree'))
    r1_1 = r1.add_child(Node('branch'))
    r1_1_1 = r1_1.add_child(Node('leaf'))
    r1_2 = r1.add_child(Node('Roots'))
    r2 = r.add_child(Node('House'))
    r2_1 = r2.add_child(Node('Kitchen'))
    r2_2 = r2.add_child(Node('bedroom'))
    r4 = r.add_child(Node('obj88'))
    r5 = r.add_child(Node('obj123'))
    r6 = r.add_child(Node('obj89'))
    ro.sort()


    class MainApp(QWidget):
        def __init__(self):
            super().__init__()
            flags: Qt.WindowFlags = Qt.Window
            flags |= Qt.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.tableWidget = QTableWidget(self)
            self.tableWidget.setColumnCount(2)
            self.tableWidget.setRowCount(6)
            self.resize(600, 800)
            for x in range(6):
                wid = TableLineEdit(r, self.tableWidget)
                wid.edt_finished.connect(self.edit_finished)
                wid.ret_pressed.connect(self.return_pressed)
                wid.txt_edited.connect(self.text_edited)
                self.tableWidget.setCellWidget(x, 1, wid)
            layout = QVBoxLayout()
            layout.addWidget(self.tableWidget)
            self.setLayout(layout)
            self.tableWidget.currentCellChanged.connect(self.cur_cell_changed)
            # self.tableWidget.currentItemChanged.connect(self.e)

        @flow
        def edit_finished(self, item, pt):
            xp(f'text <{item.text()}>')

        @flow
        def return_pressed(self, item, pt):
            xp(f'text <{item.text()}>')

        @flow
        def text_edited(self, item, pt, txt):
            xp(f'text <{txt}>')

        @flow
        def cur_cell_changed(self, cr, cc, pr, pc):
            xp(f'cur row {cr} cur col {cc} prev row {pr} prev col {pc}')

        @flow
        def e(self, cur, pre):
            xp(f'cur {cur} pre {pre}')


    app = QApplication()
    hwind = MainApp()
    hwind.show()
    app.exec_()
    xp_worker.keep_running = False
    sys.exit()

