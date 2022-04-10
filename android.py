from time import sleep
from ppadb.client import Client as AdbClient
from subprocess import run
from os import getcwd


class Android(object):
    def __init__(self):
        self.client = None
        self.device = None
        self.d = None

    def connect_tmp(self, host, port, callback):
        self.d = f'{host}:{port}'
        res = run(['adb', 'connect', self.d], capture_output=True)
        print(res)
        if 'connected' in res.stdout.decode():
            callback(None, True)

    def connect(self, host="127.0.0.1", port=5037, callback=None):
        try:
            print("get client")
            self.client = AdbClient(host, port)
            print("client connected")
        except OSError or RuntimeError:
            if callback is not None:
                callback(None, True)
            raise Exception('Error connecting to ADB server or device.')
        print('client')
        sleep(15)
        devices = self.client.devices()
        print(f'looking for device. len[{len(devices)}]')
        if len(devices) > 0:
            self.device = devices[0]
            print("device found")
        if callback is not None:
            callback(None, True)

    def disconnect(self):
        if self.client is not None:
            self.client.close()
        else:
            res = run(['adb', 'disconnect', self.d], capture_output=True)

    def open_camera(self):
        if self.device is not None:
            self.device.shell('input tap 900 1800')  # Open Camera
            # device.shell('am start -a android.media.action.IMAGE_CAPTURE')
            sleep(2)

    def open_camera_tmp(self):
        res = run(['adb', '-s', self.d, 'shell', 'input', 'tap', '900', '1800'], capture_output=True)
        print(res)
        sleep(2)
        run(['adb', '-s', self.d, 'shell', 'input', 'tap', '550', '1100'], capture_output=True)
        sleep(2)

    def take_picture_tmp(self, path):
        #sleep(1)
        run(['adb', '-s', self.d, 'shell', 'input', 'keyevent', 'KEYCODE_CAMERA'], capture_output=True)
        print('picture taken')
        sleep(1)
        while True:
            res = run(['adb', '-s', self.d, 'shell', 'ls', '-Art', '/storage/emulated/0/DCIM/Camera', '|', 'tail', '-n', '1'],
                      capture_output=True)
            filename = res.stdout.decode().replace('\r', '').replace('\n', '')
            print(filename)
            if '.pending' not in filename:
                break
            sleep(1)
        res = run(['adb', '-s', self.d, 'pull', f'/storage/emulated/0/DCIM/Camera/{filename}', path], capture_output=True)
        # adb shell rm -f /sdcard/DCIM/Image.jpeg
        run(['adb', '-s', self.d, 'rm', '-f', f'/storage/emulated/0/DCIM/Camera/{filename}'], capture_output=True)
        print(res)

    def take_picture(self, path='img.jpg'):
        if self.device is not None:
            self.device.shell('input keyevent KEYCODE_CAMERA')  # Take pic
            print('picture taken')
            sleep(1)
            filename = self.device.shell('ls -Art /storage/emulated/0/DCIM/Camera | tail -n 1')  # get file name
            print(filename)
            self.device.pull(f'/storage/emulated/0/DCIM/Camera/{filename}', path)  # copy file

    def sync_media_service(self):
        run(['adb', '-s', self.d, 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
             '-d', f'file:/storage/emulated/0/DCIM/Camera'], capture_output=True)
