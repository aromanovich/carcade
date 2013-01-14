import os
import sys

from carcade import global_settings


class Settings(object):
    def __init__(self):
        for setting in dir(global_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(global_settings, setting))
    
    def configure(self, settings_module):
        try:
            module = __import__(settings_module)
        except ImportError as e:
            raise ImportError("Could not import settings '%s' (Is it on sys.path?): %s" % (settings_module, e))

        for setting in dir(module):
            if setting == setting.upper():
                setattr(self, setting, getattr(module, setting))


settings = Settings()
