#!/usr/bin/env python
from __future__ import unicode_literals
from setuptools import setup, find_packages

#Use "source/scripts/pip_install_dependencies.py" to install dependencies

tests_requires = [
    'pytest-mock == 1.6.2',
    'pytest-runner == 2.11.1',
    'pytest == 3.2.1'
]

setup(
    name='efs-backup-solution',
    version='1.0.0',
    description='AWS EFS to AWS EFS backup',
    author='Lalit G.',
    url='https://github.com/awslabs/aws-efs-backup',
    packages=find_packages(exclude=("tests", "tests.*")),
    license="Amazon",
    zip_safe=False,
    test_suite="tests",
    tests_require=tests_requires,
    setup_requires=['pytest-runner'],
    classifiers=[
        "Programming Language :: Python :: 3.7"
    ],
)