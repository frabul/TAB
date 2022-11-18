from types import MethodType
import numpy as np
from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal, QTimer
from PySide6.QtGui import (QAction, QBrush, QImage, QKeySequence, QMouseEvent, QShortcut, QClipboard,
                           QPixmap, QDropEvent)
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget,
                               QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QLineEdit, QHBoxLayout,
                               QSlider
                               )
from vision import Vision
import cv2
import QDispatcher
class HSV_RangeFinder(QMainWindow):
    image_original : np.ndarray = None
    def __init__(self) -> None:
        super().__init__()
        self.setGeometry(100,100,600,400)
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        self.central_layout = QHBoxLayout(centralWidget)
        centralWidget.setLayout(self.central_layout)

        self.slider_h_min = self.get_slider(0) 
        self.slider_h_max = self.get_slider(255) 

        self.slider_s_min = self.get_slider(0) 
        self.slider_s_max = self.get_slider(255) 

        self.slider_v_min = self.get_slider(0) 
        self.slider_v_max = self.get_slider(255) 
 

        self.label_img = QLabel()
        self.central_layout.addWidget(self.label_img)
        self.setAcceptDrops(True)

        self.action_paste = QShortcut(QKeySequence("Ctrl+V"), self)
        self.action_paste.setEnabled(True)
        self.action_paste.activated.connect(self.get_image_from_clipboard)


    def get_image_from_clipboard(self):
        copied = QApplication.clipboard().image()
        copied = copied.convertToFormat(QImage.Format.Format_BGR888) 
        width = copied.width()
        height = copied.height()
        if width > 0 and height>0:
            ptr = copied.bits()
            #ptr.setsize(copied.byteCount())
            #img = np.zeros((copied.height(),copied.width(),3), dtype=np.uint8)
            self.image_original = np.array(ptr).reshape(height, -1, 4)  #  Copies the data
            self.update_image()


    def get_slider(self, val):
        sli = QSlider()
        sli.setMaximum(255)   
        sli.setMinimum(0)
        sli.setTickInterval(1) 
        sli.setValue(val)
        sli.valueChanged.connect(self.update_image)
        self.central_layout.addWidget(sli)
        return sli

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            url = mimeData.urls().pop() 
            if url.isLocalFile():
                self.image_original = cv2.imread(url.toLocalFile()) 
                self.update_image()
        return super().dropEvent(event)

    def update_image(self):
        if   self.image_original is None:
            return 
        ksize = (8, 8)    
        hsv = cv2.blur(self.image_original, ksize)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        # set lower and upper color limits
        upper_val = np.array([
                self.slider_h_max.value(),
                self.slider_s_max.value(),
                self.slider_v_max.value()
            ])
        lower_val = np.array([
                self.slider_h_min.value(),
                self.slider_s_min.value(),
                self.slider_v_min.value()
            ])
        mask = cv2.inRange(hsv, lower_val, upper_val)
        # apply mask to original image
        self.img_masked : np.ndarray= cv2.bitwise_and(self.image_original, self.image_original, mask=mask)
        image = self.img_masked
        height ,width,channel = image.shape
        self.qimg = QImage(image.data, width, height, channel * width, QImage.Format.Format_BGR888)
        self.label_img.setPixmap(QPixmap.fromImageInPlace(self.qimg))

QDispatcher.create(True) 
win = HSV_RangeFinder( )
#win.setParent(QDispatcher.instance)
win.show() 
QDispatcher.exec()

