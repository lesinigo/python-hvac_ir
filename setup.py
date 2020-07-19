#!/usr/bin/env python3
"""Setuptools configuration file"""

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='hvac_ir',
    version='0.1.0',
    description='library to encode and decode IR codes for HVAC systems',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Luca Lesinigo',
    author_email='luca@lesinigo.it',
    license='GPL v2',
    url='https://github.com/lesinigo/python-hvac_ir',
    platforms=['any'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Home Automation",
    ],
    packages=find_packages(),
    python_requires='>=3.7',
)
