.. vim: set fileencoding=utf-8 :
.. @author: Manuel Gunther <mgunther@vast.uccs.edu>
.. @date:   Tue Sep  8 15:05:38 MDT 2015


.. image:: http://img.shields.io/badge/docs-stable-yellow.png
   :target: http://pythonhosted.org/bob.db.ijba/index.html
.. image:: http://img.shields.io/badge/docs-latest-orange.png
   :target: https://www.idiap.ch/software/bob/docs/latest/bioidiap/bob.db.ijba/master/index.html
.. image:: https://travis-ci.org/bioidiap/bob.db.ijba.svg?branch=v2.0.0
   :target: https://travis-ci.org/bioidiap/bob.db.ijba
.. image:: https://coveralls.io/repos/bioidiap/bob.db.ijba/badge.png
   :target: https://coveralls.io/r/bioidiap/bob.db.ijba
.. image:: https://img.shields.io/badge/github-master-0000c0.png
   :target: https://github.com/bioidiap/bob.db.ijba/tree/master
.. image:: http://img.shields.io/pypi/v/bob.db.ijba.png
   :target: https://pypi.python.org/pypi/bob.db.ijba
.. image:: http://img.shields.io/pypi/dm/bob.db.ijba.png
   :target: https://pypi.python.org/pypi/bob.db.ijba
.. image:: https://img.shields.io/badge/original-data--files-a000a0.png
   :target: http://www.nist.gov/itl/iad/ig/ijba_request.cfm


==================================
 IJB-A Database Interface for Bob
==================================

This package contains an interface for the evaluation protocols of the *IARPA Janus Benchmark A* (IJB-A) database.
This package does not contain the original image data for the database.
The original data should be obtained using the link above.

The IJB-A database is a mixture of frontal and non-frontal images and videos (provided as single frames) from 500 different identities.
In many of the images and video frames, there are several people visible, but only the ones that are annotated with a bounding box should be taken into consideration.
For both model enrollment as well as for probing, images and video frames of one person are combined into so-called Templates.

The database is divided in 10 splits each defining training, enrollment and probe data.

This package implements the database interface including all its particularities:

- First, it implements the FileSet protocol, since for some probes, several files (a mixture of images and video frames) are defined.
  In the Database.object_sets() function, FileSet objects are only returned for probe purposes.
- Second, some images contain several identities. Therefore, every physical image file can be stored in several File objects.
  Also, the File.make_path() function can create two different styles of file names: the original file name (to read original images), or a unique filename (to define a unique name for each extracted face).
- Third, the Templates with the same template_id might differ between the protocols, so that the Template.template_id is **not** unique.
  On the other hand, the Template.id is used as a unique key to query the SQL database.


Installation
------------
To install this package -- alone or together with other `Packages of Bob <https://github.com/idiap/bob/wiki/Packages>`_ -- please read the `Installation Instructions <https://github.com/idiap/bob/wiki/Installation>`_.
For Bob_ to be able to work properly, some dependent packages are required to be installed.
Please make sure that you have read the `Dependencies <https://github.com/idiap/bob/wiki/Dependencies>`_ for your operating system.

Documentation
-------------
For further documentation on this package, please read the `Stable Version <http://pythonhosted.org/bob.db.janus/index.html>`_ or the `Latest Version <https://www.idiap.ch/software/bob/docs/latest/bioidiap/bob.db.janus/master/index.html>`_ of the documentation.
For a list of tutorials on this or the other packages ob Bob_, or information on submitting issues, asking questions and starting discussions, please visit its website.

.. _bob: https://www.idiap.ch/software/bob
