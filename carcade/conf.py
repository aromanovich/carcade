from carcade import global_settings


class Settings(object):
    """Class to handle settings.
    After initialization it contains default settings loaded from
    :module:`global_settings`.

    Note: settings are variables which names are all uppercase.
    """

    def __init__(self):
        self._load_settings(global_settings)

    def _load_settings(self, obj):
        for setting in dir(obj):
            if setting == setting.upper():
                setattr(self, setting, getattr(obj, setting))
    
    def configure(self, settings_module):
        """Loads settings from `settings_module`.

        :type settings_module: :class:`str`
        """
        try:
            module = __import__(settings_module)
            reload(module)
        except ImportError as e:
            raise ImportError(
                'Could not import settings \'%s\': %s' % (settings_module, e))
        
        self._load_settings(module)


settings = Settings()
