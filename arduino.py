

import serial


class Arduino(object):
    def __init__(self, com="COM4", speed="9600"):
        self._connection = None
        self.connected = False
        self._sending = False
        self.response = None
        self.callback = None
        self._msg_id = 0
        self._com = com
        self._speed = speed

    def connect(self):
        try:
            self._connection = serial.Serial(self._com, self._speed, timeout=0.2)
        except serial.SerialException:
            print('Arduino not found.')

        # Wait for connect from arduino
        if self._connection is not None:
            while True:
                data = self._connection.readline()
                if len(data) > 3:
                    print(f'rawData {data.decode()}')
                if data.decode() == "setup":
                    self.connected = True
                    break

    def get_msg_id(self):
        self._msg_id += 1
        return str(self._msg_id)

    def send_msg(self, msg_in):
        msg = self.get_msg_id() + ":" + msg_in
        if self.connected:
            print(f"Sending message[{msg}]")
            self._sending = True
            self._connection.write(bytes(msg, encoding="utf8"))
            while True:
                data = self._connection.readline().decode()
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