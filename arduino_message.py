import threading


class ArduinoMessage(object):
    def __init__(self, arduino, message=None, message_id=0, callback=None):
        self._arduino = arduino
        self._message = message
        self._message_id = str(message_id)
        self._callback = callback
        self._response = None

    def check(self):
        data = self._arduino.readline()
        data_string = data.decode()
        if len(data_string) > 0:
            print(f'rawData{data_string}')

        datas = data_string.split(":")
        if len(datas) > 0 and self.message_id == datas[0]:
            if len(datas) > 1 and "complete" == datas[1]:
                if len(datas) > 2:
                    self.response = datas[2]
                if self.callback is not None:
                    self.callback()
            threading.Timer(0.1, self.check)

    def send(self):
        msg = self.message_id + ":" + self.message
        if self._arduino is not None:
            self._arduino.write(bytes(msg, encoding="utf8"))
            threading.Timer(0.1, self.check)
        else:
            print("No arduino found.  Message will not be sent.")

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, val):
        self._message = val

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, val):
        self._callback = val

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, val):
        self._response = val

    @property
    def message_id(self):
        return self._message_id

    @message_id.setter
    def message_id(self, val):
        self._message_id = val
