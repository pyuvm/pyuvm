# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pyuvm',
    version='0.1.0',
    description='Python Implementation of Universal Verification Methodology',
    long_description=readme,
    author='Ray Salemi',
    author_email='ray@raysalemi.com',
    url='https://rayboston@bitbucket.org/rayboston/pyuvm.git',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

