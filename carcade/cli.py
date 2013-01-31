import os
import sys

from argh import ArghParser

from carcade.conf import settings
from carcade.commands import init as _init, \
                             build as _build, \
                             runserver as _runserver, \
                             extract as _extract


def runserver():
    settings.configure('carcade_settings')
    _runserver.main()


def build(build_dir='www', atomic=True):
    settings.configure('carcade_settings')
    _build.main(build_dir, atomic=atomic)


def init(project_name):
    _init.main(project_name)


def extract_translations():
    settings.configure('carcade_settings')
    _extract.main()


def main():
    sys.path.append(os.getcwd())

    parser = ArghParser()
    parser.add_commands([init, build, runserver, extract_translations])
    parser.dispatch(completion=False)  # completion = False to suppress warning
