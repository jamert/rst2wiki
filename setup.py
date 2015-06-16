from setuptools import setup
import os
# dirty hack for locale bug (for docutils)
os.environ['LC_CTYPE'] = 'en_US.UTF8'


setup(
    name='rst2wiki',
    version='0.1.2',
    description='Tool to push reST docs to confluence',
    author='Artem Dayneko',
    author_email='dayneko.ab@gmail.com',
    url='https://github.com/jamert/rst2wiki',
    py_modules=['rst2wiki'],
    install_requires=[
        'requests==2.6.0',
        'docutils==0.12',
        'Pygments==2.0.2',
        'rst2confluence==0.5.1',
    ],
    entry_points='''
        [console_scripts]
        rst2wiki = rst2wiki:main
    '''
)
