# pylint: disable=no-member
import platform
import asyncio


class localStorage:
    
    def __init__(self):
        pass

    @staticmethod
    def getItem(key):
        return platform.window.localStorage.getItem(key)
    @staticmethod
    def setItem(key, value):
        return platform.window.localStorage.setItem(key, value)
    

class localForage:

    def __init__(self):
        pass

    @staticmethod
    async def getItem(key):
        promise = platform.window.localforage.getItem(key)
        val = None
        def wait(value):
            val = value
        promise.then(wait)
        while val is None:
            await asyncio.sleep(0.5)
        return val


    @staticmethod
    def setItem(key, value):
        platform.window.localforage.setItem(key, value)