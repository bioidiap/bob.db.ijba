#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# author: Manuel Guenther <manuel.guenther@idiap.ch>
# date:   Wed Feb 13 12:35:29 CET 2013

from setuptools import setup, find_packages, dist
dist.Distribution(dict(setup_requires=['bob.extension']))

from bob.extension.utils import load_requirements
install_requires = load_requirements()

# Define package version
version = open("version.txt").read().rstrip()

# The only thing we do in this file is to call the setup() function with all
# parameters that define our package.
setup(

    name='bob.db.ijba',
    version=version,
    description='IJB-A Database Access API for Bob',
    url='http://github.com/bioidiap/bob.db.ijba',
    license='GPLv3',
    author='Tiago de Freitas Pereira',
    author_email='tiago.pereira@idiap.ch',
    long_description=open('README.rst').read(),

    # This line is required for any distutils based packaging.
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    install_requires = install_requires,

    entry_points = {
      # bob database declaration
      'bob.db': [
        'ijba = bob.db.ijba.driver:Interface',
      ],

      # scripts should be declared using this entry:
      'console_scripts' : [
        'evaluate_ijba.py     = bob.db.ijba.scripts.evaluate_ijba:main',
        'score_generation.py  = bob.db.ijba.scripts.score_generation:main'
      ],

    },

    classifiers = [
      'Framework :: Bob',
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      'Natural Language :: English',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Topic :: Scientific/Engineering :: Artificial Intelligence',
      'Topic :: Database :: Front-Ends',
    ],
)
