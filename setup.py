from distutils.core import setup

import directnet

setup(
    name='directnet',
    version=directnet.version,
    packages=['directnet'],
    url='https://github.com/cuchac/directnet',
    license='LGPL v2',
    author='Cuchac',
    author_email='cuchac@email.cz',
    description='DirectNET communication library',
    requires=['pyserial',]
)
