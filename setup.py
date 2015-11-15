from setuptools import setup
import os
# dirty hack for locale bug (for docutils)
os.environ['LC_CTYPE'] = 'en_US.UTF8'


setup(
    name='rst2wiki',
    version='0.3.0',
    description='Tool to push reST docs to confluence',
    author='Artem Dayneko',
    author_email='dayneko.ab@gmail.com',
    url='https://github.com/jamert/rst2wiki',
    py_modules=['rst2wiki'],
    install_requires=[
        'click',
        'requests',
        'docutils',
        'Pygments',
        'rst2confluence',
    ],
    entry_points='''
        [console_scripts]
        rst2wiki = rst2wiki:main
    ''',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ]
)
