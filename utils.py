import numpy as np
import cv2
from PySide6.QtGui import QImage
import random
import math


def get_hsv_mask(img: np.ndarray, lower_val, upper_val, blur=True, ksize=(8, 8)):
    hsv = img.copy()
    if blur:
        hsv = cv2.blur(hsv, ksize)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_val), np.array(upper_val))
    return mask


def apply_hsv_mask(img: np.ndarray, lower_val, upper_val, blur=True, ksize=(8, 8)):
    hsv = img.copy()
    if blur:
        hsv = cv2.blur(hsv, ksize)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_val), np.array(upper_val))
    imgMasked = cv2.bitwise_and(img, img, mask=mask)
    return imgMasked


def qimage_from_cv2(img: np.ndarray):
    h, w, c = img.shape
    if c == 3:
        return QImage(img.data, w, h, 3 * w, QImage.Format.Format_BGR888)
    else:
        return QImage(img.data, w, h, 1 * w, QImage.Format.Format_Grayscale8)


def binarize(img, threshold=150):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    return img


def random_range(rangestart, rangend):
    return rangestart + random.random() * (rangend - rangestart)


def random_point_in_rectangle(top_left, bot_right):
    return (random_range(top_left[0], bot_right[0]), random_range(top_left[1], bot_right[1]))


def point_sum(a: tuple[int | float, int | float], b: tuple[int | float, int | float]) -> tuple[int | float, int | float]:
    return (a[0] + b[0], a[1] + b[1])


def point_sub(a: tuple[int | float, int | float], b: tuple[int | float, int | float]) -> tuple[int | float, int | float]:
    return (a[0] - b[0], a[1] - b[1])


def point_distance(a: tuple[int | float, int | float], b: tuple[int | float, int | float]):
    return math.sqrt(math.pow(a[0] - b[0], 2) + math.pow(a[1] - b[1], 2))
