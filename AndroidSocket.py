import socket
from time import sleep
from PIL import Image
import io
import cv2
import numpy as np


class AndroidSocket(object):
    def __init__(self, path=None):
        self._host = "192.168.0.8"
        self._port = 50001
        self._path = path

    def take_pic(self, name):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("socket created")
        s.connect((self._host, self._port))
        s.sendall(b"take pic")
        s.shutdown(socket.SHUT_WR)
        sleep(0.5)
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.connect(("192.168.0.8", 50001))
        data = b''
        data_found = False
        while True:
            new_data = s.recv(1024)
            data += new_data
            if len(new_data) > 0:
                data_found = True
            else:
                sleep(0.5)
            if data_found and len(new_data) == 0:
                break
            # print(data)
        # print("data: " + data.decode())
        # s.shutdown(socket.SHUT_RD)
        s.close()
        image = Image.open(io.BytesIO(data)).convert('RGB')
        #image = Image.open(io.BytesIO(data))
        #image.show()
        imcv = np.array(image)
        #image.show()
        imcv = imcv[:, :, ::-1].copy()
        imcv = cv2.rotate(imcv, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite(f'%s\\%s' % (self._path, name), imcv)
        return True
