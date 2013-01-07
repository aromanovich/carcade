from setuptools import setup


setup(
    name='carcade',
    version='0.0.1',
    description='Static site generator',
    url='https://github.com/aromanovich/carcade',

    author='Anton Romanovich',
    author_email='anthony.romanovich@gmail.com',

    packages=['carcade'],
    include_package_data = True,
    package_data = {
        '': ['template/*/.gitkeep'],
    },

    scripts = [
        'carcade/commands/init.py',
        'carcade/commands/build.py',
        'carcade/commands/runserver.py',
    ],

    install_requires=[
        'distribute',
        'Jinja2==2.6',
        'watchdog==0.6.0',
        'Markdown==2.2.1',
        'PyYAML==3.10',
    ],
)
