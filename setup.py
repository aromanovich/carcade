from setuptools import setup

# http://bugs.python.org/issue15881#msg170215 workaround:
try:
    import multiprocessing
except ImportError:
    pass


VERSION = '0.1'


setup(
    name='Carcade',
    version=VERSION,
    description='Static site generator powered by Jinja2.',
    long_description=open('README.rst').read(),
    url='https://github.com/aromanovich/carcade',
    author='Anton Romanovich',
    author_email='anthony.romanovich@gmail.com',
    packages=['carcade'],
    package_dir={'carcade': 'carcade'},
    package_data={'carcade': ['template/*/.gitkeep']},
    entry_points={
        'console_scripts': [
            'carcade = carcade.cli:main',
        ],
    },
    install_requires=[
        'argh>=0.21.2',
        'argcomplete>=0.3.7',
        'Jinja2>=2.6',
        'polib>=1.0.2',
        'webassets>=0.8',
        'Markdown>=2.2.1',
        'PyYAML>=3.10',
        'watchdog>=0.6.0',
    ],
    license='BSD',
    tests_require=['nose'],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Operating System :: POSIX',
        'Operating System :: Unix',
    ],
)
