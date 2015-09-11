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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This script creates the CAS-PEAL database in a single pass.
"""

from __future__ import print_function

import os

from .models import *

def _update(session, field):
  """Add, updates and returns the given field for in the current session"""
  session.add(field)
  session.flush()
  session.refresh(field)
  return field


def add_files(session, directory, add_splits, verbose):
  """Adds all files of the JANUS database"""
  clients = set()
#  templates = {}
  files = {}
#  filenames = ['gallery.csv', 'probe.csv']
#  if add_splits:
#    filenames += ["split{s}/{p}_{s}.csv".format(s=s, p=p) for s in range(1,11) for p in ("train", "gallery", "probe")]

  filename = os.path.join(directory, 'protocol', 'metadata.csv')

  if verbose:
    print("Reading files from", filename)
  with open(os.path.join(directory, 'protocol', filename)) as f:
    # ignore the first line
    _ = f.readline()
    # read the rest of the lines
    for line in f:
      splits = line.rstrip().split(',')
      assert len(splits) == 24, splits
      # first, create a Client, if not yet there
      subject_id = int(splits[1])
      if subject_id not in clients:
        if verbose > 1: print(". Adding client", subject_id)
        client = _update(session, Client(subject_id))
        clients.add(subject_id)

      # now, create a File
      path = splits[2]
      # unique file id is the path id and the sighting_id
      path_id = "%s-%s" % (path, splits[4])
      if verbose > 2: print("... Adding file", path)
      if path_id not in files:
        file = _update(session, File(path, subject_id, int(splits[3]), int(splits[4]), int(splits[5]) if splits[5] else None))
        files[path_id] = file
        # create annotations
        if verbose > 2: print("... Adding annotation")
        annotation = Annotation(file.id, [float(a) if a else None for a in splits[6:17]], [int(a) if a else None for a in splits[17:]])
        session.add(annotation)

  # finally, return the files that we have created
  return files

def add_protocols(session, files, directory, add_splits, verbose):
  """Adds the protocols for the JANUS database"""

  def _read_file(filename):
    """Reads the given file and yields the template id, the subject id and path_id (path + sighting_id)"""
    with open(os.path.join(directory, 'protocol', filename)) as f:
      # skip the first line
      _ = f.readline()
      for line in f:
        splits = line.rstrip().split(',')
        assert len(splits) == 24, splits
        # we only carte about the template id.
        yield int(splits[0]), int(splits[1]), "%s-%s" % (splits[2], splits[4])

  # create and add protocol
  protocol = _update(session, Protocol("NoTrain"))
  if verbose: print("Adding Protocol", protocol.name)

  # read gallery and probe files
  for purpose in ("gallery", "probe"):
    # create protocol purpose association entry
    pp = _update(session, ProtocolPurpose(purpose, protocol.id))
    filename = '%s.csv' % purpose
    templates = {}
    for template_id, subject_id, path_id in _read_file(filename):
      # create template with given IDs for the given protocol purpose
      if template_id not in templates:
        if verbose > 1: print(". Adding template", template_id)
        template = _update(session, Template(template_id, subject_id, pp.id))
        templates[template_id] = template
      else:
        template = templates[template_id]

      # add files
      assert path_id in files
      template.files.append(files[path_id])

  if add_splits:
    # Now, add the training splits protocols
    for split in [str(i) for i in range(1,11)]:
      # create and add protocol
      protocol = _update(session, Protocol("split%s" % split))
      if verbose: print("Adding Protocol", protocol.name)

      # read gallery and probe files
      for purpose in ("train", "gallery", "probe"):
        # create protocol purpose association entry
        pp = _update(session, ProtocolPurpose(purpose, protocol.id))
        if verbose: print("Adding Protocol purpose", pp.protocol.name, pp.purpose)
        filename = os.path.join("split%s" % split, "%s_%s.csv" % (purpose, split))
        templates = {}
        for template_id, subject_id, path_id in _read_file(filename):
          # create template with given IDs for the given protocol purpose
          if template_id not in templates:
            if verbose > 1: print(". Adding template", template_id)
            template = _update(session, Template(template_id, subject_id, pp.id))
            templates[template_id] = template
          else:
            template = templates[template_id]

          # add files
          assert path_id in files
          template.files.append(files[path_id])


def create_tables(args):
  """Creates all necessary tables (only to be used at the first time)"""

  from bob.db.base.utils import create_engine_try_nolock

  engine = create_engine_try_nolock(args.type, args.files[0], echo=(args.verbose > 2))
  File.metadata.create_all(engine)
  Annotation.metadata.create_all(engine)
  Template.metadata.create_all(engine)
  Protocol.metadata.create_all(engine)


# Driver API
# ==========

def create(args):
  """Creates or re-creates this database"""

  from bob.db.base.utils import session_try_nolock

  dbfile = args.files[0]

  if args.recreate:
    if args.verbose and os.path.exists(dbfile):
      print('unlinking %s...' % dbfile)
    if os.path.exists(dbfile): os.unlink(dbfile)

  if not os.path.exists(os.path.dirname(dbfile)):
    os.makedirs(os.path.dirname(dbfile))

  # the real work...
  create_tables(args)
  session = session_try_nolock(args.type, args.files[0], echo=(args.verbose > 2))
  templates = add_files(session, args.directory, not args.no_splits, args.verbose)
  add_protocols(session, templates, args.directory, not args.no_splits, args.verbose)
  session.commit()
  session.close()

def add_command(subparsers):
  """Add specific subcommands that the action "create" can use"""

  parser = subparsers.add_parser('create', help=create.__doc__)

  parser.add_argument('-R', '--recreate', action='store_true', help='If set, I\'ll first erase the current database')
  parser.add_argument('-v', '--verbose', action='count', help='Do SQL operations in a verbose way?')
  parser.add_argument('-D', '--directory', metavar='DIR', default='/home/mgunther/databases/janus', help='The path to the JANUS database')
  parser.add_argument('-n', '--no-splits', action='store_true', help='If selected, the 10 splits of the protocols are disabled.')

  parser.set_defaults(func=create) #action
