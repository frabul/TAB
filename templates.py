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
        self.magniglass = Template('magniglass', (0.02, 0.63), (0.1, 0.68), score_min=0.7)  
        def prepareMagni(img: np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
            return img[1]
        self.magniglass.prepare = prepareMagni 
        
        # nest_l16
        def prepareNest(img: np.ndarray): 
            hsv_max = np.array([14, 178, 225])
            hsv_min = np.array([0, 127, 54]) 
            return utils.apply_hsv_mask(img, hsv_min, hsv_max) 
        self.nest_l16 = Template('nest_l16', (0.34, 0.59), (0.49, 0.68))
        self.nest_l16.prepare = prepareNest 
        
        # location_marker
        def prepare_location_marker(img): 
            #hsv_max = np.array([83, 145, 129])
            #hsv_min = np.array([69, 74, 58]) 
            hsv_max = np.array([83, 146, 129])
            hsv_min = np.array([59, 54, 51])
            return utils.apply_hsv_mask(img, hsv_min, hsv_max) 
        self.location_marker = Template('location_marker',(0.285, 0.599), (0.285, 0.599),score_min=0.95)
        self.location_marker.prepare = prepare_location_marker
 
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
        rectangles = templates.nest_l16.find_all(vision, (0.17, 0.45), (0.76, 0.83) )
        for rect in rectangles:
            print(f"found {rect.x()} {rect.y()} {rect.width()} {rect.height()} ")
        time.sleep(1)
    os._exit(0)

