
from components.vision import Vision
from components.templates import Templates, Template
import cv2
from components import QImageViewer

if __name__ == '__main__':
    import timeit
    import time
    import keyboard
    import os
    vision = Vision('BlueStacks App Player', (1, 35, 1, 1))
    vision.start()
    templates = Templates()
    k: str = ''

    to_search : list[Template] = []
    for k, v in templates.items.items():
        if k.startswith('nest') and k.endswith('mini'):
            to_search.append(v)

    while not keyboard.is_pressed('alt+q'):
        #maxVal, maxLoc = templates.location_marker.find_max(vision, (0.004, 0.079), (0.949, 0.754) )
        #print(f"found {maxVal} at {maxLoc}"  )
        rectangles = []
        def fu(): 
            for template in to_search:
                for rect in template.find_all(vision, (0.002, 0.12), (0.919, 0.846)):
                    rectangles.append(rect)
      
        print( f"Executed search in {timeit.timeit(fu, number=1)}s")

        img = vision.get_last_screen()
        print(f"found {len(rectangles)} rectangeles")
        for rect in rectangles:
            print(f"    {rect.x()} {rect.y()} {rect.width()} {rect.height()} ")
            pos = vision.point_su_to_px((rect.x(), rect.y()))
            size = vision.point_su_to_px((rect.width(), rect.height()))
            img = cv2.rectangle(img, pos, (pos[0] + size[0], pos[1] + size[1]), (0, 0, 255))
        QImageViewer.show_image('findings', img)
        time.sleep(1)
    os._exit(0)
