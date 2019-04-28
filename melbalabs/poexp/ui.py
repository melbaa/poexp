import traceback
import time

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
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
# http://doc.qt.io/qt-5/qguiapplication.html#quitOnLastWindowClosed-prop
# http://doc.qt.io/qt-5/qpainter.html#details

"""
on + click, open a new window, paint rectangles of chaos items on a click through window
    setAttribute(Qt::WA_NoSystemBackground, true);
    setAttribute(Qt::WA_TranslucentBackground, true);
    setAttribute(Qt::WA_TransparentForMouseEvents);
    setWindowFlags(Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint | Qt::Tool);
rectangles requre position and area, both come from stash
stash comes from update function
modify ChaosRecipe to have position and size of items, not just counters
poe inventory rectangle position will be hardcoded
on - click, hide rectangle overlay (close/destroy window so it stops updating?)
"""

BUTTON_READY_TXT = '+'
BUTTON_WAIT_TXT = 'o'





class Window(QWidget):
    def __init__(self, update_fn, parent=None):

        super().__init__(parent)

        self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint
                | QtCore.Qt.WindowStaysOnTopHint
                | QtCore.Qt.Tool  # hide taskbar entry
        )

        self.setStyleSheet('font: 15pt')

        self.txt = QLabel('empty')  # no need to parent, layout reparents

        self.button = QPushButton(BUTTON_WAIT_TXT)
        self.button.setFixedWidth(20)
        self.button.clicked.connect(self.click_recipe_items)

        layout = QHBoxLayout(sizeConstraint=QLayout.SetFixedSize)  # shrink to fit
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button)
        layout.addWidget(self.txt)

        self.setLayout(layout)

        # the last_ values are modified only when checking for updates
        # the self.xxx_recipe values are the state we work on between updates
        self.last_chaos_recipe = self.chaos_recipe = None
        self.last_gemcutter_recipe = self.gemcutter_recipe = None
        self.last_six_socket_recipe = self.six_socket_recipe = None
        self.update_fn = update_fn
        self.move_items_gen = None

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(lib.SLEEP_SEC * 1000)

        self.move(0, 0)


    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quit_act = menu.addAction("quit")
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.exec_(event.globalPos())

    def update(self):
        # save the last reply from server, use it to compare to new replies
        # when they are different, it's an update

        msg = ''
        try:
            update_arrived = False
            chaos_recipe, gemcutter_recipe, six_socket_recipe, poe_stash = self.update_fn()

            if self.last_chaos_recipe != chaos_recipe and lib.is_recipe_ready(chaos_recipe):
                # we pulled something from API and it was an actual update
                # we also have enough items
                self.last_chaos_recipe = self.chaos_recipe = chaos_recipe
                update_arrived = True

            if self.last_gemcutter_recipe != gemcutter_recipe and lib.is_recipe_ready(gemcutter_recipe):
                self.last_gemcutter_recipe = self.gemcutter_recipe = gemcutter_recipe
                update_arrived = True

            if self.last_six_socket_recipe != six_socket_recipe and lib.is_recipe_ready(six_socket_recipe):
                self.last_six_socket_recipe = self.six_socket_recipe = six_socket_recipe
                update_arrived = True

            if update_arrived:
                self.button.setText(BUTTON_READY_TXT)
                self.move_items_gen = lib.move_ready_items_to_inventory(
                    self.chaos_recipe, self.gemcutter_recipe, self.six_socket_recipe)

            msg = lib.format_chaos_recipe(chaos_recipe, colorize=False)
            msg += ' | ' + lib.format_gemcutter_recipe(gemcutter_recipe)
            msg += ' ' + lib.format_six_socket_items(poe_stash)
            msg += ' | ' + lib.format_identified_items(poe_stash)
        except lib.PoeNotFoundException as e:
            msg = 'poe not found, nothing to do'
        except Exception as e:
            traceback.print_exc()
            msg = 'exception occurred, check logs'
        self.txt.setText(msg)

    def click_recipe_items(self):
        if not lib.any_recipes_ready([
            self.chaos_recipe,
            self.gemcutter_recipe,
            self.six_socket_recipe,
        ]):
            self.button.setText(BUTTON_WAIT_TXT)
            return
        try:
            time.sleep(1)  # give user a chance to stop using the mouse
            self.chaos_recipe, self.gemcutter_recipe, self.six_socket_recipe = next(self.move_items_gen)
            if not lib.any_recipes_ready([
                self.chaos_recipe,
                self.gemcutter_recipe,
                self.six_socket_recipe,
            ]):
                self.button.setText(BUTTON_WAIT_TXT)
        except StopIteration:
            self.button.setText(BUTTON_WAIT_TXT)


def gui_main():
    conf = lib.read_conf()
    app = QApplication([])

    def update_fn():
        return lib.run_once(conf)

    w = Window(update_fn=update_fn)
    w.show()
    return app.exec_()
