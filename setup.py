# -*- coding: utf-8 -*-
import io
import re


from setuptools import find_packages
from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

with io.open("libvirtapi/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setup(
    name="libvirtapi",
    version=version,
    url="",
    author="coretek",
    author_email='admin@coretek.com',
    description="libvirt api",
    long_description=readme,
    packages=find_packages(),
    python_requires=">=3.6.6",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "start-libvirtapi = libvirtapi.app:main"
        ]
    }

)
