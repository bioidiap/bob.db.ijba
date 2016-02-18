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

"""This script creates the IJBA database in a single pass.
"""

from __future__ import print_function

import os

from .models import *


def read_file(session, directory, filename):
  """Reads the given file and yields the template id, the subject id and path_id (path + sighting_id)"""
    
  with open(os.path.join(directory, filename)) as f:
    # skip the first line
    _ = f.readline()
    for line in f:
      splits = line.rstrip().split(',')
      #splits = splits[0:24] #Removing the facial hair parameter        
      assert len(splits) == 25
        
        
      template_id = int(splits[0])
      client_id   = int(splits[1])
      path,_      = os.path.splitext(splits[2])
      sighting_id = splits[4]
      
      yield template_id, client_id, "%s-%s" % (path, sighting_id)


def log_files(protocol_name, purpose):
  log = open("log_file_not_found_{0}_{1}.txt".format(protocol_name, purpose),'w')
  for f in files_not_found:
    log.write(f + "\n")
  del log


def add_files(session, directory, verbose):
  """Adds all files of the JANUS database"""
  clients = set()
  files      = {}
  filename = os.path.join('./metadata.csv')
  
  if verbose:
    print("Reading files from", filename)
  #with open(os.path.join(directory, 'protocol', filename)) as f:
  with open(filename) as f:
    # ignore the first line
    _ = f.readline()
    # read the rest of the lines
    for line in f:
      splits = line.rstrip().split(',')
      splits = splits[0:24] #TIAGO: Removing the facial hair parameter
      assert len(splits) == 24, splits
      # first, create a Client, if not yet there
      subject_id = int(splits[1])
      if subject_id not in clients:
        if verbose > 1: print(". Adding client", subject_id)
        client = _update(session, Client(subject_id))
        clients.add(subject_id)

      # now, create a File
      # unique file id is the path id and the sighting_id
      path_id = "%s-%s" % (os.path.splitext(splits[2])[0], splits[4])
      path    = splits[2]
      
      if verbose > 2: print("... Adding file", path)
      if path_id not in files:        
        file = _update(session, File(path, subject_id, int(splits[3]), int(splits[4]), int(splits[5]) if splits[5] else None))
        #                            path, client_id,  media_id,        sighting_id ,  frame

        files[path_id] = file

        # create annotations
        if verbose > 2: print("... Adding annotation")
        annotation = Annotation(file.id, [float(a) if a else None for a in splits[6:17]], [int(a) if a else None for a in splits[17:]])
        session.add(annotation)

  # finally, return the files that we have created
  return files




def add_templates(session, files, directory, filename, protocol, group, verbose=True):
  """
  Given a IJBA filename, add all the templates
  """  
  
  templates       = {}
  for template_id, subject_id, path_id in read_file(session, directory, filename):

    if subject_id==0:
      raise ValueError("Database inconsistency. Subject id is equal to 0.")
      #if verbose: print("Ignoring the file {0}, because there is no client connected to him/her".format(path_id))      
      #continue

    #if(template_id=="4161"): #For some reason this fails in the split2, but if I commit does not
      #session.commit()
        
    # create template with given IDs 
    if template_id not in templates:
      if verbose > 1: print(". Adding template", template_id)
      
      template = _update(session, Template(template_id, subject_id))
      templates[template_id] = template

      #Adding the template
      _update(session, Protocol_Template_Association(protocol.id, template.id, group))
          
    else:
      template = templates[template_id]

    # add files
    template.add_file(files[path_id])
  
  return templates




def add_protocols_search(session, files, directory, verbose=True):
  """Adds the templates and protocols for the JANUS database"""
  
  # Now, add the training splits protocols
  for split in [str(i) for i in range(1,11)]:
    # create and add protocol

    protocol_name = "search_split%s" % split
    protocol      = _update(session, Protocol(protocol_name))
  
    if verbose: print("Adding Protocol", protocol.name)

    templates = {}
    templates['train']   = {}
    templates['gallery'] = {}
    templates['probe']   = {}

    # read gallery and probe files
    for purpose in ("gallery", "probe", "train"):

      if(purpose=="train"):
        filename = os.path.join("IJB-A_1N_sets","split%s" % split, "train_%s.csv" % (split))
        group = "world"
      else:
        filename = os.path.join("IJB-A_1N_sets","split%s" % split, "search_%s_%s.csv" % (purpose, split))
        group = "dev"

      templates[purpose] = add_templates(session, files, directory,filename, protocol, group, verbose=verbose)
    
    ##Adding the comparisons. I KNOW THIS IS NOT EFFICIENT IN THE DATABASE SIZE PERSPECTIVE,
    ##BUT WAS THE WAY THAT I FOUND TO HAVE ONLY ONE DECENT DATABASE MODEL FOR THE SEARCH AND COMPARISON PROTOCOLS.
    for t_gallery in templates['gallery']:
      for t_probe in templates['probe']:
        _update(session, Comparisons(protocol.id, templates['gallery'][t_gallery].id, templates['probe'][t_probe].id))        



