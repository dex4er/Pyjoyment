class Value:
    value = None

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        return self.value

    def inc(self):
        self.value += 1
        return self.value
