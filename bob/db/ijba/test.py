#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Gunther <mgunther@vast.uccs.edu>
# @date:   Fri Sep 11 14:53:52 MDT 2015
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A few checks for the ijba database.
"""

import os, sys
import unittest
import bob.db.ijba
import random

def db_available(test):
  """Decorator for detecting if the database file is available"""
  from bob.io.base.test_utils import datafile
  from nose.plugins.skip import SkipTest
  import functools

  @functools.wraps(test)
  def wrapper(*args, **kwargs):
    dbfile = datafile("db.sql3", __name__, None)
    if os.path.exists(dbfile):
      return test(*args, **kwargs)
    else:
      raise SkipTest("The database file '%s' is not available; did you forget to run 'bob_dbmanage.py %s create' ?" % (dbfile, 'ijba'))

  return wrapper


SEARCH_PROTOCOLS     = ['search_split%d' % s for s in range(1,11)]
COMPARISON_PROTOCOLS = ['compare_split%d' % s for s in range(1,11)]
PROTOCOLS            = SEARCH_PROTOCOLS + COMPARISON_PROTOCOLS 



@db_available
def test01_search_clients():
  # Checks the clients
  db = bob.db.ijba.Database()

  # The number of groups and protocols  
  assert set(db.protocol_names()) == set(PROTOCOLS)
  assert len(db.groups()) == 2

  # test that the expected number of clients/client_ids is returned
  assert all(len(db.clients(protocol=protocol)) in (495, 494, 493) for protocol in PROTOCOLS) #THERE IS NOT 500 CLIENTS FOR ENROLL AND PROBING 

  #checking clients per group
  assert all(len(db.client_ids(protocol=protocol, groups='world')) in (328, 327) for protocol in PROTOCOLS)
  assert all(len(db.client_ids(protocol=protocol, groups='dev')) in (168, 167, 166) for protocol in PROTOCOLS)

  #The number of models and clients are identical (need to be as we have identification protocols)
  #assert all(len(db.model_ids(protocol=protocol, groups='dev')) == len(db.client_ids(protocol=protocol, groups='dev')) for protocol in PROTOCOLS) #THIS CANNOT BE TESTED, THERE ARE SOME CLIENTS THAT ARE ONLY FOR PROBING 


@db_available
def test02_search_objects():
  # Checks the objects
  db = bob.db.ijba.Database()

  # number of world files for the protocols (cf. the number of lines in the training file lists)
  #world_files = [16911, 16358, 17289, 16567, 17058, 17663, 17589, 16373, 17441, 16783]
  world_files = [15734, 15134, 16042, 15360, 15800, 16323, 16276, 15155, 16149 ,15566]
  #for i in range(10): 
  for i in range(2):
    print("Seach protocol - World set: split {0}".format(i+1))
    assert len(db.objects(groups='world', protocol=SEARCH_PROTOCOLS[i])) == world_files[i]

  # enroll files (cf. the number of lines in the gallery file lists)
  enroll_files = [3000, 3257, 2661, 2894, 2916, 2451, 2908, 3102, 2594, 2847]
  #for i in range(10):
  for i in range(2):    
    print("Seach protocol - Enroll: split {0}".format(i+1))
    assert len(db.objects(groups='dev', purposes='enroll', protocol=SEARCH_PROTOCOLS[i])) == enroll_files[i]

  # probe files; not identical with probe file lists as files are used in several probes
  probe_files = [4068, 4671, 4512, 4788, 4535, 4275, 4074, 4871, 4451, 4700]  
  for i in range(2):  
    print("Seach protocol - Probes: split {0}".format(i+1))
    assert len(db.objects(groups='dev', purposes='probe', protocol=SEARCH_PROTOCOLS[i]))

  # WARNING! img/9834.JPG is in both gallery and probe of protocol NoTrain
  # hence, enroll_files[0] + probe_files[0] > 25817


@db_available
def test03_comparison_objects():
  # Checks the objects
  db = bob.db.ijba.Database()

  # number of world files for the protocols (cf. the number of lines in the training file lists)
  #world_files = [16911, 16358, 17289, 16567, 17058, 17663, 17589, 16373, 17441, 16783]
  world_files = [15734, 15134, 16042, 15360, 15800, 16323, 16276, 15155, 16149 ,15566]
  for i in range(2):
  #for i in range(10):
    print("Compare protocol - World set: split {0}".format(i+1))
    assert len(db.objects(groups='world', protocol=COMPARISON_PROTOCOLS[i])) == world_files[i]
  
  # enroll files (cf. the number of lines in the gallery file lists)
  enroll_files = [4260, 4761, 3995, 4458, 4212, 3875, 4133, 4552, 3922, 4332]
  #for i in range(10):
  for i in range(2):
    print("Enroll protocol - World set: split {0}".format(i+1))
    assert len(db.objects(groups='dev', purposes='enroll', protocol=COMPARISON_PROTOCOLS[i])) == enroll_files[i]



