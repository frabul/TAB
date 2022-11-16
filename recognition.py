import numpy as np
import win32gui
import win32ui
import win32con
from threading import Thread, Lock
import cv2
import easyocr
import QImageViewer
import pytesseract
import re
from vision import Vision
pytesseract.pytesseract.tesseract_cmd = 'D:\\Tools\\Tesseract\\tesseract.exe'


class Template:
    img: np.ndarray = None
    top_left = 0
    bot_right = 0
    rect = (0, 0, 0, 0)

    def __init__(self, name: str, topleft, botright) -> None:
        self.name: str = name
        x, y = topleft
        w = botright[0] - x
        h = botright[1] - y
        self.top_left = topleft
        self.bot_right = botright
        self.rect = (x, y, w, h)

    def save(self, vision: Vision):
        img = vision.get_rectangle_proportional(self.rect).copy()
        self.screen_size = (vision.w, vision.h)
        cv2.imwrite(f'./images/{self.name}.bmp', img)
        img = self.prepare(img)
        self.img = img

    def load(self):
        img = cv2.imread(f'./images/{self.name}.bmp')
        self.img = self.prepare(img)
        pass

    def prepare(self, img):
        return img

    def match_exact(self, vision: Vision, threshold=0.95) -> bool:
        ''' cuts a rectangle at the recorded position and matches on same size'''
        img = vision.get_rectangle_proportional(self.rect).copy()
        img = self.prepare(img)
        img = cv2.resize(img, (self.img.shape[1], self.img.shape[0])).copy()

        if len(img.shape) > 2:
            matches = [
                cv2.matchTemplate(img[:, :, 0], self.img[:, :, 0], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 1], self.img[:, :, 1], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 2], self.img[:, :, 2], cv2.TM_SQDIFF_NORMED)
            ]
            scores = [cv2.minMaxLoc(match)[1] for match in matches]
            positives = [1 for s in scores if (1 - s) > threshold]
            return len(positives) == len(matches)
        else:
            match = cv2.matchTemplate(img, self.img, cv2.TM_SQDIFF_NORMED)
            return 1 - cv2.minMaxLoc(match)[1] > threshold

    def match_search(self, topleft, botright, threshold):
        ''' search for matches '''
        img = vision.get_section(topleft, botright).copy()

        img = self.prepare(img)
        # todo resize
        if len(img.shape) > 2:
            matches = [
                cv2.matchTemplate(img[:, :, 0], self.img[:, :, 0], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 1], self.img[:, :, 1], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 2], self.img[:, :, 2], cv2.TM_SQDIFF_NORMED)
            ]

            score = (3 - (matches[0] + matches[1] + matches[2])) / 3
            print("found " + str(cv2.minMaxLoc(score)))

            booleanized = [(1 - m) > threshold for m in matches]
            truth_table = np.logical_and(booleanized[0], booleanized[1])
            truth_table = np.logical_and(truth_table, booleanized[2])

            hits = np.where(truth_table)

            #oktiles = []
            # for x in range(matches[0].shape[1]):
            #    for y in range(matches[1].shape[0]):
            #        scores = [s[y][x] for s in matches]
            #        found = all((1-s) > threshold  for s in scores )
            #        if(found):
            #            oktiles.append((x,y))

            return list(zip(hits[0], hits[1]))


class Templates:
    def __init__(self) -> None:
        self.items = {}
        # magniglass
        self.magniglass = Template('magniglass', (0.02, 0.63), (0.1, 0.68))

        def prepareMagni(img: np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
            return img[1]
        self.magniglass.prepare = prepareMagni
        self.items['magniglass'] = self.magniglass

        # nest_l16
        self.nest_l16 = Template('nest_l16', (0.34, 0.59), (0.49, 0.68))
        self.items['nest_l16'] = self.nest_l16


class Recognition:
    def __init__(self, vision: Vision):
        self.vision = vision
        self.templates = Templates()

    def is_outside(self) -> bool:
        tm = self.templates.magniglass
        return tm.match_exact(self.vision, 0.7)

    read_world_position_lower_val = [88, 90, 120]
    read_world_position_upper_val = [105, 160, 200]

    def read_world_position(self) -> tuple[int]:
        img = vision.get_section((0.38, 0.79), (0.60, 0.82)).copy()
        #cv2.imwrite('temp.bmp', img)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # set lower and upper color limits
        lower_val = np.array(self.read_world_position_lower_val)
        upper_val = np.array(self.read_world_position_upper_val)
        mask = cv2.inRange(hsv, lower_val, upper_val)
        # apply mask to original image
        only_txt = cv2.bitwise_and(img, img, mask=mask)
        #_, img = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
        #QImageViewer.show_image('imgpos', only_txt)
        txt = pytesseract.image_to_string(only_txt)
        rematch = re.match("X[:](\d+) [Y¥][:.-](\d+).*", txt)
        if rematch:
            return (int(rematch.group(1)), int(rematch.group(2)))
        return None

    def get_troops_deployed(self):
        img = vision.get_section((.005, .200), (.06, .235)).copy()
        #img = vision.get_section((.02, .47), (.06, .5)).copy()
        cv2.imwrite('temp.bmp',img) 
        QImageViewer.show_image('img', img)

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 
        # set lower and upper color limits
        lower_val = np.array([13,80,140])
        upper_val = np.array([20,120,220])
        mask = cv2.inRange(hsv, lower_val, upper_val)
        print("avg " + str(np.average(mask)))

        return np.average(mask) > 115


if __name__ == '__main__':
    import time
    import keyboard
    import os

    vision = Vision('BlueStacks App Player', 1, 34)
    vision.start()
    while not vision.is_ready():
        time.sleep(0.1)
    rec = Recognition(vision)
    # rec.templates.magniglass.save(vision)
    rec.templates.magniglass.load()
    # rec.templates.nest_l16.save(vision)
    rec.templates.nest_l16.load()

    while not keyboard.is_pressed('ctrl+q'):
        #hits = rec.templates.nest_l16.match_search((0.17, 0.45), (0.76, 0.83), 0.85)
        #print(f'{len(hits)} hits')

        # if rec.is_outside():
        #    print('outside')
        # else:
        #    print('inside')

        # test read_world_position
        #pos = rec.read_world_position()
        #print(f'Pos read: {pos}')

        print(rec.get_troops_deployed())
        time.sleep(1)
    os._exit(0)
