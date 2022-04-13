import os
from time import strftime
import json
import shutil


class CircularScan(object):
    def __init__(self, cap=None, arduino=None, android=None, d="/", s=100, c=None, sc=None,
                 degrees=1, ll=False, rl=True, color=False):
        self.cap = cap
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
        dps = float(degrees) / 360.0 / float(self.steps)
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

        calib_dir = self.wd + "\\scans\\calibration"
        if os.path.isdir(calib_dir):
            shutil.copytree(calib_dir, self.path)

        for i in range(1, self.steps+1):
            if self.ll:
                if self.rl or self.color:
                    self.arduino.send_msg("L11")     # Turn ON left laser
                self.android.take_picture(f'%s\\left_%04d.jpg' % (self.path, i))
                if self.rl or self.color:
                    self.arduino.send_msg("L10")     # Turn OFF left laser
            if self.rl:
                if self.ll or self.color:
                    self.arduino.send_msg("L21")     # Turn ON right laser
                self.android.take_picture(f'%s\\right_%04d.jpg' % (self.path, i))
                if self.ll or self.color:
                    self.arduino.send_msg("L20")     # Turn OFF right laser
            if self.color:
                self.android.take_picture(f'%s\\color_%04d.jpg' % (self.path, i))
            self.arduino.send_msg(f"STEP:{self.pps}:CW")      # turn platform
            if self._step_callback is not None:
                self._step_callback(i+1)

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
