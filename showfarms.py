import cv2 as cv
import cv2
import numpy as np
from vision import Vision
import pyautogui
from time import sleep
import QImageViewer

delay_after_write = 0.2
vision = Vision('BlueStacks App Player', (1, 35, 1, 1))

dai_figli = [(512,12),(1143,51),(1139,53)]
farms =  [
        (482, 454), (391, 785), (36, 151), (485, 168), (399, 387), (381, 762), (59, 850), (93, 778), (1139, 53),
        (220, 1049), (63, 114), (183, 222), (312, 953), (531, 510), (369, 595), (470, 17), (52, 857), (436, 47), 
        (1024, 899), (1078, 920), (1150, 905), (1037, 1140), (1053, 1125), (1107, 884), (1079, 926), (300, 676),
        (161, 787), (478, 9), (119, 89), (202, 109), (235, 114), (253, 95), (347, 260), (780, 39), (967, 211), 
        (265, 875), (286, 1086), (250, 1031), (172, 1059), (467, 986), (154, 1040), (9, 84), (71, 213), (1135, 15),
        (1168, 114), (1150, 147), (997, 153), (1005, 160), (922, 180), (826, 174), (871, 208), (939, 232), 
        (1002, 250), (1065, 255),(1118, 265), (1104, 279), (1002, 273), (791, 722), (172, 511), (213, 557), 
        (75, 578), (34, 619), (312, 617), (416, 617), (182, 389), (336, 280), (169, 351), (154, 386), (1143, 51) ]
for f in dai_figli:
    if not f in farms:
        farms.append(f)
 
 
# creo mappa
img = np.zeros((600, 600, 3), dtype=np.uint8)

def map_to_img(pos): 
    x = (1200 - pos[0]) * img.shape[1] //  1200
    y = pos[1] * img.shape[0]  //  1200
    return (x, y)

def img_to_world(pos):
    x,y = pos
    fx = 1200 - x * 1200 // img.shape[1]  
    fy = y *1200 // img.shape[0] 
    return (fx, fy)

# disegno farms
for fpos in farms: 
    cv2.drawMarker(img, map_to_img(fpos), color=(0, 0, 255), markerType=cv2.MARKER_CROSS, thickness=2, )
# disegno la mia posizione
cv2.drawMarker(img, map_to_img((364, 541)), color=(0, 255, 0), markerType=cv2.MARKER_CROSS, thickness=2 ) 

cv.imwrite("farms.png", img)


farms_img = img

def click_app(pos, dismiss_keyboard=True):
    if dismiss_keyboard:
        assure_keyboard_disabled()
    cx,cy = vision.get_screen_position_rel(pos) 
    pyautogui.leftClick(x=cx, y=cy) 
    sleep(0.3)

def assure_keyboard_disabled():
    if vision.is_keybord_enabled():
        click_app((0.5,0.5), False)  


def handle_mouse(event, x, y, flags, param):  
    font = cv2.FONT_HERSHEY_SIMPLEX 
    org = (50, 50) 
    fontScale = 1 
    color = (255, 0, 0) 
    thickness = 3
    global img, farms_img
    if event == cv2.EVENT_MOUSEMOVE:
        farms_img = np.copy(img)
        fx = 1200 - x * 1200 // img.shape[1]  
        fy = y *1200 // img.shape[0] 
        txt = f"X: {fx}   Y: {fy}"
        farms_img = cv2.putText(farms_img, txt , org, font, fontScale, color, thickness, cv2.LINE_AA)
    
    # try to set those coordinates
    if event == cv2.EVENT_LBUTTONUP:
        fx,fy = img_to_world((x,y)) 
        
        # attivo app
        click_app((0.5,0.5), False)  
 
        # apro gump 
        click_app((0.5,0.81)) 
         
        # insert x 
        click_app((0.22,0.84))   
        with pyautogui.hold('ctrl'):
            sleep(0.2)
            pyautogui.press('a',)
            sleep(0.2)  
        pyautogui.press( [n for n in str(fx)])
        sleep(0.2)

        # insert y 
        click_app((0.59,0.84)) 
        with pyautogui.hold('ctrl'):
            sleep(0.2)
            pyautogui.press('a',) 
            sleep(0.2) 
        pyautogui.press( [n for n in str(fy)])
        sleep(0.2)
        
        # click go 
        click_app((0.8,0.84)) 


cv2.namedWindow("farms")
cv2.setMouseCallback("farms", handle_mouse)

vision.start()

while True:
    cv.imshow('farms', farms_img) 
    k = cv.waitKey(50)
    if k == ord('a'):
        exit(0)