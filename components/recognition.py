import numpy as np
import cv2
import pytesseract
import re
from .vision import Vision
from .template import Template
from .templates import Templates
from . import QImageViewer
from . import utils

#pytesseract.pytesseract.tesseract_cmd = 'e:\\Tools\\Tesseract\\tesseract.exe'
debug = False


def show_image(winname, img):
    if debug:
        QImageViewer.show_image(winname, img)


class Recognition:
    def __init__(self, vision: Vision):
        self.vision = vision
        self.templates = Templates()

    def is_outside(self) -> bool:
        tm = self.templates.magniglass
        return tm.match_exact(self.vision)

    def is_inside(self) -> bool:
        tm = self.templates.workers_icon
        return tm.match_exact(self.vision)

    def read_world_position(self) -> tuple[int]:
        img = self.vision.get_section_2p_su((0.38, 0.79), (0.60, 0.82))
        #cv2.imwrite('temp.bmp', img)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # set lower and upper color limits
        hsv_max = np.array([99, 149, 162])
        hsv_min = np.array([58, 82, 67])
        mask = cv2.inRange(hsv, hsv_min, hsv_max)
        # apply mask to original image
        only_txt = cv2.bitwise_and(img, img, mask=mask)
        #only_txt = cv2.cvtColor(only_txt, cv2.COLOR_BGR2GRAY)
        #only_txt = cv2.blur(only_txt,  (2,2) )
        #show_image('imgpos', only_txt)
        tesserconfig = '--psm 7 -c tessedit_char_whitelist=0123456789XY:'
        txt = pytesseract.image_to_string(only_txt, config=tesserconfig)
        rematch = re.match("X[:](\d+)\s?[Y¥][:.-](\d+).*", txt)
        if rematch is None:
            only_txt2 = cv2.erode(only_txt, np.ones((2, 1)))
            txt = pytesseract.image_to_string(only_txt2, config=tesserconfig)
            rematch = re.match("X[:](\d+) [Y¥][:.-](\d+).*", txt)

        if rematch is None:
            only_txt3 = cv2.erode(only_txt, np.ones((1, 2)))
            txt = pytesseract.image_to_string(only_txt3, config=tesserconfig)
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
            img = self.vision.get_section_su(pos)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # set lower and upper color limits
            lower_val = np.array([13, 80, 140])
            upper_val = np.array([20, 120, 220])
            mask = cv2.inRange(hsv, lower_val, upper_val)
            #print("avg " + str(np.average(mask)))
            found = np.average(mask) > 95 and np.average(mask) < 125
            if found:
                count += 1
            else:
                break
        return count

    def is_exit_game_gump(self) -> bool:
        img = self.vision.get_section_2p_su((0.37, 0.459), (0.559, 0.495))
        txt: str = pytesseract.image_to_string(img, config='--psm 7')
        if txt and "Exit Game" in txt:
            return True
        return False

    def is_troop_selection_gump(self) -> bool:
        img = self.vision.get_section_2p_su((0.348, 0.017), (0.627, 0.048))
        txt: str = pytesseract.image_to_string(img, config='--psm 7')
        if txt and "March Troops" in txt:
            return True
        return False

    def is_attack_gump(self) -> bool:
        img = self.vision.get_section_2p_su((0.423, 0.652), (0.521, 0.677))
        txt: str = pytesseract.image_to_string(img, config='--psm 7')
        if txt and "Attack" in txt:
            return True
        return False

    def is_lizard_rally_gump(self) -> bool:
        img = self.vision.get_section_2p_su((0.535, 0.216), (0.678, 0.256))
        txt: str = pytesseract.image_to_string(img, config='--psm 7')
        if txt and "Lizard" in txt:
            return True
        return False

    def read_nest_info(self):
        ''' returns (name, alliance, location) '''
        res = self.templates.location_marker.find_max(self.vision, (0.002, 0.193), (0.821, 0.844))
        name = None
        location = None
        alliance = None
        if res:
            maxVal, maxLoc = res
            nameRect1 = (maxLoc[0] - 0.015, maxLoc[1] - .105, 0.364, 0.027)  # no alliance
            nameRect2 = (maxLoc[0] - 0.015, maxLoc[1] - .126, 0.364, 0.027)  # expect alliance
            locRect = (maxLoc[0] + .028, maxLoc[1], 0.195, 0.027)

            ok = False
            nameImg1 = self.vision.get_section_su(nameRect1)
            nameImg2 = self.vision.get_section_su(nameRect2)
            # nameImg1 - no alliance
            txt: str = pytesseract.image_to_string(nameImg1)
            if len(txt) > 0:
                ok = True
                name = txt.splitlines()[0]
            else:
                # nameImg2 - alliance expected
                txt: str = pytesseract.image_to_string(nameImg2)
                if len(txt) > 0:
                    rematch = re.match("[(]([A-Za-z0-9]+)[)](.+)", txt.splitlines()[0])
                    if rematch:
                        ok = True
                        name = rematch.group(2)
                        alliance = rematch.group(1)

            # read location
            locImg = self.vision.get_section_su(locRect)
            locStr = self.read_small_white_text(
                locImg,
                2,
                100,
                (2, 2),
                chars_allowed='0123456789,:XY ')

            rematch = re.search("X[:]([\d,.]+)[\s ,|]+[Y¥][:.-]([\d,.]+).*", locStr)
            location = None
            show_image('nameImg1', nameImg1)
            show_image('nameImg2', nameImg2)
            if rematch:
                location = (int(rematch.group(1).replace(',', '')), int(rematch.group(2).replace(',', '')))

        return (name, alliance, location)

    def read_staminas(self) -> tuple[str, tuple[float, float]]:
        markers = self.templates.stamina_marker.find_all(self.vision, (0.491, 0.321), (0.781, 0.886))
        twidth = self.templates.stamina_marker.rect[2]
        results = []
        for i, marker in enumerate(markers):
            x, y = utils.point_sum(marker.topLeft().toTuple(), (twidth - 0.001, -0.002))
            w, h = (0.126, 0.028)
            img = self.vision.get_section_su((x, y, w, h))

            stam_txt = self.read_small_white_text(img, dilate_size=(2, 2), chars_allowed='0123456789/', threshold=60)
            parts = stam_txt.split('/')
            if len(parts) == 2:
                try:
                    squad_name_pos = utils.point_sub((x, y), (0.528, 0.029))
                    results.append((int(parts[0]), squad_name_pos))
                except:
                    pass
        return results

    def is_keybord_enabled(self) -> bool:
        if not self.vision.is_ready():
            raise Exception('vision not ready')
        img = self.vision.get_section_2p_su((0.81, 0.95), (0.90, 0.98))
        #cv2.imshow("ok", img)
        txt: str = pytesseract.image_to_string(img, config='--psm 7').strip().upper()
        return "OK" in txt or "0K" in txt

    def is_march_button(self) -> bool:
        # troop_march_button
        img = self.vision.get_section_2p_su((0.5, 0.916), (0.883, 0.973))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # set lower and upper color limits
        hsv_min = np.array([16, 67, 0])
        hsv_max = np.array([25, 255, 255])
        mask = cv2.inRange(hsv, hsv_min, hsv_max)
        #print("avg " + str(np.average(mask)))
        found = np.average(mask) > 200
        return found

    def read_nest_level(self) -> int:
        #img = self.vision.get_section_2p_su((0.449, 0.47),(0.490, 0.490))
        img = self.vision.get_section_2p_su((0.457, 0.478), (0.481, 0.492))
        hsv_min = np.array([0, 0, 40])
        hsv_max = np.array([250, 75, 260])
        #img = utils.apply_hsv_mask(img, hsv_min, hsv_max, blur=False )
        txt = self.read_small_white_text(img,
                                         3,
                                         90,
                                         # dilate_size=(2,2),
                                         chars_allowed='0123456789'
                                         )
        try:
            if len(txt) > 0:
                num = int(txt.splitlines()[0])
                if num <= 25 and num > 0:
                    return num
        except:
            pass
        return None

    @staticmethod
    def read_small_white_text(locImg, resize_factor=2, threshold=70, dilate_size=None, chars_allowed='', margin=5) -> str:
        img = locImg.copy()
        img = cv2.resize(img, (img.shape[1] * resize_factor, img.shape[0] * resize_factor))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY_INV)[1]

        frame = np.ones((img.shape[0] + margin * 2, img.shape[1] + margin * 2), dtype=np.uint8) * 255
        frame[margin: -margin, margin:-margin] = img
        img = frame

        if not dilate_size is None:
            img = cv2.erode(img, np.ones(dilate_size, dtype=np.uint8))
        if debug:
            QImageViewer.show_image('read_small_white_text_img', locImg)
            QImageViewer.show_image('read_small_white_text_final', img)

        confstring = '--psm 7 '
        if not chars_allowed is None:
            confstring += f'-c tessedit_char_whitelist="{chars_allowed}"'
        txt = pytesseract.image_to_string(img, config=confstring)
        return txt
