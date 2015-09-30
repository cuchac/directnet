from distutils.core import setup

import directnet

setup(
    name='directnet',
    version=directnet.version,
    packages=['directnet'],
    url='',
    license='',
    author='Cuchac',
    author_email='cuchac@email.cz',
    description='DirectNET communication library',
    requires=['pyserial',]
)
