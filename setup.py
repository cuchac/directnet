from setuptools import setup

import directnet

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='directnet',
    version=directnet.version,
    packages=('directnet',),
    url='https://github.com/cuchac/directnet',
    license='LGPL v2',
    author='Cuchac',
    long_description=long_description,
    author_email='cuchac@email.cz',
    description='DirectNET communication library',
    install_requires=('pyserial', 'six'),
)
