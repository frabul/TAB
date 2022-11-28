import numpy as np
import cv2

from .vision import Vision
from .template import Template
from . import utils
from . import QImageViewer

hsv_min = np.array([83, 148, 132])
hsv_max = np.array([[69, 54, 54]])


class Templates:
    def __init__(self) -> None:
        self.items = {}

        # magniglass
        self.magniglass = Template('magniglass', (0.022, 0.63), (0.101, 0.677), score_min=0.7)

        def prepareMagni(img: np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
            return img[1]
        self.magniglass.prepare = prepareMagni

        # define workers_icon
        self.workers_icon = Template('workers_icon', (0.027, 0.139), (0.099, 0.173), score_min=0.75)

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
            return utils.apply_hsv_mask(img, hsv_min, hsv_max, ksize=(3, 3))
        self.nest_l16_mini = Template('nest_l16_mini', (0.546, 0.618), (0.644, 0.653))  # (0.453, 0.692),(0.556, 0.724)
        self.nest_l16_mini.prepare = prepareNest

        # nest_eggs_mini
        self.nest_eggs_mini = Template('nest_eggs_mini', (0.453, 0.68), (0.549, 0.7))

        # zucca1
        self.nest_zucca1_mini = Template('nest_zucca1_mini', (0.394, 0.684), (0.473, 0.722))

        # next_ruby_lizard_mini
        self.nest_ruby_lizard_mini = Template('nest_ruby_lizard_mini', (0.662, 0.664), (0.762, 0.7))

        # nest_ice_cream_mini
        self.nest_ice_cream_mini = Template('nest_ice_cream_mini', (0.722, 0.414), (0.821, 0.437))

        # nest_banana_mini
        self.nest_banana_mini = Template('nest_banana_mini', (0.41, 0.659), (0.513, 0.687))

        # nest_snake_mini
        self.nest_snake_mini = Template('nest_snake_mini', (0.579, 0.579), (0.653, 0.624))

        # nest_fish_mini
        self.nest_fish_mini = Template('nest_fish_mini', (0.368, 0.712), (0.448, 0.748))

        # nest_dino_mini
        self.nest_dino_mini = Template('nest_dino_mini', (0.738, 0.637), (0.827, 0.666))

        # nest_neko_mini
        self.nest_neko_mini = Template('nest_neko_mini', (0.458, 0.606), (0.536, 0.641))

        # nest_bonsai_mini 
        self.nest_bonsai_mini = Template('nest_bonsai_mini', (0.516, 0.68), (0.588, 0.71) ) 

        # nest_fish2_mini 
        self.nest_fish2_mini = Template('nest_fish2_mini', (0.527, 0.661), (0.612, 0.701) ) 

        # nest_bird_mini 
        self.nest_bird_mini = Template('nest_bird_mini', (0.442, 0.446), (0.534, 0.487) ) 

        # nest_amber_mini 
        self.nest_amber_mini = Template('nest_amber_mini', (0.392, 0.57), (0.469, 0.606) ) 

        # nest_crystal_baron_mini 
        self.nest_crystal_baron_mini = Template('nest_crystal_baron_mini', (0.487, 0.577), (0.536, 0.623) ) 

        # nest_whale_mini 
        self.nest_whale_mini = Template('nest_whale_mini', (0.491, 0.397), (0.556, 0.433) )  

        # nest_octopus_mini 
        self.nest_octopus_mini = Template('nest_octopus_mini', (0.478, 0.731), (0.549, 0.768) ) 

        # nest_shell_mini 
        self.nest_shell_mini = Template('nest_shell_mini', (0.444, 0.645), (0.507, 0.685) )  

        # nest_ananas_mini 
        self.nest_ananas_mini = Template('nest_ananas_mini', (0.451, 0.618), (0.507, 0.648) )  

        # nest_pangolin_mini 
        self.nest_pangolin_mini = Template('nest_pangolin_mini', (0.415, 0.688), (0.493, 0.729) ) 

        # nest_rafflesia_mini 
        self.nest_rafflesia_mini = Template('nest_rafflesia_mini', (0.478, 0.625), (0.536, 0.665) ) 

        # nest_astice_mini 
        self.nest_astice_mini = Template('nest_astice_mini', (0.408, 0.681), (0.489, 0.712) ) 

        # nest_cocomero_mini 
        self.nest_cocomero_mini = Template('nest_cocomero_mini', (0.442, 0.683), (0.516, 0.714) ) 

        # nest_spongebob_mini 
        self.nest_spongebob_mini = Template('nest_spongebob_mini', (0.383, 0.563), (0.46, 0.594) ) 

        # nest_santa_mini 
        self.nest_santa_mini = Template('nest_santa_mini', (0.366, 0.667), (0.421, 0.702), score_min=0.95  ) 

        # nest_sake_mini 
        self.nest_sake_mini = Template('nest_sake_mini', (0.462, 0.667), (0.536, 0.702) ) 

        # nest_nautilus_mini 
        self.nest_nautilus_mini = Template('nest_nautilus_mini', (0.464, 0.624), (0.543, 0.659) ) 
   
        # nest_l22_mini 
        self.nest_l22_mini = Template('nest_l22_mini', (0.381, 0.651), (0.471, 0.676) ) 
        
        # nest_dragon_fruit_mini 
        self.nest_dragon_fruit_mini = Template('nest_dragon_fruit_mini', (0.343, 0.538), (0.442, 0.558) ) 
        # nest_orchids_mini 
        self.nest_orchids_mini = Template('nest_orchids_mini', (0.401, 0.69), (0.473, 0.716) ) 
        # nest_paguro_mini 
        self.nest_paguro_mini = Template('nest_paguro_mini', (0.413, 0.675), (0.498, 0.708) ) 
 
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
        self.location_marker = Template('location_marker', (0.271, 0.526), (0.305, 0.552), score_min=0.85)
        self.location_marker.prepare = prepare_location_marker

        # app_icon
        self.app_icon = Template('app_icon', (0.704, 0.198), (0.8, 0.257), score_min=0.9)

        # load all
        for key, val in self.__dict__.items():
            if type(val) is Template:
                val.load()
                self.items[key] = val
