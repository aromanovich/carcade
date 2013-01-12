from setuptools import setup


setup(
    name='carcade',
    version='0.0.3',
    description='Static site generator',
    url='https://github.com/aromanovich/carcade',
    author='Anton Romanovich',
    author_email='anthony.romanovich@gmail.com',
    packages=['carcade', 'carcade.commands'],
    package_dir={'carcade': 'carcade'},
    package_data={'carcade': ['template/*/.gitkeep']},
    entry_points={
        'console_scripts': [
            'carcade = carcade.commands:main',
        ],
    },
    install_requires=[
        'argh==0.21.2',
        'Jinja2==2.6',
        'polib==1.0.2',
        'webassets==0.8',
        'Markdown==2.2.1',
        'PyYAML==3.10',
        'watchdog==0.6.0',
    ],
)
