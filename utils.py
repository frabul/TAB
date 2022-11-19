import numpy as np
import cv2
from PySide6.QtGui import QImage

def get_hsv_mask( img: np.ndarray, lower_val, upper_val):
    ksize = (8, 8)
    hsv = cv2.blur(img, ksize)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_val), np.array(upper_val))
    return mask

def apply_hsv_mask( img: np.ndarray, lower_val, upper_val):
    hsv = img.copy()
    #ksize = (8, 8)
    #hsv = cv2.blur(img, ksize)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_val), np.array(upper_val))
    imgMasked = cv2.bitwise_and(img, img, mask=mask)
    return imgMasked

def qimage_from_cv2( img: np.ndarray): 
    h, w, c = img.shape 
    if c == 3:
        return QImage(img.data, w, h, 3 * w, QImage.Format.Format_BGR888)
    else:
        return QImage(img.data, w, h, 1 * w, QImage.Format.Format_Grayscale8)