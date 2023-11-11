#!/usr/bin/env python3
from distutils.core import setup

setup(
    name='ansible-tty',
    description='Initiate an ssh session over ansible-inventory',
    author='Iker Blanco',
    author_email='iker.blanco@mrmilu.com',
    url='https://github.com/mrmilu/ansible-tty',
    version='0.6',
    scripts=['ansible-tty'],
    install_requires=["prettytable"],
    license='GPL-v3',
    long_description=open('README.md').read(),
)
