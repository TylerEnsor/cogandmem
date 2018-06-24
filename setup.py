import os
from setuptools import setup
from io import open

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding = "utf-8") as f:
    long_description_string = f.read()

setup(
    name = "cogandmem",
    version = "0.1.0",
    description = "Package for running memory experiments",
    long_description = long_description_string,
    long_description_content_type = "text/markdown",
    url = "https://github.com/TylerEnsor/cogandmem",
    author = "Tyler M. Ensor",
    author_email = "tyler.ensor@mun.ca",
    classifiers = [
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 2",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License"
    ],
    keywords = "psychology experiment memory cognition",
    packages = ["cogandmem"],
    install_requires = [
        "numpy >= 1.7.0",
        "pygame"
    ],
    include_package_data = True
)
