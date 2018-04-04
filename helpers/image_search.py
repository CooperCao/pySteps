import numpy as np
import pyautogui
import random
import time
import sys
from .image_remove_noise import process_image_for_ocr
import logging
import platform
import os

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract
import cv2

pyautogui.FAILSAFE = False
DEFAULT_IMG_ACCURACY = 0.8
FIND_METHOD = cv2.TM_CCOEFF_NORMED
IMAGES = {}
DEBUG = True


def get_os():
    current_system = platform.system()
    current_os = ''
    if current_system == "Windows":
        current_os = "win"
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'
    elif current_system == "Linux":
        current_os = "linux"
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    elif current_system == "Darwin":
        current_os = "osx"
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    else:
        logging.error("Iris does not yet support your current environment: " + current_system)

    return current_os


def get_platform():
    return platform.machine()


def get_module_dir():
    return os.path.realpath(os.path.split(__file__)[0] + "/../..")


CURRENT_PLATFORM = get_os()
PROJECT_BASE_PATH = get_module_dir()
for root, dirs, files in os.walk(PROJECT_BASE_PATH):
    for file_name in files:
        if file_name.endswith(".png"):
            if CURRENT_PLATFORM in root:
                IMAGES[file_name] = os.path.join(root, file_name)
            elif "common" in root:
                IMAGES[file_name] = os.path.join(root, file_name)

logging.info("Loaded: " + str(len(IMAGES)) + " assets")
screenWidth, screenHeight = pyautogui.size()

IMAGE_DEBUG_PATH = get_module_dir() + "/image_debug"
try:
    os.stat(IMAGE_DEBUG_PATH)
except:
    os.mkdir(IMAGE_DEBUG_PATH)
