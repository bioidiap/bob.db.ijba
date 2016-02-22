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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Commands this database can respond to.
"""

import os
import sys

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


def upload_text(arguments):
  """For our raw database: uploads the bob/db/ijba/data  database file to a server."""
  # get the file name of the target db
  assert len(arguments.files) == 1
  assert os.path.basename(arguments.files[0]) == 'data'

  source_file = "./bob/db/ijba/data"
  target_file = os.path.join(arguments.destination, arguments.name + ".tar.bz2")

  if os.path.exists(source_file):
    print ("Compressing file '%s' to '%s'" %(source_file, target_file))
    import tarfile, stat
    f = tarfile.open(target_file, 'w:bz2')
    f.add(source_file, os.path.basename(source_file))
    f.close()
    os.chmod(target_file, stat.S_IRUSR|stat.S_IWUSR | stat.S_IRGRP|stat.S_IWGRP | stat.S_IROTH)
  else:
    print ("WARNING! Database file '%s' is not available.'" % (source_file))



def download_text(arguments):
  """For our raw database: Downloads the data dir from a server."""
  # get the file name of the target db
  assert len(arguments.files) == 1
  assert os.path.basename(arguments.files[0]) == 'data'
  target_file = arguments.files[0]
  if os.path.exists(target_file) and not arguments.force:
    print ("Skipping download of file '%s' since it exists already." % target_file)
  else:
    # get URL of database file
    source_url = os.path.join(arguments.source, arguments.name + ".tar.bz2")
    # download
    import sys, tempfile, tarfile
    if sys.version_info[0] <= 2:
      import urllib2 as urllib
    else:
      import urllib.request as urllib

    try:
      print ("Extracting url '%s' to '%s'" %(source_url, target_file))
      u = urllib.urlopen(source_url)
      f = tempfile.NamedTemporaryFile(suffix = ".tar.bz2")
      open(f.name, 'wb').write(u.read())
      t = tarfile.open(fileobj=f, mode = 'r:bz2')
      t.extractall(os.path.dirname(target_file))
      t.close()
      f.close()
    except Exception as e:
      print ("Error while downloading: '%s'" % e)




class Interface(BaseInterface):

  def name(self):
    return 'ijba'

  def version(self):
    import pkg_resources  # part of setuptools
    return pkg_resources.require('bob.db.%s' % self.name())[0].version

  def files(self):
    from pkg_resources import resource_filename
    raw_files = ('data',)
    return [resource_filename(__name__, k) for k in raw_files]
    #return ()

  def type(self):
    return 'text'

  def add_commands(self, parser):

    from . import __doc__ as docs
    import argparse

    subparsers = self.setup_parser(parser,
      "IJBA database", docs)

    from .query import Database
    db = Database()

    #Setting and reseting the download/upload commands
    from bob.db.base.driver import upload_command, download_command
    parser = upload_command(subparsers)
    parser.set_defaults(func=upload_text)

    parser = download_command(subparsers)    
    parser.set_defaults(func=download_text)


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
