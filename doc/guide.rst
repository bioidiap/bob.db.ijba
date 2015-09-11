.. vim: set fileencoding=utf-8 :
.. @author: Manuel Gunther <mgunther@vast.uccs.edu>
.. @date:   Fri Sep 11 14:53:52 MDT 2015

==============
 User's Guide
==============

This package contains the access API and descriptions for the JANUS CS2 database.
The actual raw data is currently only available for the performers in the JANUS project, but will hopefully be made public after that project finishes.

Included in the database, there are list files defining identification experiments.
The is one protocol, which we call `'NoTrain'`, that consists of a split of the data into a gallery of 500 subjects and a probe group.
Additionally, 10 different splits are provided, each of which is split into a training set, a gallery of 167 or 168 subjects and an according probe set.

The JANUS database is a quite difficult face recognition database.
The raw data contain images or video frames in different qualities, and many of the faces are non-frontal.
For each subject, several :py:class:`bob.db.janus.Template`'s are defined, where in each Template one or more images or video frames are combined.
For each subject, one of these Templates is used to enroll a model, and the remaining Templates are used for probing.
Hence, this database implements the FileSet protocol, which is defined in more detail in :ref:`commons`.


The Database Interface
----------------------

The :py:class:`bob.db.janus.Database` complies with the standard biometric verification database as described in :ref:`commons`, implementing the interface :py:class:`bob.db.verification.utils.SQLiteDatabase`.

.. todo::
   Explain the particularities of the :py:class:`bob.db.janus.Database` database.


.. _bob: https://www.idiap.ch/software/bob
