import numpy as np
import cv2
import pytesseract
import re
from vision import Vision
import QImageViewer
from template import Template
from templates import Templates

pytesseract.pytesseract.tesseract_cmd = 'D:\\Tools\\Tesseract\\tesseract.exe'



class Recognition:
    def __init__(self, vision: Vision):
        self.vision = vision
        self.templates = Templates()

    def is_outside(self) -> bool:
        tm = self.templates.magniglass
        return tm.match_exact(self.vision)

    read_world_position_lower_val = [88, 90, 120]
    read_world_position_upper_val = [105, 160, 200]

    def read_world_position(self) -> tuple[int]:
        img = self.vision.get_section((0.38, 0.79), (0.60, 0.82)).copy()
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

    def get_troops_deployed_count(self):
        ''' needs to be outside '''
        liclover = [
            (0.006, 0.2, 0.052, 0.035),
            (0.006, 0.257, 0.052, 0.035),
            (0.006, 0.317, 0.052, 0.035),
            (0.006, 0.374, 0.052, 0.035)]
        count = 0
        for i, pos in enumerate(liclover):
            img = self.vision.get_rectangle_proportional(pos).copy()
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # set lower and upper color limits
            lower_val = np.array([13, 80, 140])
            upper_val = np.array([20, 120, 220])
            mask = cv2.inRange(hsv, lower_val, upper_val)
            print("avg " + str(np.average(mask)))
            found = np.average(mask) > 95 and np.average(mask) < 125
            if found:
                count += 1
            else:
                break
        return count

    def is_exit_game_gump(self):
        img = self.vision.get_section((0.37, 0.459), (0.559, 0.495))
        txt: str = pytesseract.image_to_string(img)
        if txt and "Exit Game" in txt:
            return True
        return False

    def is_troop_selection_gump(self):
        img = self.vision.get_section((0.348, 0.017), (0.627, 0.048))
        txt: str = pytesseract.image_to_string(img)
        if txt and "March Troops" in txt:
            return True
        return False

    def is_attack_gump(self):
        img = self.vision.get_section((0.423, 0.652), (0.521, 0.677))
        txt: str = pytesseract.image_to_string(img)
        if txt and "Attack" in txt:
            return True
        return False

    def read_location_info(self):
        ''' returns (name, alliance, location)'''
        res = self.templates.location_marker.find_max(self.vision,(0.004, 0.079), (0.949, 0.754) )
        name = None
        location = None
        alliance = None
        if res:
            maxVal, maxLoc = res
            nameRect = (maxLoc[0] - 0.015, maxLoc[1] - .126, 0.364, 0.052)
            locRect = (maxLoc[0] + .028, maxLoc[1], 0.195, 0.024)  

            nameImg = self.vision.get_rectangle_proportional(nameRect).copy()
            txt :str = pytesseract.image_to_string(nameImg)
            if len(txt)>0:
                name = txt.splitlines()[0]
                rematch = re.match("[(]([A-Za-z0-9]+)[)](.+)", name)
                if rematch:
                    name = rematch.group(2)
                    alliance = rematch.group(1) 

            
            locImg = self.vision.get_rectangle_proportional(locRect).copy()
            locStr = pytesseract.image_to_string(locImg)
            rematch = re.match("X[:]([\d,]+)[\s ,]+[Y¥][:.-]([\d,]+).*", locStr)
            location = None
            QImageViewer.show_image('nameImg',nameImg)
            QImageViewer.show_image('locImg',locImg) 
            if rematch:
                location = (int(rematch.group(1).replace(',','')), int(rematch.group(2).replace(',',''))) 

        return (name, alliance, location)


    def is_inside(self):
        return False


if __name__ == '__main__':
    import time
    import keyboard
    import os

    vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
    vision.start()
    while not vision.is_ready():
        time.sleep(0.1)
    rec = Recognition(vision)
    # rec.templates.magniglass.save(vision) 
    # rec.templates.nest_l16.save(vision) 

    while not keyboard.is_pressed('ctrl+q'):
        #hits = rec.templates.nest_l16.match_search(vision, (0.17, 0.45), (0.76, 0.83), 0.85)
        #print(f'{len(hits)} hits')

        # if rec.is_outside():
        #    print('outside')
        # else:
        #    print('inside')

        # test read_world_position
        #pos = rec.read_world_position()
        #print(f'Pos read: {pos}')

        # test get_troops_deployed_count
        # print(rec.get_troops_deployed_count())
        #print(f"is attack = {rec.is_attack_gump()}")

        print(rec.read_location_info())
        time.sleep(1)
    os._exit(0)
