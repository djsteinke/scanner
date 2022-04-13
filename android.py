from time import sleep
from subprocess import run


def print_res(res):
    if len(res.stderr.decode()) > 0:
        print(f'ANDROID ERROR: {res.stderr.decode()}')


class Android(object):
    def __init__(self, host='192.168.0.37', port=5555, cb=None):
        self._callback = cb
        self.d = f'{host}:{port}'
        self.connected = False
        self.last_filename = ""

    def connect(self):
        res = run(['adb', 'connect', self.d], capture_output=True)
        print_res(res)
        if 'connected' in res.stdout.decode():
            self.connected = True
            self._callback(None, True, 'connected')

    def disconnect(self):
        res = run(['adb', 'disconnect', self.d], capture_output=True)
        print_res(res)
        self.connected = False

    def open_camera(self):
        res = run(['adb', '-s', self.d, 'shell', 'input', 'tap', '900', '1800'], capture_output=True)
        print_res(res)
        sleep(2)
        res = run(['adb', '-s', self.d, 'shell', 'input', 'tap', '550', '1100'], capture_output=True)
        print_res(res)
        sleep(2)

    def take_picture(self, path):
        res = run(['adb', '-s', self.d, 'shell', 'input', 'keyevent', 'KEYCODE_CAMERA'], capture_output=True)
        print_res(res)
        print('picture taken')
        sleep(1)
        while True:
            res = run(['adb', '-s', self.d, 'shell', 'ls', '-Art', '/storage/emulated/0/DCIM/Camera', '|', 'tail', '-n', '1'],
                      capture_output=True)
            filename = res.stdout.decode().replace('\r', '').replace('\n', '')
            print(filename)
            if '.pending' not in filename and filename != self.last_filename:
                break
            sleep(1)
        self.last_filename = filename
        res = run(['adb', '-s', self.d, 'pull', f'/storage/emulated/0/DCIM/Camera/{filename}', path],
                  capture_output=True)
        print_res(res)

        res = run(['adb', '-s', self.d, 'shell', 'rm', '-f', f'/storage/emulated/0/DCIM/Camera/{filename}'],
                  capture_output=True)
        print_res(res)

    def sync_media_service(self):
        run(['adb', '-s', self.d, 'am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
             '-d', f'file:/storage/emulated/0/DCIM/Camera'], capture_output=True)
