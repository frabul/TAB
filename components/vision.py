import numpy as np
import win32gui
import win32ui
import win32con
from threading import Thread, Lock 
import pytesseract 

#pytesseract.pytesseract.tesseract_cmd = 'D:\\Tools\\Tesseract\\tesseract.exe' 

class Vision:
    # threading properties
    stopped = True
    lock = None
    screenshot = None
    # properties
    w = 0
    h = 0
    hwnd = None
    

    # constructor
    def __init__(self, window_name=None, padding = (0,0,0,0)):
        '''
            padding: (left,top,right,bottom)
        '''
        # create a thread lock object
        self.padding = padding
        self.window_name = window_name 
        self.lock = Lock()
        self._update_window_info()
        self.last_report = 0

    def _update_window_info(self):
        # find the handle for the window we want to capture.
        # if no window name is given, capture the entire screen
        if self.window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, self.window_name)

        if not self.hwnd:
            #print(f'Window {self.window_name} not found')
            return

        # get the window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0] 
        self.h = window_rect[3] - window_rect[1]  
        # account for the window border and titlebar and cut them off
        self.w = self.w - self.padding[0] - self.padding[2]
        self.h = self.h - self.padding[1] - self.padding[3]
        
        if self.h < 0: self.h = 0
        if self.w < 0: self.w = 0
 

        # set the cropped coordinates offset so we can translate screenshot
        # images into actual screen positions
        self.offset_x = window_rect[0] + self.padding[0]
        self.offset_y = window_rect[1] + self.padding[1]

    def get_screenshot(self) -> np.ndarray:
        self._update_window_info()
        if self.hwnd is None:
            return
        if not win32gui.IsWindowVisible(self.hwnd) or self.w < 1 or self.h < 1:
            import time 
            if time.time() > self.last_report + 2:
                print('not visible')
                self.last_report = time.time()
            return None
        # get the window image data
        try: 
            wDC = win32gui.GetWindowDC(self.hwnd) 
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.padding[0], self.padding[1]), win32con.SRCCOPY)

            # convert the raw data into a format opencv can read
            #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.fromstring(signedIntsArray, dtype='uint8')
            img.shape = (self.h, self.w, 4)

        

            # drop the alpha channel, or cv.matchTemplate() will throw an error like:
            #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type()
            #   && _img.dims() <= 2 in function 'cv::matchTemplate'
            img = img[..., :3]

            # make image C_CONTIGUOUS to avoid errors that look like:
            #   File ... in draw_rectangles
            #   TypeError: an integer is required (got type tuple)
            # see the discussion here:
            # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
            img = np.ascontiguousarray(img)
            return img
        except Exception as ex:
            print("Exception in get_screenshot "+ str(ex))
            pass
        finally:
            # free resources
            if cDC:
                cDC.DeleteDC()
            if dcObj:
                dcObj.DeleteDC()
            if wDC:    
                win32gui.ReleaseDC(self.hwnd, wDC)
            if dataBitMap:   
                try:
                    win32gui.DeleteObject(dataBitMap.GetHandle())
                except:
                    pass
        return None

    # find the name of the window you're interested in.
    # once you have it, update window_capture()
    # https://stackoverflow.com/questions/55547940/how-to-get-a-list-of-the-name-of-every-open-window
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler, None)

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the __init__ constructor.
    def get_screen_position_px(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    def get_screen_position_su(self, pos_su: tuple):
        x = pos_su[0] * self.w
        y = pos_su[1] * self.h
        return (x + self.offset_x, y + self.offset_y)

    @staticmethod
    def saturate(val, min, max):
        if val > max:
            return max
        if val < min:
            return min
        return val
    
    def get_section_2p_su(self, top_left, bot_right) -> (np.ndarray or None):
        x, y = top_left
        w = bot_right[0] - x
        h = bot_right[1] - y
        return self.get_section_su((x, y, w, h))

    def get_section_su(self, rectangle) -> (np.ndarray or None):
        ''' rectangele defined by (x,y,w,h) '''
        if self.screenshot is None:
            return None

        def sat(v):
            return Vision.saturate(v, 0, 1)
        x, y, w, h = rectangle
        x = int(sat(x) * self.w)
        y = int(sat(y) * self.h)
        w = int(sat(w) * self.w)
        h = int(sat(h) * self.h)
        self.lock.acquire()
        res = self.screenshot[y: y + h, x: x + w, :].copy()
        self.lock.release()
        return res

 
    def point_px_to_su(self, point) -> tuple:
        return (point[0] / self.w, point[1] / self.h)
        
    def point_su_to_px(self, prop) -> tuple:  
        return (int(prop[0] * self.w), int(prop[1] * self.h))

    def get_last_screen(self) -> (np.ndarray or None):
        self.lock.acquire()
        res = self.screenshot.copy()
        self.lock.release()
        return res
 
    def is_ready(self) -> bool:
        return not self.screenshot is None
    # threading methods

    def start(self):
        self.stopped = False
        t = Thread(target=self._worker_method, daemon=True)
        t.daemon = True
        t.start()

    def stop(self):
        self.stopped = True

    def _worker_method(self):
        # TODO: you can write your own time/iterations calculation to determine how fast this is
        while not self.stopped:
            # get an updated image of the game
            screenshot = self.get_screenshot()
            # lock the thread while updating the results
            if not screenshot is None:
                self.lock.acquire()
                self.screenshot = screenshot
                self.lock.release()

   

    


