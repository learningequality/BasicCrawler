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
    "requests>=2.22.0",
    "cachecontrol>=0.12.6",
    "lockfile>=0.12.2",
    "beautifulsoup4>=4.6.3",
    "html5lib>=1.0.1",
    "youtube_dl>=2020.6.6",
]

test_requirements = [
    'pytest>=5.3.5',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
