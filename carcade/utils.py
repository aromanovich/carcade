import subprocess

from carcade.conf import settings


def sh(shell_command):
    subprocess.call(shell_command, shell=True)


def path_for(name, language=None):
    url = ''
    if language and language != settings.DEFAULT_LANGUAGE:
        url += '%s/' % language
    if name != settings.DEFAULT_PAGE:
        url += '%s/' % name
    return url
