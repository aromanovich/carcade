import os
import time
import shutil

from carcade.core import build
from carcade.utils import sh


def main(target_dir, atomic=False):
    print 'Build...',

    current_dir = os.getcwd()
    if not atomic:
        build_dir = os.path.join(current_dir, target_dir)
        if os.path.exists(build_dir) and os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
        build(current_dir, build_dir)

    else:
        build_dir = os.path.join(current_dir, '.build-%s' % int(time.time()))
        build(current_dir, build_dir)

        prev_build_dir = None
        if os.path.exists(target_dir):
            if os.path.islink(target_dir):
                prev_build_dir = os.readlink(target_dir)
            else:
                shutil.rmtree(target_dir)

        # Link new build to ./www
        sh('ln -snf %s %s' % (build_dir, target_dir))

        # Remove old build if exists
        if prev_build_dir:
            shutil.rmtree(prev_build_dir)

    print 'Done.'
