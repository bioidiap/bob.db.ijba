#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""Commands this database can respond to.
"""

import os
import sys
import pkg_resources

from bob.db.base.driver import Interface as BaseInterface


def checkfiles(args):
  """Checks existence of files based on your criteria"""

  from .query import Database

  protocols        = ['search_split%d' % s for s in range(1,11)]
  protocols.extend(['compare_split%d' % s for s in range(1,11)])

  for p in protocols:

    db = Database()
    r = db.objects(protocol=p)
    good = {}
    bad = {}
    # go through all files, check if they are available on the filesystem
    for f in r:

      found = False
      for e in args.extension:

        if os.path.exists(f.make_path(args.directory,e)):
          good[f.id] = f.make_path(args.directory,e)
          found = True
          break
      if not found:
        bad[f.id] = f.make_path(args.directory,args.extension[0])

  # report
  output = sys.stdout
  if args.selftest:
    from bob.db.base.utils import null
    output = null()

  if bad:
    for id, f in bad.items():
      output.write('Cannot find file "%s"\n' % f)
    output.write('%d files (out of %d) were not found at "%s"\n' % \
        (len(bad), len(r), args.directory))
  else:
    output.write('All files were found !!!')

  return 0


def path(args):
  """Returns a list of fully formed paths or stems given some file id"""

  from .query import Database
  db = Database()

  output = sys.stdout
  if args.selftest:
    from bob.db.base.utils import null
    output = null()

  r = db.paths(args.id, prefix=args.directory, suffix=args.extension)
  for path in r: output.write('%s\n' % path)

  if not r: return 1

  return 0


class Interface(BaseInterface):


  def name(self):
    return 'ijba'


  def version(self):
    return pkg_resources.require('bob.db.%s' % self.name())[0].version


  def files(self):
    basedir = pkg_resources.resource_filename(__name__, '')
    filelist = os.path.join(basedir, 'files.txt')
    return [os.path.join(basedir, k.strip()) for k in \
      open(filelist, 'rt').readlines() if k.strip()]


  def type(self):
    return 'text'


  def add_commands(self, parser):

    from . import __doc__ as docs
    import argparse

    subparsers = self.setup_parser(parser, "IJBA database", docs)

    from .query import Database
    db = Database()

    # the "checkfiles" action
    parser = subparsers.add_parser('checkfiles', help=checkfiles.__doc__)
    parser.add_argument('-d', '--directory', help="if given, this path will be prepended to every entry returned.")
    parser.add_argument('-e', '--extension', nargs="+", help="if given, this extension will be appended to every entry returned.")
    parser.add_argument('--self-test', dest="selftest", action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=checkfiles) #action

    # adds the "path" command
    parser = subparsers.add_parser('path', help=path.__doc__)
    parser.add_argument('-d', '--directory', help="if given, this path will be prepended to every entry returned.")
    parser.add_argument('-e', '--extension', help="if given, this extension will be appended to every entry returned.")
    parser.add_argument('id', type=int, nargs='+', help="one or more file ids to look up. If you provide more than one, files which cannot be found will be omitted from the output. If you provide a single id to lookup, an error message will be printed if the id does not exist in the database. The exit status will be non-zero in such case.")
    parser.add_argument('--self-test', dest="selftest", action='store_true', help=argparse.SUPPRESS)
    parser.set_defaults(func=path) #action
