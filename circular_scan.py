import os
from time import strftime
import json


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
        self._lasers = [False, False]       # left/right
        self.path = None
        self.degrees = degrees
        self.per_step = 360 / degrees / self.steps
        print(self.per_step)
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

        motor_steps = 200 * 2 * self.per_step       # 200 full steps per rotation (motor), 2 micro-steps

        if not self.ll:
            self.arduino.send_msg("L21")     # Turn ON right laser
            self._lasers[1] = True

        for i in range(0, self.steps):
            if self.ll:
                if not self._lasers[0]:
                    self.arduino.send_msg("L11")     # Turn ON left laser
                    self._lasers[0] = True
                self.android.take_picture(f'%s\\left_%04d.jpg' % (self.path, i))
                self.arduino.send_msg("L10")     # Turn OFF left laser
                self._lasers[0] = False
            if self.rl:
                if not self._lasers[1]:
                    self.arduino.send_msg("L21")     # Turn ON right laser
                    self._lasers[1] = True
                self.android.take_picture_tmp(f'%s\\right_%04d.jpg' % (self.path, i))
                if self.ll or self.color:
                    self.arduino.send_msg("L20")     # Turn OFF right laser
                    self._lasers[1] = False
            if self.color:
                self.android.take_picture_tmp(f'%s\\color_%04d.jpg' % (self.path, i))
            self.arduino.send_msg(f"STEP:{motor_steps}:CW")      # turn platform
            if self._step_callback is not None:
                self._step_callback(i+1)

        self.android.sync_media_service()
        if self._callback is not None:
            self._callback()

    def save_details(self):
        details = {"date": self.timestamp,
                   "steps": self.steps,
                   "ll": self.ll,
                   "rl": self.rl,
                   "color": self.color,
                   "type": "circular",
                   "dps": '%0.2f' % self.per_step}
        print(details)
        d_path = self.path + "\\details.json"
        f = open(d_path, 'w')
        f.write(json.dumps(details))
        f.close()
