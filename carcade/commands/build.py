# -*- coding: utf-8 -*-
import os
import time
import shutil

from carcade.core import build
from carcade.utils import sh


def main():
    print 'Build...',

    build_dir = '.build-%s' % int(time.time())
    shutil.copytree('static', build_dir)

    build(build_dir)
    prev_build_dir = os.path.exists('www') and os.readlink('www')

    # Link new build to ./www
    sh('ln -snf ./%s ./www' % build_dir)
    # os.symlink(build_dir, 'www')  There is no -f key :(

    # Remove old build if exists
    if prev_build_dir:
        shutil.rmtree(prev_build_dir)

    print 'Done.'
