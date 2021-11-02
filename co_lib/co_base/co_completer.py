from __future__ import annotations

import sys
from typing import List, Union

from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QCompleter, QPushButton

from .co_logger import xp

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
    def __init__(self):
        self.root_node: Union[Node, None] = Node('')

    def __str__(self) -> str:
        return f'{self.root}'

    def root(self) -> Union[Node, None]:
        return self.root_node

    def set_root(self, n: Node) -> Node:
        self.root_node = n
        return n

    def sort(self):
        if self.root_node:
            self.sort_int(self.root_node)

    def sort_int(self, n: Node):
        n.children.sort(key=lambda no: no.data.lower())
        for x in n.children:
            self.sort_int(x)


class PathCompleter(QCompleter):

    PathRole = Qt.UserRole + 1

    def __init__(self, root=None, parent=None):
        super().__init__()
        if root:
            self.create_model(root)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchContains)
        # self.setFilterMode(Qt.MatchStartsWith)

    def splitPath(self, path: str):
        xp('split in', path, 'out', path.split('.'))
        if not path.startswith('.'):
            path = '.' + path
        return path.split('.')

    def pathFromIndex(self, idx):
        xp('idx in', idx, 'out', idx.data(PathCompleter.PathRole))
        return idx.data(PathCompleter.PathRole)

    def create_model(self, root):
        model = QStandardItemModel(self)
        self.add_items(model, root)
        self.setModel(model)

    def add_items(self, parent, root: Node, path=''):
        item = QStandardItem()
        item.setText(root.data)
        data = f'{path}.{root.data}' if path else f'{root.data}'
        xp('add: txt', root.data)
        item.setData(data, PathCompleter.PathRole)
        parent.appendRow(item)
        for x in root.children:
            self.add_items(item, x, data)

    def on_btn(self):
        print('?????')
        pass


if __name__ == "__main__":

    ro = Root()
    r = ro.root()
    r3 = r.add_child(Node('obj44'))
    r1 = r.add_child(Node('tree'))
    r1_1 = r1.add_child(Node('branch'))
    r1_1_1 = r1_1.add_child(Node('leaf'))
    r1_2 = r1.add_child(Node('Roots'))
    r2 = r.add_child(Node('House'))
    r2_1 = r2.add_child(Node('Kitchen'))
    r2_2 = r2.add_child(Node('bedroom'))
    r4 = r.add_child(Node('obj88'))
    ro.sort()


    class MainApp(QWidget):
        def __init__(self):
            super().__init__()
            self.edt = QLineEdit(self)
            self.edt.setText('')
            self.completer = PathCompleter(r)
            self.edt.setCompleter(self.completer)
            layout = QVBoxLayout()
            btn = QPushButton('?')
            btn.clicked.connect(self.completer.on_btn)
            layout.addWidget(btn)
            layout.addWidget(self.edt)
            self.setLayout(layout)


    app = QApplication(sys.argv)
    hwind = MainApp()
    hwind.show()
    sys.exit(app.exec_())
