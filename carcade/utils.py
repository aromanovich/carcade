import subprocess
import glob
import os
import codecs

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


def yield_files(directory, extension):
    pattern = '*'
    if not extension.startswith('.'):
        pattern += '.'
    pattern += extension

    for filename in glob.glob(os.path.join(directory, pattern)):
        with codecs.open(filename, 'r', 'utf-8') as file_:
            yield file_
