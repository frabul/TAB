import numpy as np
import cv2
import QImageViewer
from vision import Vision
import math
from PySide6.QtCore import QRectF
import utils

class info:
    def __init__(self, x, y, score):
        self.x = x
        self.y = y
        self.score = score

    def __str__(self):
        return f"{{{self.x}, {self.y}, {self.score} }}"

class Template:
    img: np.ndarray = None
    top_left = 0
    bot_right = 0
    rect = (0, 0, 0, 0)

    def __init__(self, name: str, topleft, botright, score_min=0.85) -> None:
        self.name: str = name
        self.score_min = score_min
        x, y = topleft
        w = botright[0] - x
        h = botright[1] - y
        self.top_left = topleft
        self.bot_right = botright
        self.rect = (x, y, w, h)
         
    def save(self, vision: Vision):
        img = vision.get_section_su(self.rect).copy()
        self.screen_size = (vision.w, vision.h)
        cv2.imwrite(f'./images/{self.name}.bmp', img)
        img = self.prepare(img)
        self.img = img

    def load(self):
        img = cv2.imread(f'./images/{self.name}.bmp')
        self.img = self.prepare(img)
        self.size_px = (img.shape[1], img.shape[0])
        pass

    def prepare(self, img):
        return img
         
    def match_exact(self, vision: Vision) -> bool:
        ''' cuts a rectangle at the recorded position and matches on same size'''
        img = vision.get_section_su(self.rect).copy()
        img = self.prepare(img)
        img = cv2.resize(img, (self.img.shape[1], self.img.shape[0])).copy()

        if len(img.shape) > 2:
            matches = [
                cv2.matchTemplate(img[:, :, 0], self.img[:, :, 0], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 1], self.img[:, :, 1], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 2], self.img[:, :, 2], cv2.TM_SQDIFF_NORMED)
            ]
            scores = [cv2.minMaxLoc(match)[1] for match in matches]
            positives = [1 for s in scores if (1 - s) > self.score_min]
            return len(positives) == len(matches)
        else:
            match = cv2.matchTemplate(img, self.img, cv2.TM_SQDIFF_NORMED)
            return 1 - cv2.minMaxLoc(match)[1] > self.score_min

    def find_max(self, vision: Vision, topleft, botright):
        img = vision.get_section_2p_su(topleft, botright).copy()
        img = self.prepare(img)
        #QImageViewer.show_image('screen', img)
        #QImageViewer.show_image('template', self.img)
        # todo resize
        if len(img.shape) > 2:
            matches = [
                cv2.matchTemplate(img[:, :, 0], self.img[:, :, 0], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 1], self.img[:, :, 1], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 2], self.img[:, :, 2], cv2.TM_SQDIFF_NORMED)
            ]

            score = (3 - (matches[0] + matches[1] + matches[2])) / 3
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(score)
            # retransform coordinates
            offset = vision.point_su_to_px(topleft)
            maxLoc = (maxLoc[0] + offset[0], maxLoc[1] + offset[1])
            maxLoc = vision.point_px_to_su(maxLoc)
            if maxVal > self.score_min:
                return (maxVal, maxLoc)
            else:
                return None
        else:
            raise Exception('Not implemented')

    def find_all(self, vision: Vision, topleft, botright) -> list[QRectF]:
        ''' search for matches '''
        self.w_px = self.img.shape[1]
        self.h_px = self.img.shape[0]

        img = vision.get_section_2p_su(topleft, botright) 
        #QImageViewer.show_image('screen',img)
        img = self.prepare(img)
        #QImageViewer.show_image('template',self.img)
        # todo resize
        if len(img.shape) > 2:
            matches = [
                cv2.matchTemplate(img[:, :, 0], self.img[:, :, 0], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 1], self.img[:, :, 1], cv2.TM_SQDIFF_NORMED),
                cv2.matchTemplate(img[:, :, 2], self.img[:, :, 2], cv2.TM_SQDIFF_NORMED)
            ]

            score = (3 - (matches[0] + matches[1] + matches[2])) / 3
            #print("max score at " + str(cv2.minMaxLoc(score)))

            booleanized = [(1 - m) > self.score_min for m in matches]
            truth_table = np.logical_and(booleanized[0], booleanized[1])
            truth_table = np.logical_and(truth_table, booleanized[2])
        else:
            mat = cv2.matchTemplate(img , self.img , cv2.TM_SQDIFF_NORMED)
            score = mat
            truth_table = (1 - mat) > self.score_min 

        hits = np.where(truth_table)
        infos = []

        coordinates = list(zip(hits[0], hits[1]))
        for hit in coordinates:
            infos.append(info(x=hit[1], y=hit[0], score=score[hit[0]][hit[1]]))

        # scrematura doppioni
        templateSize = vision.point_su_to_px(self.rect[2:4])
        minDist = math.sqrt(templateSize[0]**2 + templateSize[1]**2)

        def distance(a: info, b: info):
            return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

        groups: list[list[info]] = []
        for to_add in infos:
            added = False
            for group in groups:
                if not added:
                    for elem in group:
                        if distance(to_add, elem) < minDist:
                            group.append(to_add)
                            added = True
                            break
            if not added:
                groups.append([to_add, ])

        # search max for each group
        results: list[info] = []
        for group in groups:
            maxElem = None
            for el in group:
                if maxElem is None or maxElem.score < el.score:
                    maxElem = el
            if not maxElem is None:
                results.append(maxElem)

        # trasformiamo le coordinate in coordinate generali
        rectangles = []

        #rectOnsection = img.copy()
        for el in results:  
            a = vision.point_px_to_su((el.x, el.y)) 
            x,y = utils.point_sum(a, topleft) 
            w, h = vision.point_px_to_su((self.w_px, self.h_px))
            rectangles.append(QRectF(x, y, w, h))

        #QImageViewer.show_image('rectOnsection', rectOnsection)
        return rectangles
