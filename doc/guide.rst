.. vim: set fileencoding=utf-8 :
.. @author: Manuel Gunther <mgunther@vast.uccs.edu>
.. @date:   Fri Sep 11 14:53:52 MDT 2015

==============
 User's Guide
==============



The Database Interface
----------------------

The :py:class:`bob.db.ijba.Database` complies with the standard biometric verification database as described in :ref:`commons`, implementing the interface :py:class:`bob.db.verification.utils.SQLiteDatabase`.


The Database Protocols
----------------------

In total we provide 20 evaluation protocols, the first 10 represents the search protocols and the last 10 are the comparison protocols (one for each split).


Search protocols
================


The search protocol measures the accuracy of open-set and closed-set search on the gallery templates using probe templates. 
To prevent an algorithm from leveraging apriori knowledge that every probe subject contains a mate in the gallery, 55 randomly selected subjects in each split have templates/imagery removed from the gallery set. 
Every probe template in a given split (regardless of whether or not the gallery contains the probe’s mated templates) are to be searched against the set of gallery templates. **ADD REF**.

The clients of a split as split in two groups called ```world``` and ```dev```.
With that division the defined protocols are called ```search_splitN``` with ```N=[1-10]```.

To fetch the object files using some protocol (let's say the first split), use the following piece of code:

.. code-block:: python

   >>> import bob.db.ijba
   >>> db = bob.db.ijba.Database()   
   >>> #Training set
   >>> train      = db.objects(protocol='search_split1', groups='world')   
   >>>
   >>> # Fetching the gallery of the development set
   >>> dev_enroll = db.objects(protocol='search_split1', groups='dev', purposes="enroll")
   >>> # Fetching the probes of the development set
   >>> dev_probe = db.objects(protocol='search_split1', groups='dev', purposes="probe")
   >>> 


.. warning::  
  
  Not all files in the **training set** (world) contains the full annotations (eyes, nose and mouth positions, gender and so on).
  This API only consider the files with the full annotations.
  It is important to emphasize this design decision does not impact in the compatibility with the original protocol.



Comparison protocols
====================


How to build the database
-------------------------


.. todo::
   Explain the particularities of the :py:class:`bob.db.janus.Database` database.


.. _bob: https://www.idiap.ch/software/bob
