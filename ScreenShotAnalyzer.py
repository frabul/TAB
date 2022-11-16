import keyboard
import os
import sys
import typing
from threading import Thread
from time import sleep
from types import MethodType
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal, QTimer
from PySide6.QtGui import (QAction, QBrush, QImage, QKeySequence, QMouseEvent, QShortcut, QClipboard,
                           QPixmap, QMouseEvent)
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget,
                               QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QLineEdit, QHBoxLayout
                               )

import farms_positions
import QImageViewer
from droid import Droid
from vision import Vision
from FarmsDb import Farm, FarmsDb


vision = Vision('BlueStacks App Player', 1, 34)


class ScreenShotAnalyzer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.last_pos = (0,0)
        self.last_pos_rel = (0,0)
        self.top_left = (0,0)
        self.bot_right = (0,0)

        self.vision = Vision('BlueStacks App Player', 1, 34)
        self.vision.start()

        self.setWindowTitle("Screenshot Analyzer")
        self.setGeometry(0, 0, 500, 800)

        mainframe = QWidget(self)
        self.setCentralWidget(mainframe)

        mainpanel = QHBoxLayout()
        mainframe.setLayout(mainpanel)

        self.label_screen = QLabel() 
        self.label_screen.mouseMoveEvent = self.handle_label_mouse_move
        self.label_screen.mousePressEvent = self.handle_label_mouse_press
        self.label_screen.mouseReleaseEvent = self.handle_label_mouse_release
        self.label_screen.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        mainpanel.addWidget(self.label_screen)

        sidpanel = QVBoxLayout()
        mainpanel.addLayout(sidpanel)

        self.label_position = QLabel()
        self.label_position.setText('position')
        self.label_position.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_position.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_position.to_clipboard)
        sidpanel.addWidget(self.label_position)

        self.label_position_rel = QLabel()
        self.label_position_rel.setText('pos rel')
        self.label_position_rel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_position_rel.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_position_rel.to_clipboard)
        sidpanel.addWidget(self.label_position_rel)

        self.label_rect = QLabel()
        self.label_rect.setText('rect ')
        self.label_rect.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_rect.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_rect.to_clipboard)
        sidpanel.addWidget(self.label_rect)

        # filler
        sidpanel.addWidget(QWidget())

        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.handle_timer_timeout)
        self.timer.start()

       
    def handle_label_mouse_press(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint().toTuple()
        self.drag_init_pos = pos

    def handle_label_mouse_release(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint().toTuple()
        self.drag_end_pos = pos
        w =  self.label_screen.size().width()
        h =  self.label_screen.size().height()
        self.top_left = (
            round(min( self.drag_init_pos[0], self.drag_end_pos[0]) / w,3),
            round(min( self.drag_init_pos[1], self.drag_end_pos[1]) / h,3)
        )
        self.bot_right = (
            round(max( self.drag_init_pos[0], self.drag_end_pos[0]) / w,3),
            round(max( self.drag_init_pos[1], self.drag_end_pos[1]) / h,3)
        )

    def handle_label_mouse_move(self, event: QMouseEvent) -> None:
        x, y = event.position().toTuple()
        x_rel = x / self.label_screen.size().width()
        y_rel = y / self.label_screen.size().height()
        self.last_pos = event.position().toPoint().toTuple()
        self.last_pos_rel = (round(x_rel, 3), round(y_rel, 3))

    def handle_timer_timeout(self):
        if not self.vision.is_ready():
            return
        screen = self.vision.get_last()
        h, w, _ = screen.shape
        self.last_screen = QImage(screen.data, w, h, 3 * w, QImage.Format.Format_BGR888)
        # self.label_screen.setGeometry(5,5,w,h)
        
        self.label_position.setText(f'Position: {self.last_pos}')
        self.label_position.to_clipboard = str( self.last_pos )

        self.label_position_rel.setText(f'Position Rel {self.last_pos_rel}')
        self.label_position_rel.to_clipboard = str( self.last_pos_rel )

        self.label_rect.setText(f'Rect: {self.top_left},{self.bot_right}')
        self.label_rect.to_clipboard = f'{self.top_left},{self.bot_right}'
        
        self.label_screen.resize(self.last_screen.size())
        self.label_screen.setPixmap(QPixmap.fromImageInPlace(self.last_screen))
        self.resize(w + 250, h)

        # self.repaint()


def main():
    win = ScreenShotAnalyzer()
    win.show()
    return win


QImageViewer.invoke(main)
while True:
    if keyboard.is_pressed('ctrl+q'):
        os._exit(0)
