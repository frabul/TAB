import random 
import cv2
import numpy as np
import os
from time import sleep, time 
from vision import Vision
from pynput import keyboard, mouse
import pyautogui
import queue 
import re

import easyocr
import QImageViewer
import pytesseract
import timeit


#ocrreader = easyocr.Reader(['en']) 
pytesseract.pytesseract.tesseract_cmd = 'D:\\Tools\\Tesseract\\tesseract.exe'
 

coordinates = { } 

 

# Change the working directory to the folder this script is in.
# Doing this because I'll be putting the files from each video in their own folder on GitHub
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# set failsafe just in case
pyautogui.FAILSAFE = True
wincap = Vision('BlueStacks App Player', (1, 35, 1, 1))
callback_queue = queue.Queue()


loop_time = time()
counter = 0
screenshot = wincap.get_screenshot()
wincap.start()
end = False
while not end:
    # debug the loop rate
    loop_time = time()
    img = wincap.get_section_su((0.18, 0.27, 0.58, 0.48))
    if img is None:
        continue
    
    # resize
    scale_factor = 2 # percent of original size
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor) 
    img = cv2.resize(img, (width, height) )

    # Convert the image to gray scale
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    #dilate
    kernel = np.ones((3,3),np.uint8)
    #img = cv2.dilate(img, kernel, iterations = 1)

    # Performing OTSU threshold
    #ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv.THRESH_TOZERO ) 
    #ret, img = cv2.threshold(img, 50, 255, cv2.THRESH_TOZERO )

    

     
    QImageViewer.show_image('analized', img) 
    text = ""

    def use_easyocr():
        global text
        text = reader.readtext(img, min_size=10, blocklist=';.', paragraph=True) 
        text = '\r\n'.join([x[1] for x in text ])

    def use_tesseract():
        global text
        text = pytesseract.image_to_string(img)

    #t1 = timeit.timeit(use_easyocr, number = 3)
    #t2 = timeit.timeit(use_tesseract, number = 3)
    #print(f"t1 {t1}    t2 {t2}")
    use_tesseract()
    #print(text)

    match = re.findall('\s+#811\s+X[:. ]?(\d+) [Y¥][:. -]?(\d+)',text) 
    for m in match:
        location = (int(m[0]), int(m[1]))
        if not location in coordinates:
            coordinates[location] = 0
        coordinates[location] += 1
    
    confirmed_cnt = len([x for x in coordinates if coordinates[x] > 10])
    
    print(f'Found {confirmed_cnt} coordinates.')
 

 

farms_confirmed = [x for x in coordinates if coordinates[x] > 10]
print(farms_confirmed)