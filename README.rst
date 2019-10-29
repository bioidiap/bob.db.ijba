.. vim: set fileencoding=utf-8 :
.. Thu 18 Aug 13:44:41 CEST 2016

.. image:: http://img.shields.io/badge/docs-v2.1.4-yellow.svg
   :target: https://www.idiap.ch/software/bob/docs/bob/bob.db.ijba/v2.1.4/index.html
.. image:: http://img.shields.io/badge/docs-latest-orange.svg
   :target: https://www.idiap.ch/software/bob/docs/bob/bob.db.ijba/master/index.html
.. image:: https://gitlab.idiap.ch/bob/bob.db.ijba/badges/v2.1.4/build.svg
   :target: https://gitlab.idiap.ch/bob/bob.db.ijba/commits/v2.1.4
.. image:: https://gitlab.idiap.ch/bob/bob.db.ijba/badges/v2.1.4/coverage.svg
   :target: https://gitlab.idiap.ch/bob/bob.db.ijba/commits/v2.1.4
.. image:: https://img.shields.io/badge/gitlab-project-0000c0.svg
   :target: https://gitlab.idiap.ch/bob/bob.db.ijba
.. image:: http://img.shields.io/pypi/v/bob.db.ijba.svg
   :target: https://pypi.python.org/pypi/bob.db.ijba


==================================
 IJB-A Database Interface for Bob
==================================

This package is part of the signal-processing and machine learning toolbox
Bob_.  This package contains an interface for the evaluation protocols of the
`IARPA Janus Benchmark A (IJB-A) database`_ and does not contain the original
image data for the database.  The original data should be obtained using the
link above.

The IJB-A database is a mixture of frontal and non-frontal images and videos
(provided as single frames) from 500 different identities.  In many of the
images and video frames, there are several people visible, but only the ones
that are annotated with a bounding box should be taken into consideration.  For
both model enrollment as well as for probing, images and video frames of one
person are combined into so-called Templates.

The database is divided in 10 splits each defining training, enrollment and
probe data.

This package implements the database interface including all its
particularities:

- First, it implements the FileSet protocol, since for some probes, several
  files (a mixture of images and video frames) are defined. In the
  Database.object_sets() function, FileSet objects are only returned for probe
  purposes.
- Second, some images contain several identities. Therefore, every physical
  image file can be stored in several File objects. Also, the File.make_path()
  function can create two different styles of file names: the original file
  name (to read original images), or a unique filename (to define a unique name
  for each extracted face).
- Third, the Templates with the same template_id might differ between the
  protocols, so that the Template.template_id is **not** unique. On the other
  hand, the Template.id is used as a unique key to query the SQL database.


Installation
------------

Complete Bob's `installation`_ instructions. Then, to install this package,
run::

  $ conda install bob.db.ijba


Contact
-------

For questions or reporting issues to this software package, contact our
development `mailing list`_.


.. Place your references here:
.. _bob: https://www.idiap.ch/software/bob
.. _installation: https://www.idiap.ch/software/bob/install
.. _mailing list: https://www.idiap.ch/software/bob/discuss
.. _iarpa janus benchmark a (ijb-a) database: http://www.nist.gov/itl/iad/ig/ijba_request.cfm
