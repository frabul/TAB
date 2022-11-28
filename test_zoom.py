import pyautogui
import time
from components.droid import Droid
from components.vision import Vision



droid = Droid(Vision('BlueStacks App Player', (1, 35, 1, 1)))
droid.vision.start()

droid.activate_win()
droid.zoom_out()

for x in range(10):
    (0.513, 0.248)
    pyautogui.moveTo()
    pyautogui.keyDown('ctrl')
    pyautogui.scroll(-100)
    time.sleep(1)
    pyautogui.keyUp('ctrl')