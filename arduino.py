

import serial


class Arduino(object):
    def __init__(self, com="COM4", speed="9600"):
        self.serial = None
        self._connected = False
        self._sending = False
        self.response = None
        self.callback = None
        self._msg_id = 0
        self._com = com
        self._speed = speed

    def open(self):
        try:
            self.serial = serial.Serial(self._com, self._speed, timeout=0.2)
        except serial.SerialException:
            print('Arduino not found.')
            raise Exception('Failed to connect')

        # Wait for connect from arduino
        if self.serial is not None:
            while not self.connected:
                data = self.serial.readline().decode()
                if len(data) > 3:
                    print(f'rawData [{data}]')
                if data == "setup":
                    self.connected = True
            print("connected")

    def close(self):
        if self.serial is not None:
            self.serial.close()
        self.connected = False

    def get_msg_id(self):
        self._msg_id += 1
        return str(self._msg_id)

    def send_msg(self, msg_in):
        msg = self.get_msg_id() + ":" + msg_in
        if self.connected:
            print(f"Sending message[{msg}]")
            self._sending = True
            self.serial.write(bytes(msg, encoding="utf8"))
            while True:
                data = self.serial.readline().decode()
                if len(data) > 0:
                    print(f'rawData[{data}]')

                datas = data.split(":")
                if len(datas) > 0 and str(self._msg_id) == datas[0]:
                    if len(datas) > 1:
                        self.response = datas[1]
                        if self.callback is not None:
                            self.callback()
                    self._sending = False
                    break
        else:
            print("No arduino found.  Message will not be sent.")

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, val):
        self._connected = val
