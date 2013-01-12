# -*- coding: utf-8 -*-
import os
import time
import glob
import polib

from carcade.core import build
from carcade.utils import sh


def main():
    print 'Build...',

    build_dir = '.build-%s' % int(time.time())
    sh('cp -r ./static ./%s' % build_dir)

    for translation in glob.glob('translations/*.po'):
        language, ext = os.path.splitext(os.path.basename(translation))
        polib.pofile(translation).save_as_mofile('translations/.%s.mo' % language)

    build(build_dir)
    prev_build_dir = os.path.exists('./www') and os.readlink('./www')

    # Link new build to ./www
    sh('ln -snf ./%s ./www' % build_dir)

    # Remove old build if exists
    if prev_build_dir:
        sh('rm -rf %s' % prev_build_dir)

    print 'Done.'
