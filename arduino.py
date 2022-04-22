import serial
from time import sleep


class Arduino(object):
    def __init__(self, com="COM3", speed="9600"):
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
            self.serial = serial.Serial(self._com, 9600, timeout=0.2)
        except serial.SerialException:
            print('Arduino not found.')
            raise Exception('Failed to connect')

        self.connected = True
        """
        # Wait for connect from arduino
        if self.serial is not None:
            cnt = 0
            while not self.connected:
                data = self.serial.readline()
                if len(data) > 0:
                    s = data.decode().rstrip()
                    print(f'rawData [{s}]')
                    if data == "setup" or data == 'ping':
                        self.connected = True
                if cnt > 10:
                    r = self.serial.write(bytes('message', encoding='utf-8'))
                    print(f'written [{r}]')
                    self.serial.flush()
                    sleep(0.1)
                    cnt = 0
                cnt += 1
                sleep(0.1)
            print("connected")
        """

    def close(self):
        if self.serial is not None:
            self.serial.close()
        self.connected = False

    def get_msg_id(self):
        self._msg_id += 1
        return self._msg_id

    def send_msg_new(self, a, d=0, v=0):
        if self.connected:
            m = self.get_msg_id() + 512     # MSG ID 10 bits
            m = m << 4                      # Action 4 bits
            m += a                          # Action
            m = m << 2                      # Direction 2 bits
            m += d                          # Direction
            m = m << 16                     # Value 16 bits
            m += v                          # Value

            self.serial.write(bytes(str(m), encoding='utf-8'))

            while True:
                data = self.serial.readline()
                if data:
                    res = int(data)
                    msg_id = res & 0x7c0
                    msg_id = msg_id >> 6
                    found = msg_id == self._msg_id
                    success = res & 0x003f == 1
                    if found:
                        print(msg_id, success)
                        break

    def send_msg(self, msg_in):
        if self.connected:
            msg = str(self.get_msg_id()) + ":" + msg_in
            print(f"out[{msg}]")
            msg += ":end"
            self._sending = True
            self.serial.write(bytes(msg, encoding="utf8"))
            while True:
                data = self.serial.readline()
                s_data = data.decode().rstrip()
                if len(s_data) > 0:
                    s_data = s_data.rstrip(':end')
                    print(f'in[{s_data}]')

                datas = s_data.split(":")
                if len(datas) > 0 and str(self._msg_id) == datas[0]:
                    self.response = s_data
                    if datas[-1] == 1:
                        if self.callback is not None:
                            self.callback()
                    else:
                        self.send_msg(msg_in)
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
