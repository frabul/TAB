import numpy as np
import cv2
import QImageViewer
from vision import Vision
from template import Template
import utils
hsv_min = np.array([83, 148, 132])
hsv_max = np.array([[69, 54, 54]])


class Templates:
    def __init__(self) -> None:
        self.items = {}

        # magniglass
        self.magniglass = Template('magniglass', (0.022, 0.63),(0.101, 0.677), score_min=0.7) 
        def prepareMagni(img: np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
            return img[1]
        self.magniglass.prepare = prepareMagni

        # define workers_icon
        self.workers_icon = Template('workers_icon', (0.027, 0.139),(0.099, 0.173), score_min=0.75) 
  

        # nest_l16
        def prepareNest(img: np.ndarray):
            hsv_max = np.array([14, 178, 225])
            hsv_min = np.array([0, 127, 54])
            return utils.apply_hsv_mask(img, hsv_min, hsv_max)
        self.nest_l16 = Template('nest_l16', (0.34, 0.59), (0.49, 0.68))
        self.nest_l16.prepare = prepareNest

        # nest_l16_mini
        def prepareNest(img: np.ndarray): 
            hsv_min = np.array([3, 113, 49])
            hsv_max = np.array([16, 201, 230])
            return utils.apply_hsv_mask(img, hsv_min, hsv_max, ksize=(3,3))
        self.nest_l16_mini = Template('nest_l16_mini', (0.546, 0.618), (0.644, 0.653)) #(0.453, 0.692),(0.556, 0.724)
        self.nest_l16_mini.prepare = prepareNest

        # nest_eggs_mini
        self.nest_eggs_mini = Template('nest_eggs_mini', (0.453, 0.68),(0.549, 0.7))

        # stamina_marker
        def prepare_stamina_marker(img: np.ndarray):
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.stamina_marker = Template('stamina_marker', (0.528, 0.609), (0.58, 0.635), score_min=0.95)
        self.stamina_marker.prepare = prepare_stamina_marker
 
        # location_marker
        def prepare_location_marker(img): 
            hsv_max = np.array([78, 171, 199])
            hsv_min = np.array([67, 54, 44]) 
            return utils.apply_hsv_mask(img, hsv_min, hsv_max, ksize=(2, 2))
        self.location_marker = Template('location_marker', (0.271, 0.526),(0.305, 0.552), score_min=0.85)
        self.location_marker.prepare = prepare_location_marker

        #app_icon
        self.app_icon = Template('app_icon', (0.704, 0.198),(0.8, 0.257), score_min=0.9)

        # load all
        for it in self.__dict__.values():
            if type(it) is Template:
                it.load()

    

if __name__ == '__main__':
    import time
    import keyboard
    import os
    vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
    vision.start()
    templates = Templates()
    while not keyboard.is_pressed('ctrl+q'):
        #maxVal, maxLoc = templates.location_marker.find_max(vision, (0.004, 0.079), (0.949, 0.754) )
        #print(f"found {maxVal} at {maxLoc}"  )
        rectangles = templates.nest_eggs_mini.find_all(vision, (0.002, 0.12),(0.919, 0.846))
        img = vision.get_last_screen()
        print(f"found {len(rectangles)} rectangeles")
        for rect in rectangles:
            print(f"    {rect.x()} {rect.y()} {rect.width()} {rect.height()} ")
            pos = vision.point_su_to_px((rect.x(), rect.y()))
            size = vision.point_su_to_px((rect.width(), rect.height()))
            img = cv2.rectangle(img, pos, (pos[0] + size[0], pos[1] + size[1]), (0, 0, 255))
        QImageViewer.show_image('foundings', img)
        time.sleep(1)
    os._exit(0)