#!/usr/bin/env python3
from distutils.core import setup

setup(
    name='ansible-tty',
    description='Initiate a session ssh over ansible-inventory',
    author='Alex Left',
    author_email='alejandro.izquierdo.b@gmail.com',
    url='https://github.com/alex-left/ansible-tty',
    version='0.1',
    scripts=['ansible-tty'],
    license='GPL-v3',
    long_description=open('README.md').read(),
)
