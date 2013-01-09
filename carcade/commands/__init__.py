from argh import ArghParser

from . import init as _init, \
              build as _build, \
              runserver as _runserver


def runserver():
    _runserver.main()


def build():
    _build.main()


def init(project_name):
    _init.main(project_name)


def main():
    parser = ArghParser()
    parser.add_commands([init, build, runserver])
    parser.dispatch(completion=False)  # completion = False to suppress warning
