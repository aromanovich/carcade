import os
import sys
import time
import shutil
import traceback
import os.path

import argh

import carcade
from carcade import server
from carcade.conf import settings
from carcade.i18n import extract_translations
from carcade.environments import create_jinja2_env
from carcade.core import build as _build
from carcade.utils import sh


def init(project):
    """Creates default directory structure in the `project` directory
    (it must not exist)."""
    carcade_path = os.path.dirname(os.path.abspath(carcade.__file__))
    template_path = os.path.join(carcade_path, 'template')
    destination_path = os.path.join(os.getcwd(), project)
    if os.path.exists(destination_path):
        print 'Error: path %s already exists!'
    else:
        shutil.copytree(template_path, destination_path)
        print '%s successfully initialized.'


def build(to='www', atomically=False):
    """Builds the site."""
    settings.configure('settings')

    print 'Build...'
    try:
        current_dir = os.getcwd()

        if not atomically:
            build_dir = os.path.join(current_dir, to)
            if os.path.exists(build_dir):
                if os.path.islink(build_dir):
                    os.unlink(build_dir)
                elif os.path.isdir(build_dir):
                    shutil.rmtree(build_dir)

            _build(current_dir, build_dir)
        else:
            timestamp = int(time.time())
            build_dir = os.path.join(current_dir, '.build-%s' % timestamp)

            _build(current_dir, build_dir)

            target_dir = os.path.join(current_dir, to)
            previous_build_dir = None
            if os.path.exists(target_dir):
                if os.path.islink(target_dir):
                    # If `target_dir` is the result of atomic build
                    previous_build_dir = os.readlink(target_dir)
                else:
                    shutil.rmtree(target_dir)

            # Link new build to ./www
            # Is it really atomically? Consider using `mv -T`:
            # http://rcrowley.org/2010/01/06/things-unix-can-do-atomically.html
            sh('ln -snf %s %s' % (build_dir, target_dir))

            # Remove old build if exists
            if previous_build_dir:
                shutil.rmtree(previous_build_dir)
    except:
        print 'Ooops...'
        traceback.print_exc()
        return 1
    else:
        print 'Done.'


def runserver(host='localhost', port=8000):
    """Fires up a server that will host `www` directory, monitor
    the changes and regenerate the site automatically.
    """
    settings.configure('settings')
    server.serve(host=host, port=port)


def extract_messages(to='translations/messages.pot'):
    """Extracts localizable strings from the templates."""
    settings.configure('settings')
    jinja2_env = create_jinja2_env()
    extract_translations(jinja2_env, to)


def main():
    sys.path.append(os.getcwd())
    parser = argh.ArghParser()
    parser.add_commands([
        init,
        build,
        runserver,
        extract_messages,
    ])
    parser.dispatch()
