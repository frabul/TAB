import sys

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget,QVBoxLayout,QPushButton  
import PySide6
import PySide6.QtCore
class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("My App")

        layout = QVBoxLayout()

        button = QPushButton('fw') 
        layout.addWidget(button)
        layout.addWidget(QPushButton('gmktyuk ukyku kyu'))
        layout.addWidget(QPushButton('asdasdd')) 
        layout.addWidget(QWidget())
        
        widget = QWidget(self)
        
       
        widget.setLayout(layout)
        #widget.setGeometry(5,5,100,100)
        self.setCentralWidget(widget)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()