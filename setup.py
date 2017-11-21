#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import basiccrawler

try:
    import pypandoc
    readme = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    readme = open('README.md').read()

requirements = [
    'le_utils>=0.1.3',
    'ricecooker>=0.6.10',
]

setup_requirements = [
    'pytest-runner',
    # TODO(learningequality): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    # TODO: put package test requirements here
]

setup(
    name='basiccrawler',
    version=basiccrawler.__version__,
    description="Basic web crawler that automates website exploration and producing web resource trees.",
    long_description=readme,  #  + '\n\n' + history,
    author="Learning Equality",
    author_email='ivan@learningequalty.org',
    url='https://github.com/learningequality/BasicCrawler',
    packages=find_packages(include=['basiccrawler']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='basiccrawler',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
