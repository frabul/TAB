

from PySide6.QtWidgets import QApplication, QLabel
import PySide6.QtCore
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QPixmap, QImage, QMouseEvent
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QWidget
import numpy as np
import cv2
from types import MethodType
from time import sleep
from typing import Optional
import typing
from . import QDispatcher  
##################################attempted relative import with no known parent package####################################################################################################
######################################################################################################################################


class ImageViewer(QMainWindow):
    min_width = 100
    mouse_move_handler = None
    mouse_press_handler = None
    mouse_release_handler = None

    def __init__(self, name: str, image: np.ndarray):
        super().__init__()
        flags = self.windowFlags()
        flags = flags & (~(Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowMinimizeButtonHint))
        self.setWindowFlags(flags)
        self.title = name
        self.setWindowTitle(self.title)
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: lightgreen;")
        self.set_image(image)

        self.label.mousePressEvent = MethodType(ImageViewer.mousePressEvent_wrapper, self)
        self.label.mouseReleaseEvent = MethodType(ImageViewer.mouseReleaseEvent_wrapper, self)
        self.label.mouseMoveEvent = MethodType(ImageViewer.mouseMoveEvent_wrapper, self)

    def __update_size(self):
        self.label.setGeometry(0, 0, self.qImg.width(), self.qImg.height())
        w = max(self.qImg.width(), 30)  
        h = max(self.qImg.height(), 30)
        self.setFixedSize(w, h)

    def set_image(self, image: np.ndarray):
        if image is None:
            return
        if len(image.shape) > 2:
            height, width, channel = image.shape
            self.qImg = QImage(image.data, width, height, channel * width, QImage.Format.Format_BGR888)
        else:
            height, width = image.shape
            self.qImg = QImage(image.data, width, height, width, QImage.Format.Format_Grayscale8)

        self.label.setPixmap(QPixmap.fromImage(self.qImg))
        self.__update_size()
        self.repaint()

    def mousePressEvent_wrapper(self, event):
        if not self.mouse_press_handler is None:
            self.mouse_press_handler(event)
        # return super().mousePressEvent(event)

    def mouseReleaseEvent_wrapper(self, event):
        if not self.mouse_release_handler is None:
            self.mouse_release_handler(event)
        # return super().mouseReleaseEvent(event)

    def mouseMoveEvent_wrapper(self, event: QMouseEvent) -> None:
        x, y = event.position().toTuple()
        if not self.mouse_move_handler is None:
            self.mouse_move_handler(x, y)
        # return super().mouseMoveEvent(event)


######################################################################################################################################
######################################################################################################################################
class WinManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.windows: dict[str, QWidget] = {}

    def set_mouse_move_handler(self, winName: str, handler: typing.Callable[[int, int], None]) -> None:
        if winName in self.windows:
            self.windows[winName].mouse_move_handler = handler

    def set_mouse_press_handler(self, winName: str, handler: typing.Callable[[QMouseEvent], None]) -> None:
        if winName in self.windows:
            self.windows[winName].mouse_press_handler = handler

    def set_mouse_release_handler(self, winName: str, handler: typing.Callable[[QMouseEvent], None]) -> None:
        if winName in self.windows:
            self.windows[winName].mouse_release_handler = handler

    @PySide6.QtCore.Slot(str, name='asdasd')
    def show_image(self, winName: str, image: np.ndarray):
        if not winName in self.windows:
            w = ImageViewer(winName, image)
            self.windows[winName] = w
        else:
            w = self.windows[winName]
            w.set_image(image)
        if not image is None and not w.isVisible():
            w.show()
        #print("requested " + winName)

    PySide6.QtCore.Slot(object, name='invoke')

    def invoke(self, func: object):
        self.it = func()

######################################################################################################################################
######################################################################################################################################


class WinManagerInterface(QObject):
    ShowImageSignal = Signal(str, np.ndarray)
    InvokeSignal = Signal(object)

    def __init__(self) -> None:
        super().__init__()

    def invoke(self, callable: typing.Callable):
        self.InvokeSignal.emit(callable)

    def show_image(self, winName: str, img: np.ndarray):
        self.ShowImageSignal.emit(winName, img)

    def run_test(self):
        count = 0
        while count < 100:
            sleep(5)
            img = np.zeros((500, 500, 3), dtype=np.uint8)
            show_image("win" + str(count), img)
            #print("win Increasing")
            count += 1
######################################################################################################################################
######################################################################################################################################


WINMAN: WinManager = None
CONTROLLER: WinManagerInterface = None
_started = False


def start_winmanager(a, b, c):
    global WINMAN, CONTROLLER
    WINMAN = WinManager()
    CONTROLLER = WinManagerInterface()
    CONTROLLER.ShowImageSignal.connect(WINMAN.show_image)
    CONTROLLER.InvokeSignal.connect(WINMAN.invoke)


def wait_winman():
    global _started
    if not _started:
        _started = True
        QDispatcher.enqueue_job(start_winmanager, [1, 2, 3])

    while not WINMAN or not CONTROLLER:
        sleep(0.05)


def show_image(winName: str, img: np.ndarray):
    wait_winman()
    CONTROLLER.show_image(winName, img)


def invoke(callable: typing.Callable):
    wait_winman()
    CONTROLLER.invoke(callable)


def create_window(winName: str):
    wait_winman()
    CONTROLLER.show_image(winName, None)


def set_mouse_move_handler(winName: str, handler: typing.Callable[[int, int], None]) -> None:
    wait_winman()
    WINMAN.set_mouse_move_handler(winName, handler)


def set_mouse_press_handler(winName: str, handler: typing.Callable[[QMouseEvent], None]) -> None:
    wait_winman()
    WINMAN.set_mouse_press_handler(winName, handler)


def set_mouse_release_handler(winName: str, handler: typing.Callable[[QMouseEvent], None]) -> None:
    wait_winman()
    WINMAN.set_mouse_release_handler(winName, handler)

import threading
if __name__ == "__main__":
    def test_call():
        print(f"Called from {threading.get_ident()}")

    test_call()
    invoke(test_call)

    # CONTROLLER.run_test()
    show_image("t1", np.zeros((100, 100, 3)))
    sleep(4)
    show_image("t1", np.zeros((200, 200, 3)))
    sleep(4)
    show_image("t2", np.zeros((100, 100, 3)))
    sleep(4)
    show_image("t2", np.zeros((200, 200, 3)))
