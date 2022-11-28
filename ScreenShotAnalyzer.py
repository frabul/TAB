from PySide6.QtCore import QObject, QRect, Qt, QThread, Signal, QTimer, QPointF
from PySide6.QtGui import (QPen, QAction, QBrush, QImage, QKeySequence, QMouseEvent, QShortcut, QClipboard,
                           QPixmap, QMouseEvent, QIcon)
from PySide6.QtWidgets import (QApplication, QGraphicsEllipseItem,
                               QGraphicsItem, QGraphicsRectItem,QGraphicsPixmapItem,
                               QGraphicsScene, QGraphicsSceneMouseEvent,
                               QGraphicsView, QLabel, QMainWindow, QWidget,
                               QGridLayout, QPushButton, QVBoxLayout, QSizePolicy, QLineEdit, QHBoxLayout
                               )
 


from vision import Vision    
import QDispatcher
import threading

import cv2

class ScreenShotAnalyzer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.last_screed_size = (0,0)
        self.last_pos = (0,0)
        self.last_pos_rel = (0,0)
        self.top_left = (0,0)
        self.bot_right = (0,0)

        self.vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
        self.vision.start()

        self.setWindowIcon(QIcon('./images/RemixIcon-ScreenshotLine.png'))
        self.setWindowTitle("Screenshot Analyzer")
        self.setGeometry(0, 0, 500, 800)

        self.selection_start : QPointF= None
        self.selection_end : QPointF= None  

        
        def screen_scene_handle_mouse_press( event: QGraphicsSceneMouseEvent):
            self.selection_start = event.scenePos()

        def screen_scene_handle_mouse_release( event: QGraphicsSceneMouseEvent):
            self.selection_end = event.scenePos()
            xmin = min(self.selection_start.x(), self.selection_end.x())
            xmax = max(self.selection_start.x(), self.selection_end.x())
            ymin = min(self.selection_start.y(), self.selection_end.y())
            ymax = max(self.selection_start.y(), self.selection_end.y())
            w = xmax - xmin
            h = ymax - ymin
            if w > 10 and h > 10:
                self.selection_rect.show()
                self.selection_rect.setRect(xmin,ymin,w,h)
                self.selection_rect.setPen(QPen(Qt.GlobalColor.red))

                sw =  self.screen_scene.width() 
                sh =  self.screen_scene.height() 
                self.top_left = ( round(xmin / sw,3), round(ymin / sh,3) )
                self.bot_right = ( round(xmax / sw,3), round(ymax / sh,3)  )


        self.screen_scene = QGraphicsScene() 
        self.screen_scene.mousePressEvent = screen_scene_handle_mouse_press
        self.screen_scene.mouseReleaseEvent = screen_scene_handle_mouse_release
        self.screen_scene.mouseMoveEvent = self.handle_label_mouse_move
 
   
        # scene image
        self.screen_item = QGraphicsPixmapItem()
        self.screen_scene.addItem(self.screen_item)

        # selection rect
        self.selection_rect = QGraphicsRectItem()
        self.selection_rect.hide()
        self.screen_scene.addItem(self.selection_rect)
        def selection_rect_mouseDoubleClickEvent(event):
            rect =   self.selection_rect.rect().toRect()
            section = self.last_screen_cv[ 
                rect.y() : rect.y() +rect.height(),
                rect.x() : rect.x() +rect.width(),
                :
            ].copy()
            cv2.imwrite('screen_selection.bmp',section)
            h, w, _ = section.shape
            QApplication.clipboard().setImage(
                QImage(section.data, w, h, 3 * w, QImage.Format.Format_BGR888))
            pass 
        self.selection_rect.mouseDoubleClickEvent = selection_rect_mouseDoubleClickEvent
        # view
        self.view = QGraphicsView(self.screen_scene, self)
        self.view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setContentsMargins(0,0,0,0)
        self.view.setGeometry(0, 0, self.screen_scene.width()  + 2 , self.screen_scene.height()  + 2 ) 
        self.view.setSceneRect(self.screen_scene.sceneRect()) 
        #self.view.setMouseTracking(True)
        self.view.setSizePolicy( QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed )
        #mainpanel.addWidget(self.view)
   
        # ---
        self.rightpanelwidget = QWidget(self)
        right_panel_layout = QVBoxLayout()
        self.rightpanelwidget.setLayout(right_panel_layout)

        self.label_position = QLabel()
        self.label_position.setText('position')
        self.label_position.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_position.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_position.to_clipboard)
        right_panel_layout.addWidget(self.label_position)

        self.label_position_rel = QLabel()
        self.label_position_rel.setText('pos rel')
        self.label_position_rel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_position_rel.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_position_rel.to_clipboard)
        right_panel_layout.addWidget(self.label_position_rel)

        self.label_rect = QLabel()
        self.label_rect.setText('rect ')
        self.label_rect.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_rect.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_rect.to_clipboard)
        right_panel_layout.addWidget(self.label_rect)

        self.label_rect_size = QLabel()
        self.label_rect_size.setText('rect size')
        self.label_rect_size.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label_rect_size.mouseDoubleClickEvent = \
            lambda ev: QApplication.clipboard().setText(self.label_rect_size.to_clipboard)
        right_panel_layout.addWidget(self.label_rect_size)
        # filler
        right_panel_layout.addWidget(QWidget())

        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.handle_timer_timeout)
        self.timer.start()
 
    def handle_label_mouse_move(self, event: QGraphicsSceneMouseEvent) -> None:
        x, y = event.scenePos().toTuple()
        x_rel = x / self.screen_scene.width() 
        y_rel = y / self.screen_scene.height() 
        self.last_pos = event.scenePos().toPoint().toTuple()
        self.last_pos_rel = (round(x_rel, 3), round(y_rel, 3))

    def handle_timer_timeout(self):
        if not self.vision.is_ready():
            return
        screen = self.vision.get_last_screen()
        h, w, _ = screen.shape
        #cv2.imwrite('screen.png',screen)
        self.last_screen_cv = screen
        self.last_screen = QImage(screen.data, w, h, 3 * w, QImage.Format.Format_BGR888)
        # self.label_screen.setGeometry(5,5,w,h)
        
        self.label_position.setText(f'Position: {self.last_pos}')
        self.label_position.to_clipboard = str( self.last_pos )

        self.label_position_rel.setText(f'Position Rel {self.last_pos_rel}')
        self.label_position_rel.to_clipboard = str( self.last_pos_rel )

        self.label_rect.setText(f'Rect: {self.top_left},{self.bot_right}')
        self.label_rect.to_clipboard = f'{self.top_left},{self.bot_right}'
        
        size = (self.bot_right[0] - self.top_left[0],self.bot_right[1] - self.top_left[1] )
        self.label_rect_size.setText(f'Rect Size: {size}')
        self.label_rect_size.to_clipboard = f'{size}'

        # self.label_screen.resize(self.last_screen.size())
        #self.last_screen.save('temp.png')
        self.screen_item.setPixmap(QPixmap.fromImage(self.last_screen))
        if self.last_screed_size != (w,h):
            self.last_screed_size = (w,h)
            self.screen_scene.setSceneRect(0,0,self.last_screen.width(), self.last_screen.height())
            self.view.setSceneRect(self.screen_scene.sceneRect())   
            self.view.resize(self.screen_scene.width()+ 3,self.screen_scene.height() + 3)
            self.rightpanelwidget.setGeometry(self.view.width() + 10, 0, 250, self.view.height())
            self.resize(w + 260, self.view.height())
  



QDispatcher.create(True)
print(f"ScreenShotAnalyzer running in thread #{threading.get_ident()}") 
win = ScreenShotAnalyzer( )
#win.setParent(QDispatcher.instance)
win.show() 
QDispatcher.exec()


 