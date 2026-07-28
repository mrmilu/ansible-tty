#!/usr/bin/env python3
from distutils.core import setup

setup(
    name='ansible-tty',
    description='Initiate an ssh session over ansible-inventory',
    author='Iker Blanco',
    author_email='iker.blanco@mrmilu.com',
    url='https://github.com/mrmilu/ansible-tty',
    version='0.9.2',
    scripts=['ansible-tty', 'inventory/sentinel_inventory.py'],
    install_requires=["prettytable", "boto3"],
    license='GPL-v3',
    long_description=open('README.md').read(),
)
