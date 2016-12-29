.. vim: set fileencoding=utf-8 :

.. _bob.db.ijba:

=========================================
 JANUS Database Identification Protocols
=========================================

This package contains the access API and descriptions for the JANUS database
(also known as IARPA Janus Benchmark A -- IJB-A).  The actual raw data can be
downloaded from the original web page:
http://www.nist.gov/itl/iad/ig/facechallenges.cfm (note that not everyone might
be eligible for downloading the data).

Included in the database, there are list files defining identification (search)
and verification (compare) experiments.

For the identification, ten different splits are provided, each of which is
split into a training set, a gallery of 167 or 168 subjects and an according
probe set.  Similarly, for the verification, each split contains a training set
(same as for the identification) and a file defining a set of comparisons for
each template.  It is important to highlight that each template has their set
of probes.

The JANUS database is a quite difficult face recognition database.  The raw
data contain images or video frames in different qualities, and many of the
faces are non-frontal.  For each subject, several
:py:class:`bob.db.ijba.Template`'s are defined, where in each Template one or
more images or video frames are combined.  For each subject, one of these
Templates is used to enroll a model, and the remaining Templates are used for
probing.  Hence, this database implements the FileSet protocol, which is
defined in more detail in `bob.db.base <bob.db.base>`.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   guide
   py_api

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
