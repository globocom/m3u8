import os
from setuptools import setup

long_description = None
if os.path.exists("README.rst"):
    long_description = open("README.rst").read()

setup(
    name="m3u8",
    author='Globo.com',
    version="0.1.4",
    zip_safe=False,
    packages=["m3u8"],
    url="https://github.com/globocom/m3u8",
    description="Python m3u8 parser",
    long_description=long_description
    )
