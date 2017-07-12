#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [i.strip() for i in open('requirements.txt').readlines()]

setup(
    name='biometalib',
    version='0.0.3',
    description="A set of helper functions for working with biological metadata from the SRA.",
    long_description=readme,
    author="Justin Fear",
    author_email='justin.m.fear@gmail.com',
    url='https://github.com/jfear/biometalib',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    entry_points={
        'console_scripts':
        [
            'initialize_biometa = biometalib.utils.initialize_biometa:main',
            'attribute_selector = biometalib.utils.attribute_selector:main',
        ],
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
