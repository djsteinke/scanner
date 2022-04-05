from time import sleep
from ppadb.client import Client as AdbClient


class Android(object):
    def __init__(self):
        self.client = None
        self.device = None

    def connect(self, host="127.0.0.1", port=5037, callback=None):
        try:
            self.client = AdbClient(host, port)
        except OSError or RuntimeError:
            if callback is not None:
                callback(None, True)
            raise Exception('Error connecting to ADB server or device.')
        devices = self.client.devices()
        if len(devices) > 0:
            self.device = devices[0]
        if callback is not None:
            callback(None, True)

    def disconnect(self):
        self.client.close()

    def open_camera(self):
        if self.device is not None:
            self.device.shell('input tap 900 1800')  # Open Camera
            # device.shell('am start -a android.media.action.IMAGE_CAPTURE')
            sleep(2)

    def take_picture(self, path='img.jpg'):
        if self.device is not None:
            self.device.shell('input keyevent KEYCODE_CAMERA')  # Take pic
            print('picture taken')
            sleep(1)
            filename = self.device.shell('ls -Art /storage/emulated/0/DCIM/Camera | tail -n 1')  # get file name
            print(filename)
            self.device.pull(f'/storage/emulated/0/DCIM/Camera/{filename}', path)  # copy file
