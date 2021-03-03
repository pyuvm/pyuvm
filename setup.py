# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages



readme = """
# Description

**pyuvm** implements the most often-used parts of the UVM while taking advantage of the fact that Python does not have strict typing and does not require parameterized classes. The project refactors pieces of the UVM that were either overly complicated due to typing or legacy code.

The code is based in the IEEE 1800.2 specification and most classes and methods have the specification references in the comments.
"""

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pyuvm',
    version='1.0.1',
    description='Python Implementation of Universal Verification Methodology',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Ray Salemi',
    author_email='ray@raysalemi.com',
    url='https://github.com/pyuvm/pyuvm',
    license='Apache License',
    packages=find_packages(exclude=('tests', 'docs', 'examples', 'scratch'))
)

