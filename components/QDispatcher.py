from PySide6.QtCore import Qt, QThread, QObject, Signal,QTimer
from PySide6.QtGui import QPixmap, QImage, QMouseEvent
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QWidget 
from threading import Thread, Lock
from queue import Queue,Empty
import typing
import time 
import threading


class QDispatcher(QApplication):
    instance :'QDispatcher'= None
    gui_thread : Thread = None
    InvokeSignal = Signal(object)

    def __init__(self):
        super().__init__()
        self.windows : list[QWidget] = []
        self.timer = QTimer(self)   
        self.timer.start(100)
        self.timer.timeout.connect(self.handle_timer)
        self.jobs = Queue(100)
        self.InvokeSignal.connect(self.handle_invoke)

    def handle_invoke(self, fu):
        retval = fu()
        if type(retval) is QWidget:
            self.windows.append(retval)

    def handle_timer(self):
        try:
            while True:
                job = self.jobs.get(False)
                job[0](*job[1])
                self.jobs.task_done()   
        except Empty as emptyEx:
            pass
        except Exception as ex:
            print("error in dispatched func " + str(ex))
            pass
        pass

    def enqueue_job(self, job, args=[]):
        self.jobs.put((job, args ),False)

    def invoke(self, callable: typing.Callable):
        self.InvokeSignal.emit(callable)

def create(setQuitOnLastWindowClosed=False):
    ''' Can be use to create and then exec QDispatcher in current thread '''
    #print(f"Dispatcher running in thread #{threading.get_ident()}")
    QDispatcher.instance = QDispatcher()
    QDispatcher.instance.setQuitOnLastWindowClosed(setQuitOnLastWindowClosed)

def exec():
    QDispatcher.instance.exec()

def _run():
    '''run dispatcher in current thread'''
    if not QDispatcher.instance: 
        create()
        QDispatcher.instance.exec()
    

def check_created(): 
    '''checks if dispatcher has been created otherwise creates it'''
    if not QDispatcher.instance: 
        QDispatcher.gui_thread = Thread(target=_run)
        QDispatcher.gui_thread.start() 
    while not QDispatcher.instance:
        time.sleep(0.05)

def exit(code = 0):
    if QDispatcher.instance:
        enqueue_job(QDispatcher.instance.exit,[code])
        

def enqueue_job(job : typing.Callable, args : list=[]):
    check_created()
    QDispatcher.instance.enqueue_job(job, args)    

def invoke(job: typing.Callable):
    check_created()
    QDispatcher.instance.invoke(job)