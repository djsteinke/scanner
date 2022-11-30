import os
from time import strftime, sleep
import json
import logging
from tkinter import Toplevel, Button
from threading import Timer
import cv2

from AndroidSocket import AndroidSocket
from camera_config import apply_brightness_contrast

module_logger = logging.getLogger('CircularScan.scan')
step_delay = 0.7


def take_pic(path, pic, android=None, cam=None, camera_calibration=None, bright=0, contrast=0):

    android_socket = AndroidSocket(path)
    android_socket.take_pic(pic)
    """
    if cam is not None:
        ret, cv2image = cam.read()
        if ret:
            h, w, _ = cv2image.shape
            if w > h:
                cv2image = cv2.rotate(cv2image, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2image = camera_calibration.undistort_img(cv2image, crop=False)
            cv2image = apply_brightness_contrast(cv2image, bright, contrast)
            cv2.imwrite(f'%s\\%s' % (path, pic), cv2image)
    elif android is not None:
        android.take_picture(f'%s\\%s' % (path, pic))
        """


class CircularScan(object):
    def __init__(self, cap=None, arduino=None, android=None, d="/", s=100, c=None, sc=None,
                 degrees=1, ll=False, rl=True, color=False, camera_calibration=None, brightness=None, contrast=None):
        self.cap = cap
        self.camera_calibration = camera_calibration
        self.arduino = arduino
        self.android = android
        self.wd = d
        self.steps = s
        self.ll = ll
        self.rl = rl
        self.color = color
        self._callback = c
        self._step_callback = sc
        self.path = None
        self.degrees = degrees
        self.tl = None
        self._bright = 0 if brightness is None else brightness.get()
        self._contrast = 0 if contrast is None else contrast.get()
        dps = float(degrees) / 360.0 / float(self.steps-1)
        self.pps = round(200.0 * 16.0 * dps)          # 200 full steps per rotation (motor), 16 micro-steps
        print(self.pps)
        self.timestamp = strftime('%Y%m%d%H%M%S')

    def start(self):
        self.path = os.path.join(self.wd, f"scans")
        self.save_details()

        if not self.arduino.connected:
            self.arduino.open()

        if not self.arduino.connected:
            print("Arduino not connected. Exiting.")
            if self._step_callback is not None:
                self._step_callback(-1)
            exit()

        self.path = os.path.join(self.wd, f"scans\\{self.timestamp}")  # create scans dir
        os.makedirs(self.path)
        self.save_details()

        # calib_dir = self.wd + "\\scans\\calibration"
        # if os.path.isdir(calib_dir):
        #     shutil.copytree(calib_dir, self.path)
        """
        pic = 'calibration_line.jpg'
        self.android.take_picture(f'%s\\%s' % (self.path, pic))
        sleep(0.2)

        if self.ll:
            self.arduino.send_msg_new(2)
            module_logger.debug('PICO.LL ON')
            sleep(0.2)
            pic = 'calibration_ll.jpg'
            self.android.take_picture(f'%s\\%s' % (self.path, pic))
            module_logger.debug(f'Picture[{pic}] saved.')
            self.arduino.send_msg_new(1)
            module_logger.debug('PICO.LL OFF')
            sleep(0.2)

        if self.rl:
            self.arduino.send_msg_new(4)
            module_logger.debug('PICO.RL ON')
            sleep(0.2)
            pic = 'calibration_rl.jpg'
            self.android.take_picture(f'%s\\%s' % (self.path, pic))
            module_logger.debug(f'Picture[{pic}] saved.')
            self.arduino.send_msg_new(3)
            module_logger.debug('PICO.RL OFF')
            sleep(0.2)

        half = int(200 * 16 / 2)
        self.arduino.send_msg_new(6, 1, half)
        pic = 'calibration_pattern.jpg'
        self.android.take_picture(f'%s\\%s' % (self.path, pic))
        """
        # popup to setup object
        self.tl = Toplevel()
        cb = Button(self.tl, text="Scan", command=self.scan_clicked, width=15)
        self.tl.geometry('200x100+100+450')
        cb.pack(pady=(40, 0))
        self.tl.grab_set()

    def scan_clicked(self):
        self.tl.destroy()
        if self._callback is not None:
            self._callback()
        Timer(0.1, self.scan).start()

    def scan(self):
        if not self.ll and not self.color:
            self.arduino.send_msg_new(4)
            module_logger.debug('PICO.RL ON')
            sleep(step_delay)
        for i in range(0, self.steps):
            if self.ll:
                if self.rl or self.color:
                    # self.arduino.send_msg("L11")     # Turn ON left laser
                    self.arduino.send_msg_new(2)
                    module_logger.debug('PICO.LL ON')
                    sleep(step_delay)
                pic = 'left_%04d.jpg' % i
                take_pic(self.path, pic, self.android, self.cap, self.camera_calibration, self._bright, self._contrast)
                print(pic)
                module_logger.debug(f'Picture[{pic}] saved.')
                if self.rl or self.color:
                    # self.arduino.send_msg("L10")     # Turn OFF left laser
                    self.arduino.send_msg_new(1)
                    module_logger.debug('PICO.LL OFF')
            if self.rl:
                if self.ll or self.color:
                    # self.arduino.send_msg("L21")     # Turn ON right laser
                    self.arduino.send_msg_new(4)
                    module_logger.debug('PICO.RL ON')
                    sleep(step_delay)
                pic = 'right_%04d.jpg' % i
                take_pic(self.path, pic, self.android, self.cap, self.camera_calibration, self._bright, self._contrast)
                print(pic)
                module_logger.debug(f'Picture[{pic}] saved.')
                if self.ll or self.color:
                    # self.arduino.send_msg("L20")     # Turn OFF right laser
                    self.arduino.send_msg_new(3)
                    module_logger.debug('PICO.RL OFF')
                    sleep(step_delay)
            if self.color:
                pic = 'color_%04d.jpg' % i
                take_pic(self.path, pic, self.android, self.cap, self.camera_calibration, self._bright, self._contrast)
                print(pic)
                module_logger.debug(f'Picture[{pic}] saved.')
            # self.arduino.send_msg(f"STEP:{self.pps}:CW")      # turn platform
            self.arduino.send_msg_new(6, 1, self.pps)
            module_logger.debug(f'PICO.STEP[{i}]')
            sleep(step_delay)
            if self._step_callback is not None:
                self._step_callback(i+1)
        self._step_callback(-2)
        if self.android is not None:
            self.android.move_files(self._step_callback)
            print('moving files complete.')
            self.android.sync_media_service()
        if self._callback is not None:
            self._callback()

    def save_details(self):
        dps = self.pps / (200.0 * 16.0) * 360.0
        details = {"date": self.timestamp,
                   "steps": self.steps,
                   "ll": self.ll,
                   "rl": self.rl,
                   "color": self.color,
                   "type": "circular",
                   "dps": round(dps, 2)}
        print(details)
        d_path = self.path + "\\details.json"
        f = open(d_path, 'w')
        f.write(json.dumps(details))
        f.close()
