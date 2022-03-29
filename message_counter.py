

class MessageCounter(object):
    def __init__(self, initial=0):
        self._count = initial

    def get_next(self):
        self._count += 1
        return self._count

    def current(self):
        return self._count
