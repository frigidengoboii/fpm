#!/usr/bin/env python3

from setuptools import setup

setup(
    name='Frigid Page Manager',
    version='0.1',
    description='Anonymous page repost manager',
    url='https://github.com/frigidengoboii/fpm',
    author='Frigid Engo Boii',
    author_email='frigidengoboii@gmail.com',
    license='CC-BY-SA',
    packages=['fpm'],
    install_requires=[
        'requests',
        'google-api-python-client',
        'pytz', 'tzlocal',
        'xxhash',
        'selenium'
      
    ],
    entry_points = {
        'console_scripts': ['fpm_cli=fpm.cli.crap_line_interface:crap_line_interface']
    },
    zip_safe=False
)