for debug_image_file in os.listdir(IMAGE_DEBUG_PATH):
    file_path = os.path.join(IMAGE_DEBUG_PATH, debug_image_file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        continue

'''
Private function: Saves PIL input image for debug
'''


def _save_debug_image(search_for, search_in, res_coordinates):
    if DEBUG:
        w, h = search_for.shape[::-1]

        if isinstance(res_coordinates, list):
            for match_coordinates in res_coordinates:
                cv2.rectangle(search_in, (match_coordinates[0], match_coordinates[1]),
                              (match_coordinates[0] + w, match_coordinates[1] + h), [0, 0, 255], 2)
        else:
            cv2.rectangle(search_in, (res_coordinates[0], res_coordinates[1]),
                          (res_coordinates[0] + w, res_coordinates[1] + h), [0, 0, 255], 2)

        current_time = int(time.time())
        random_nr = random.randint(1, 51)
        cv2.imwrite(IMAGE_DEBUG_PATH + '/name_' + str(current_time) + '_' + str(random_nr) + '.png', search_in)


'''
Private function: Returns a screenshot from tuple (topx, topy, bottomx, bottomy)

Input : Region tuple (topx, topy, bottomx, bottomy)
Output : PIL screenshot image

Ex: _region_grabber(region=(0, 0, 500, 500)) 
'''


def _region_grabber(coordinates):
    x1 = coordinates[0]
    y1 = coordinates[1]
    width = coordinates[2] - x1
    height = coordinates[3] - y1
    grabbed_area = pyautogui.screenshot(region=(x1, y1, width, height))
    return grabbed_area


'''
Private function: Search for needle in stack
'''


def _match_template(search_for, search_in, precision=DEFAULT_IMG_ACCURACY, search_multiple=False):
    img_rgb = np.array(search_in)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    needle = cv2.imread(search_for, 0)

    res = cv2.matchTemplate(img_gray, needle, FIND_METHOD)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val < precision:
        return [-1, -1]
    else:
        _save_debug_image(needle, img_rgb, max_loc)
        return max_loc


def _match_template_multiple(search_for, search_in, precision=DEFAULT_IMG_ACCURACY, search_multiple=False,
                             threshold=0.7):
    img_rgb = np.array(search_in)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    needle = cv2.imread(search_for, 0)

    res = cv2.matchTemplate(img_gray, needle, FIND_METHOD)
    w, h = needle.shape[::-1]
    points = []
    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if FIND_METHOD in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc

        if max_val > threshold:
            sx, sy = top_left
            for x in range(sx - w / 2, sx + w / 2):
                for y in range(sy - h / 2, sy + h / 2):
                    try:
                        res[y][x] = np.float32(-10000)
                    except IndexError:
                        pass
            new_match_point = (top_left[0], top_left[1])
            points.append(new_match_point)
        else:
            break

    _save_debug_image(needle, img_rgb, points)
    return points


'''
Private function: Search for an image on the entire screen.
    For searching in a certain area use _image_search_area

Input :
    image_path : Path to the searched for image.
    precision : OpenCv image search precision.

Output :
   Top left coordinates of the element if found as [x,y] or [-1,-1] if not.

'''


def _image_search(image_path, precision=DEFAULT_IMG_ACCURACY):
    in_region = _region_grabber(coordinates=(0, 0, screenWidth, screenHeight))
    return _match_template(image_path, in_region, precision)


'''
Private function: Search for multiple matches of image on the entire screen.

Input :
    image_path : Path to the searched for image.
    precision : OpenCv image search precision.

Output :
   Array of coordinates if found as [[x,y],[x,y]] or [] if not.

'''


def _image_search_multiple(image_path, precision=DEFAULT_IMG_ACCURACY):
    in_region = _region_grabber(coordinates=(0, 0, screenWidth, screenHeight))
    return _match_template_multiple(image_path, in_region, precision)


'''
Private function: Search for an image within an area

Input :
    image_path :  Path to the searched for image.
    x1 : Top left x area value.
    y1 : Top left y area value.
    x2 : Bottom right x area value.
    y2 : Bottom right y area value.
    precision : OpenCv image search precision.
    in_region : an already cached region, in this case x1,y1,x2,y2 will be ignored

Output :
    Top left coordinates of the element if found as [x,y] or [-1,-1] if not.
'''


def _image_search_area(image_path, x1, y1, x2, y2, precision=DEFAULT_IMG_ACCURACY, in_region=None):
    if in_region is None:
        in_region = _region_grabber(coordinates=(x1, y1, x2, y2))
    return _match_template(image_path, in_region, precision)


'''
Private function: Search for an image on entire screen continuously until it's found.

Input :
    image_path : Path to the searched for image.
    time_sample : Waiting time after failing to find the image .
    precision :  OpenCv image search precision.

Output :
     Top left coordinates of the element if found as [x,y] or [-1,-1] if not.

'''


def _image_search_loop(image_path, time_sample, attempts=5, precision=0.8):
    pos = _image_search(image_path, precision)
    tries = 0
    while (pos[0] == -1) and (tries < attempts):
        time.sleep(time_sample)
        pos = _image_search(image_path, precision)
        tries += 1
    return pos


'''
Private function: Search for an image on a region of the screen continuously until it's found.

Input :
    time : Waiting time after failing to find the image. 
    image_path :  Path to the searched for image.
    x1 : Top left x area value.
    y1 : Top left y area value.
    x2 : Bottom right x area value.
    y2 : Bottom right y area value.
    precision : OpenCv image search precision.
    in_region : An already cached region, in this case x1,y1,x2,y2 will be ignored

Output :
    Top left coordinates of the element if found as [x,y] or [-1,-1] if not.

'''


def _image_search_region_loop(image_path, time_sample, x1, y1, x2, y2, precision=DEFAULT_IMG_ACCURACY, in_region=None):
    pos = _image_search_area(image_path, x1, y1, x2, y2, precision, in_region)
    while pos[0] == -1:
        time.sleep(time_sample)
        pos = _image_search_area(image_path, x1, y1, x2, y2, precision, in_region)
    return pos


'''

Private function: Clicks on a image

input :
    image_path : Path to the clicked image ( only for width,height calculation)
    pos : Position of the top left corner of the image [x,y].
    action : button of the mouse to activate : "left" "right" "middle".
    time : Time taken for the mouse to move from where it was to the new position.
'''


def _click_image(image_path, pos, action, time_stamp):
    img = cv2.imread(image_path)
    height, width, channels = img.shape
    pyautogui.moveTo(pos[0] + width / 2, pos[1] + height / 2, time_stamp)
    pyautogui.click(button=action)


def _text_search_all(in_region=None):
    if in_region is None:
        in_region = _region_grabber(coordinates=(0, 0, screenWidth, screenHeight))

    tesseract_match_min_len = 12
    input_image = np.array(in_region)
    optimized_ocr_image = process_image_for_ocr(image_array=Image.fromarray(input_image))

    if DEBUG:
        cv2.imwrite(IMAGE_DEBUG_PATH + "/debug_ocr_ready.png", optimized_ocr_image)

    optimized_ocr_array = np.array(optimized_ocr_image)
    processed_data = pytesseract.image_to_data(Image.fromarray(optimized_ocr_array))

    final_data = []
    for line in processed_data.split("\n"):
        try:
            data = line.encode("ascii").split()
            if len(data) is tesseract_match_min_len:
                precision = int(data[10]) / float(100)
                new_match = {'x': data[6],
                             'y': data[7],
                             'width': data[8],
                             'height': data[9],
                             'precision': precision,
                             'value': data[11]
                             }
                final_data.append(new_match)
        except:
            continue

    return final_data


def wait(image_name, max_attempts=10, interval=0.5, precision=DEFAULT_IMG_ACCURACY):
    image_path = IMAGES[image_name]
    image_found = _image_search_loop(image_path, interval, max_attempts, precision)
    if (image_found[0] != -1) & (image_found[1] != -1):
        return True
    return False


def waitVanish(image_name, max_attempts=10, interval=0.5, precision=DEFAULT_IMG_ACCURACY):
    logging.debug("Wait vanish for: " + image_name)
    pattern_found = wait(image_name, 1)
    tries = 0
    while (pattern_found is True) and (tries < max_attempts):
        time.sleep(interval)
        pattern_found = wait(image_name, 1)
        tries += 1

    return pattern_found


# @todo Search in regions for faster results
def click(image_name):
    logging.debug("Try click on: " + image_name)
    image_path = IMAGES[image_name]
    pos = _image_search(image_path)
    if pos[0] != -1:
        _click_image(image_path, pos, "left", 0)
        time.sleep(1)
        return pos
    else:
        logging.debug("Image not found:", image_name)


def exists(image_name):
    return wait(image_name, 3, 0.5)


# @todo to take in consideration the number of screens
def get_screen():
    if DEBUG is True:
        pyautogui.displayMousePosition()
    return _region_grabber(coordinates=(0, 0, screenWidth, screenHeight))


def hover(x=0, y=0, duration=0.0, tween='linear', pause=None, image=None):
    if image is not None:
        pos = _image_search(image)
        if pos[0] != -1:
            pyautogui.moveTo(pos[0], pos[1])
    else:
        x = int(x)
        y = int(y)
        pyautogui.moveTo(x, y, duration, tween, pause)


def find(image_name):
    image_path = IMAGES[image_name]
    return _image_search(image_path)


def findAll(image_name):
    image_path = IMAGES[image_name]
    return _image_search_multiple(image_path)


def typewrite(text, interval=0.02):
    logging.debug("Type: " + str(text))
    pyautogui.typewrite(text, interval)


def press(key):
    logging.debug("Press: " + key)
    pyautogui.keyDown(str(key))
    pyautogui.keyUp(str(key))


def hotkey_press(*args):
    pyautogui.hotkey(*args)


def keyDown(key):
    pyautogui.keyDown(key)


def keyUp(key):
    pyautogui.keyUp(key)


def scroll(clicks):
    pyautogui.scroll(clicks)