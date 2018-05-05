#!/usr/bin/env python3

from setuptools import setup

setup(
    name='Frigid Page Manager',
    version='0.1',
    description='Anonymous page repost manager',
    url='http://github.com/storborg/funniest',
    author='Frigid Engo Boii',
    author_email='flyingcircus@example.com',
    license='MIT',
    packages=['fpm'],
    install_requires=[
        'requests',
        'google-api-python-client',
        'pytz', 'tzlocal',
        'xxhash'
      
    ],
    entry_points = {
        'console_scripts': ['fpm_cli=fpm.cli.crap_line_interface:crap_line_interface']
    },
    zip_safe=False
)


