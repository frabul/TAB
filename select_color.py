import numpy as np 
import cv2
import QImageViewer

# load image
img = cv2.imread("temp.bmp")
# convert to HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 
# set lower and upper color limits
lower_val = np.array([13,80,140])
upper_val = np.array([20,120,220])
# Threshold the HSV image to get only green colors
mask = cv2.inRange(hsv, lower_val, upper_val)
# apply mask to original image - this shows the green with black blackground
only_green = cv2.bitwise_and(img,img, mask=mask)
 
#show image
QImageViewer.show_image("img", mask)
