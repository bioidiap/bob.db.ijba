#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""
This script has some sort of utilitary functions that parses the original database files
"""

from __future__ import print_function

import os

import bob.db.base


class File(bob.db.base.File):
  """
  IJBA File class

  Diferent from its ascendent class, this one has the client ID as input

  """
  def __init__(self, client_id, path, file_id = None):
    """**Constructor Documentation**

    Initialize the File object with the minimum required data.

    Parameters:

    client_id : various type
      The id of the client, this file belongs to.
      The type of it is dependent on your implementation.
      If you use an SQL database, this should be an SQL type like Integer or String.

    path : str
      The path of this file, relative to the basic directory.
      If you use an SQL database, this should be the SQL type String.
      Please do not specify any file extensions.

    file_id : various type
      The id of the file.
      The type of it is dependent on your implementation.
      If you use an SQL database, this should be an SQL type like Integer or String.
      If you are using an automatically determined file id, you can skip selecting the file id.
    """
    super(File, self).__init__(path, file_id)
    self.client_id = client_id



class Template:
  """A ``Template`` contains a list of :py:class:`File` objects belonging to
  the same subject (there might be several templates per subject).

  These are listed in the ``self.files`` field.

  A ``Template`` can serve for training, model enrollment, or for probing.

  Each template belongs specifically to a certain protocol, as the template_id
  in the original file lists might differ for different protocols.

  The protocol purpose can be obtained using ``self.protocol_purpose`` after
  creation of the database.

  Note that the ``template_id`` corresponds to the template_id of the file
  lists, while the ``id`` is only used as a unique key for querying the
  database.

  For convenience, the template also contains a ``path``, which is a
  concatenation of the ``File.media_id`` of the first file, and the
  ``self.template_id``, making it unique (at least per protocol).

  """

  def __init__(self, template_id, subject_id, files):
    self.id = template_id
    self.client_id   = subject_id
    assert isinstance(files,list)
    self.files       = files
    self.path = "%s-%s" % (files[0].media_id, template_id)


def read_file(filename):
  """Reads the given file and yields the template id, the subject id and path_id (path + sighting_id)"""

  with open(filename) as f:
    # skip the first line
    _ = f.readline()
    for line in f:
      splits = line.rstrip().split(',')

      assert len(splits) == 25


      #Parsing the ids
      template_id = int(splits[0])
      client_id   = int(splits[1])

      path,extension     = os.path.splitext(splits[2])
      sighting_id = splits[4]
      file_id     = "%s-%s" % (path, sighting_id)

      #Creating the file object and binding the annotations directly to the object
      file_obj = File(client_id, path, file_id)
      annotations = read_annotations(splits[6:])

      file_obj.annotations = annotations
      file_obj.extension   = extension
      file_obj.media_id    = splits[3]

      yield template_id, client_id, file_obj


def get_comparisons(filename):
  """
  Parse the file verify_comparisons_[n].csv where [n] is the split number
  """

  lines          = open(filename).readlines()
  template_comparisons = {}

  for line in lines:

    splits = line.rstrip().split(',')
    assert len(splits) == 2

    template_A = int(splits[0])
    template_B = int(splits[1].rstrip("\n"))

    if template_A not in template_comparisons:
      template_comparisons[template_A] = [template_B]
    else:
      template_comparisons[template_A].append(template_B)

  return template_comparisons



def get_templates(filename,  verbose=True):
  """
  Given a IJBA file, get a dictionary with all their templates with their respective files in the following format:


  templates['template_01'] = [file_01, file_02, file_03]
  templates['template_02'] = [file_01, file_02, file_03]
  .
  .
  .

  """

  templates       = {}
  for template_id, client_id, file_obj in read_file(filename):

    # create template with given IDs
    if template_id not in templates:
      templates[template_id] = Template(template_id,client_id,[file_obj])
    else:
      templates[template_id].files.append(file_obj)

  return templates



def read_annotations(raw_annotations):
  """
  Parse the annotations
  """

  annotations = {}


  tl_x   = float(raw_annotations[0]) if raw_annotations[0]!='' else None
  tl_y   = float(raw_annotations[1]) if raw_annotations[1]!='' else None
  size_x = float(raw_annotations[2]) if raw_annotations[2]!='' else None
  size_y = float(raw_annotations[3]) if raw_annotations[3]!='' else None
  re_x   = float(raw_annotations[4]) if raw_annotations[4]!='' else None
  re_y   = float(raw_annotations[5]) if raw_annotations[5]!='' else None
  le_x   = float(raw_annotations[6]) if raw_annotations[6]!='' else None
  le_y   = float(raw_annotations[7]) if raw_annotations[7]!='' else None
  n_x    = float(raw_annotations[8]) if raw_annotations[8]!='' else None
  n_y    = float(raw_annotations[9]) if raw_annotations[9]!='' else None
  yaw    = float(raw_annotations[10]) if raw_annotations[10]!='' else None

  forehead = raw_annotations[17-6]
  eyes     = raw_annotations[18-6]
  nm       = raw_annotations[19-6]
  indoor   = raw_annotations[20-6]
  gender   = raw_annotations[21-6]
  skin     = raw_annotations[22-5]
  age      = raw_annotations[23-6]


  annotations['topleft']            = (tl_y, tl_x)
  annotations['size']               = (size_y, size_x)
  annotations['bottomright']        = (tl_y + size_y, tl_x + size_x)
  annotations['forehead-visible']   = forehead
  annotations['eyes-visible']       = eyes
  annotations['nose-mouth-visible'] = nm
  annotations['indoor']             = indoor
  annotations['gender']             = gender
  annotations['skin-tone']          = skin
  annotations['age']                = age

  if all(a is not None for a in (re_y, re_x)): annotations['reye'] = (re_y, re_x)
  if all(a is not None for a in (le_y, le_x)): annotations['leye'] = (le_y, le_x)
  if all(a is not None for a in (n_y, n_x)): annotations['nose'] = (n_y, n_x)
  if yaw is not None: annotations['yaw'] = yaw

  return annotations


