from os.path import abspath, dirname, exists, join

from setuptools import setup

long_description = None
if exists("README.md"):
    with open("README.md") as file:
        long_description = file.read()

install_reqs = [
    req for req in open(abspath(join(dirname(__file__), "requirements.txt")))
]

setup(
    name="m3u8",
    author="Globo.com",
    version="5.2.0",
    license="MIT",
    zip_safe=False,
    include_package_data=True,
    install_requires=install_reqs,
    packages=["m3u8"],
    url="https://github.com/globocom/m3u8",
    description="Python m3u8 parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
)
