#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Guenther <Manuel.Guenther@idiap.ch>
# @date:   Mon Dec 10 14:29:51 CET 2012
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
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

"""A few checks for the JANUS database.
"""

import os, sys
import unittest
import bob.db.janus
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
      raise SkipTest("The database file '%s' is not available; did you forget to run 'bob_dbmanage.py %s create' ?" % (dbfile, 'janus'))

  return wrapper


PROTOCOLS = ['split%d' % s for s in range(1,11)]
ALL_PROTOCOLS = ['NoTrain'] + PROTOCOLS

@db_available
def test_clients():
  # Checks the clients
  db = bob.db.janus.Database()

  # The number of groups and protocols
  assert set(db.protocol_names()) == set(ALL_PROTOCOLS)
  assert len(db.groups(protocol='NoTrain')) == 1
  assert all(len(db.groups(protocol=protocol)) == 2 for protocol in PROTOCOLS)

  # test that the expected number of clients/client_ids is returned
  assert all(len(db.clients(protocol=protocol)) == 500 for protocol in ['NoTrain'] + PROTOCOLS[1:])
  assert len(db.clients(protocol=PROTOCOLS[0])) == 499 ## For some reason, client with ID 657 is not part of split1

  assert len(db.client_ids(protocol='NoTrain', groups='world')) == 0
  assert all(len(db.client_ids(protocol=protocol, groups='world')) in (332, 333) for protocol in PROTOCOLS)

  assert len(db.client_ids(protocol='NoTrain', groups='dev')) == 500
  assert all(len(db.client_ids(protocol=protocol, groups='dev')) in (167, 168) for protocol in PROTOCOLS)

  # The number of models and clients are identical (need to be as we have identification protocols)
  assert len(db.model_ids(protocol='NoTrain', groups='dev')) == len(db.client_ids(protocol='NoTrain', groups='dev'))
  assert all(len(db.model_ids(protocol=protocol, groups='dev')) == len(db.client_ids(protocol=protocol, groups='dev')) for protocol in PROTOCOLS)


@db_available
def test_objects():
  # Checks the objects
  db = bob.db.janus.Database()

  # test that the objects() function returns reasonable numbers of files
  assert all(len(db.objects(protocol=protocol)) == 25817 for protocol in ['NoTrain'] + PROTOCOLS[1:])
  assert len(db.objects(protocol=PROTOCOLS[0])) == 25800

  # number of world files for the protocols (cf. the number of lines in the training file lists)
  world_files = [0, 16911, 16358, 17289, 16567, 17058, 17663, 17589, 16373, 17441, 16783]
  assert all(len(db.objects(groups='world', protocol=protocol)) == world_files[i] for i,protocol in enumerate(ALL_PROTOCOLS))

  # enroll files (cf. the number of lines in the gallery file lists)
  enroll_files = [12754, 4276, 4785, 4011, 4460, 4221, 3877, 4152, 4572, 3924, 4333]
  assert all(len(db.objects(groups='dev', purposes='enroll', protocol=protocol)) == enroll_files[i] for i,protocol in enumerate(ALL_PROTOCOLS))

  # probe files; not identical with probe file lists as files are used in several probes
  probe_files = [13064, 4613, 4674, 4517, 4790, 4538, 4278, 4076, 4872, 4452, 4701]
  assert all(len(db.objects(groups='dev', purposes='probe', protocol=protocol)) == probe_files[i] for i,protocol in enumerate(ALL_PROTOCOLS))

  # WARNING! img/9834.JPG is in both gallery and probe of protocol NoTrain
  # hence, enroll_files[0] + probe_files[0] > 25817


@db_available
def test_object_sets():
  # Checks the objects
  db = bob.db.janus.Database()

  # test that the object_sets() function returns reasonable numbers of Template objects
  probe_templates = [5152, 1806, 1798, 1732, 1807, 1766, 1657, 1652, 1883, 1788, 1753]
  assert all(len(db.object_sets(groups='dev', purposes='probe', protocol=protocol)) == probe_templates[i] for i,protocol in enumerate(ALL_PROTOCOLS))


@db_available
def test_annotations():
  # Tests that the annotations are available for all files
  db = bob.db.janus.Database()

  all_keys = set(['topleft', 'size', 'bottomright', 'forehead-visible', 'eyes-visible', 'nose-mouth-visible', 'indoor', 'gender', 'skin-tone', 'age', 'leye', 'reye', 'nose', 'yaw'])

  # we test only one of the protocols
  for protocol in random.sample(ALL_PROTOCOLS, 2):
    files = db.objects(protocol=protocol)
    # ...and some of the files
    for file in random.sample(files, 1000):
      annotations = db.annotations(file)
      assert 'topleft' in annotations and 'size' in annotations and 'bottomright' in annotations, "Annotations '%s' of file '%s' are incomplete" % (annotations, file.path)
      assert len(annotations['topleft']) == 2
      assert len(annotations['bottomright']) == 2
      assert set(annotations.keys()).issubset(all_keys)

@db_available
def test_driver_api():
  # Tests the bob_dbmanage.py driver interface
  from bob.db.base.script.dbmanage import main
  assert main('janus dumplist --self-test'.split()) == 0
  assert main('janus dumplist --group=dev --purpose=probe --template-id=133 --protocol=NoTrain --self-test'.split()) == 0
  assert main('janus checkfiles --self-test'.split()) == 0
  assert main('janus reverse frame/30125_00224 --self-test'.split()) == 0
  assert main('janus path 42 --self-test'.split()) == 0
