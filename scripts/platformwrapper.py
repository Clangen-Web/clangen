import platform


class localStorage:
    
    def __init__(self):
        pass

    @staticmethod
    def getItem(key):
        return platform.window.localStorage.getItem(key) # pylint: disable=no-member
    @staticmethod
    def setItem(key, value):
        return platform.window.localStorage.setItem(key, value) # pylint: disable=no-member