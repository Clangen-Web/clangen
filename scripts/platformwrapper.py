# pylint: disable=no-member
import platform
from sys import platform as _platform
if _platform == "emscripten":
    is_web = True
else:
    is_web = False
del _platform



def reload():
    if not is_web:
        return
    platform.window.location.reload()

def pushdb():
    if not is_web:
        return
    platform.window.FS.syncfs(False, platform.window.console.log)

def pulldb():
    if not is_web:
        return
    platform.window.FS.syncfs(True, platform.window.console.log)

def _is_web():
    return is_web