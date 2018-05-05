class GraphAuthError(RuntimeError):
    def __init__(self, data, message):
        self.data = data
        self.message = message

class GraphUnknownError(RuntimeError):
    def __init__(self, data, message):
        self.data = data
        self.message = message
