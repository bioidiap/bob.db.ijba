#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""A few checks for the ijba database.
"""

import os, sys
import unittest
import bob.db.ijba
import random


SEARCH_PROTOCOLS     = ['search_split%d' % s for s in range(1,11)]
COMPARISON_PROTOCOLS = ['compare_split%d' % s for s in range(1,11)]
PROTOCOLS            = SEARCH_PROTOCOLS + COMPARISON_PROTOCOLS


def test01_search_clients():
  # Checks the clients
  db = bob.db.ijba.Database()

  # The number of groups and protocols
  assert set(db.protocol_names()) == set(PROTOCOLS)
  assert len(db.groups()) == 2

  # test that the expected number of clients/client_ids is returned
  assert all(len(db.clients(protocol=protocol)) in (499, 500) for protocol in PROTOCOLS) #THERE IS NOT 500 CLIENTS IN THE search_split1


  #checking clients per group
  assert all(len(db.client_ids(protocol=protocol, groups='world')) in (333, 332) for protocol in PROTOCOLS)
  assert all(len(db.client_ids(protocol=protocol, groups='dev')) in (168, 167, 166) for protocol in PROTOCOLS)

  #The number of models and clients are identical (need to be as we have identification protocols)
  #assert all(len(db.model_ids(protocol=protocol, groups='dev')) == len(db.client_ids(protocol=protocol, groups='dev')) for protocol in PROTOCOLS) #THIS CANNOT BE TESTED, THERE ARE SOME CLIENTS THAT ARE ONLY FOR PROBING


def test02_search_objects():
  # Checks the objects
  db = bob.db.ijba.Database()

  # number of world files for the protocols (cf. the number of lines in the training file lists)

  world_files = [16910, 16354, 17287, 16548, 17040, 17644, 17584, 16367, 17421 ,16910]
  for i in range(10):
    assert len(db.objects(groups='world', protocol=SEARCH_PROTOCOLS[i])) == world_files[i]

  # enroll files (cf. the number of lines in the gallery file lists)
  enroll_files = [3000, 3261, 2661, 2894, 2920, 2451, 2912, 3106, 2594, 3000]
  for i in range(10):
    assert len(db.objects(groups='dev', purposes='enroll', protocol=SEARCH_PROTOCOLS[i])) == enroll_files[i]

  # probe files; not identical with probe file lists as files are used in several probes
  probe_files = [13737, 13983, 13467, 14323, 13566, 12789, 12131, 14601, 13323, 13737]
  for i in range(10):
    assert len(db.objects(groups='dev', purposes='probe', protocol=SEARCH_PROTOCOLS[i])) == probe_files[i]


def test03_comparison_objects():
  # Checks the objects
  db = bob.db.ijba.Database()

  # number of world files for the protocols (cf. the number of lines in the training file lists)
  world_files = [16910, 16354, 17287, 16548, 17040, 17644, 17584, 16367, 17421 ,16910]
  for i in range(10):
    assert len(db.objects(groups='world', protocol=COMPARISON_PROTOCOLS[i])) == world_files[i]

  # enroll files (cf. the number of lines in the gallery file lists)
  enroll_files = [4260, 4765, 3995, 4458, 4216, 3875, 4137, 4556, 3922, 4260]
  for i in range(10):
    assert len(db.objects(groups='dev', purposes='enroll', protocol=COMPARISON_PROTOCOLS[i])) == enroll_files[i]
