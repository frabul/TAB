import numpy as np
import cv2
import QImageViewer
from vision import Vision
import math
from PySide6.QtCore import QRectF


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

    def match_exact(self, vision: Vision) -> bool:
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
            positives = [1 for s in scores if (1 - s) > self.score_min]
            return len(positives) == len(matches)
        else:
            match = cv2.matchTemplate(img, self.img, cv2.TM_SQDIFF_NORMED)
            return 1 - cv2.minMaxLoc(match)[1] > self.score_min

    def find_max(self, vision: Vision, topleft, botright):
        img = vision.get_section(topleft, botright).copy()
        img = self.prepare(img)
        QImageViewer.show_image('screen', img)
        QImageViewer.show_image('template', self.img)
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
            offset = vision.proportional_to_absolute(topleft)
            maxLoc = (maxLoc[0] + offset[0], maxLoc[1] + offset[1])
            maxLoc = vision.point_to_proportional(maxLoc)
            if maxVal > self.score_min:
                return (maxVal, maxLoc)
            else:
                return None
        else:
            raise Exception('Not implemented')

    def find_all(self, vision: Vision, topleft, botright) -> list[QRectF]:
        ''' search for matches '''
        img = vision.get_section(topleft, botright).copy()
        img = self.prepare(img)
        # QImageViewer.show_image('screen',img)
        # QImageViewer.show_image('template',self.img)
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

            hits = np.where(truth_table)
            infos = []

            coordinates = list(zip(hits[0], hits[1]))
            for hit in coordinates:
                infos.append(info(hit[0], hit[1], score[hit[0]][hit[1]]))

            # scrematura doppioni
            templateSize = vision.proportional_to_absolute(self.rect[2:4])
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
            for el in results:
                offset = vision.proportional_to_absolute(topleft)
                el.x += offset[0]
                el.y += offset[1]
                x, y = vision.point_to_proportional((el.x, el.y))
                rectangles.append(QRectF(x, y, self.rect[2], self.rect[3]))
            return rectangles