def add_protocols_comparison(session, files, directory, verbose=True):
  """
  Adds the templates and the COMPARISON protocols for the JANUS database
  
  For the Compasison protocols, the train set is the same as the search.
  
  The comparisons between templates os described in the file verify_comparisons_n.csv where 'n' is the split name
  """

  # Now, add the training splits protocols
  for split in [str(i) for i in range(1,11)]:
    # create and add protocol

    protocol_name = "compare_split%s" % split
    protocol      = _update(session, Protocol(protocol_name))
  
    if verbose: print("Adding Protocol", protocol.name)

    templates = {}
    templates['train']   = {}
    templates['not_train'] = {}

    filename = os.path.join("IJB-A_11_sets", "split%s" % split, "verify_metadata_%s.csv" % (split))
    group    = "dev"

    #First, lets add the verification files
    templates['not_train'] = add_templates(session, files, directory,filename, protocol, group, verbose=verbose)
    
    #Now lets add the comparisons
    filename = os.path.join(directory,"IJB-A_11_sets" ,"split%s" % split, "verify_comparisons_%s.csv" % (split))
    comparisons = open(filename)
    
    for c in comparisons:
      template_A = templates['not_train'][int(c.split(",")[0])]
      template_B = templates['not_train'][int(c.split(",")[1].rstrip("\n\r"))]
      _update(session, Comparisons(protocol.id, template_A.id, template_B.id))
    
    ## Now adding the training set
    filename = os.path.join("IJB-A_11_sets", "split%s" % split, "train_%s.csv" % (split))
    group    = "world"
    templates['train'] = add_templates(session, files, directory,filename, protocol, group, verbose=verbose)



def generate_metadata(directory):
  """
  Read all the metadata files from the splits and save in one single file.
  The files are the following: search_gallery_[1-10].csv search_probe_[1-10].csv verify_metadata_[1-10].csv
  """  

  def read_file(filename, read_header=False):
    lines = open(filename).readlines()
    
    if(read_header):
      return lines
    else:
      return lines[1:]


  #For each split
  metadata_list_temp = []
  for i in range(1,11):
    read_header = False
    if(i==1):
      read_header = True

    #Search protocol files (1:N)
    metadata_list_temp.append(read_file(os.path.join(directory,"IJB-A_1N_sets","split{0}".format(i),"search_gallery_{0}.csv".format(i)), read_header=read_header))
    metadata_list_temp.append(read_file(os.path.join(directory,"IJB-A_1N_sets","split{0}".format(i),"search_probe_{0}.csv".format(i))))
               
    #Comparison protocol files (1:1)
    metadata_list_temp.append(read_file(os.path.join(directory,"IJB-A_11_sets","split{0}".format(i),"verify_metadata_{0}.csv".format(i))))
        
    #Both protocols (The train set is the same)
    metadata_list_temp.append(read_file(os.path.join(directory,"IJB-A_11_sets","split{0}".format(i),"train_{0}.csv".format(i))))
    
    
  #flatting the list
  metadata_list = [item for sublist in metadata_list_temp for item in sublist]
  metadata_file = open("./metadata.csv",'w')
  for m in metadata_list:
    metadata_file.write(m)
  del metadata_file


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

  
  if args.verbose:  print("Generating the metadata files")
  generate_metadata(args.directory)  

  files = add_files(session, args.directory, args.verbose)  
  add_protocols_search(session, files, args.directory, args.verbose)
  add_protocols_comparison(session, files, args.directory, args.verbose)
  
  session.commit()
  session.close()

def add_command(subparsers):
  """Add specific subcommands that the action "create" can use"""

  parser = subparsers.add_parser('create', help=create.__doc__)

  parser.add_argument('-R', '--recreate', action='store_true', help='If set, I\'ll first erase the current database')
  parser.add_argument('-v', '--verbose', action='count', help='Do SQL operations in a verbose way?')

  parser.add_argument('-D', '--directory', metavar='DIR', default='/idiap/resource/database/IJB-A/', help='The path to the JANUS database')

  parser.set_defaults(func=create) #action
