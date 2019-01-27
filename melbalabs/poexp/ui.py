import traceback

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLayout
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QWidget

import melbalabs.poexp.lib as lib

# https://github.com/baoboa/pyqt5/blob/master/examples/mainwindows/menus.py
# https://pythonprogramminglanguage.com/pyqt5-window-flags/
# http://doc.qt.io/qt-5/qt.html#WindowType-enum
# http://doc.qt.io/qt-5/qlayout.html#setContentsMargins
# http://zetcode.com/gui/pyqt5/layout/
# http://doc.qt.io/qt-5/stylesheet-examples.html
# https://github.com/baoboa/pyqt5/tree/master/examples/widgets
# https://build-system.fman.io/ fbs installer

# TODO movable window + save state
# TODO make installer with fbs
# TODO quit should close the whole app


class Window(QWidget):
    def __init__(self, update_fn, parent=None):

        super().__init__(parent)

        self.setStyleSheet('font: 15pt')

        self.update_fn = update_fn

        self.txt = QLabel('empty')  # no need to parent, layout reparents

        layout = QHBoxLayout(sizeConstraint=QLayout.SetFixedSize)  # shrink to fit
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txt)

        self.setLayout(layout)

        self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint
                | QtCore.Qt.WindowStaysOnTopHint
                | QtCore.Qt.Tool  # hide taskbar entry
        )

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(lib.SLEEP_SEC * 1000)

        self.move(0, 0)


    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quit_act = menu.addAction("quit")
        quit_act.triggered.connect(self.close)
        menu.exec_(event.globalPos())

    def update(self):
        try:
            chaos_recipe = self.update_fn()
            msg = str(chaos_recipe)
        except lib.PoeNotFoundException as e:
            msg = 'poe not found, nothing to do'
        except Exception as e:
            traceback.print_exc()
            msg = 'exception occurred, check logs'
        self.txt.setText(msg)


def gui_main():
    conf = lib.read_conf()
    app = QApplication([])

    def update_fn():
        return lib.run_once(conf)

    w = Window(update_fn=update_fn)
    w.show()
    app.exec_()
