#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Tiago de Freitas Pereira <tiago.pereira@idiap.ch>
# @date:   Thu 18 Feb 2016 15:23:45 CET 
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

"""
This script has some sort of utilitary functions that parses the original database files
"""

from __future__ import print_function

import os

from bob.db.verification.utils import File



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

      path,_      = os.path.splitext(splits[2])
      sighting_id = splits[4]
      file_id     = "%s-%s" % (path, sighting_id)

      #Creating the file object and binding the annotations directly to the object
      file_obj = File(client_id, path, file_id)      
      annotations = read_annotations(splits[6:])
      
      file_obj.annotations = annotations
      
      yield template_id, file_obj


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
  for template_id, file_obj in read_file(filename):

    # create template with given IDs 
    if template_id not in templates:
      templates[template_id] = [file_obj]
    else:
      templates[template_id].append(file_obj)
    
  return templates



def read_annotations(raw_annotations):
  """
  Parse the annotations
  """

  annotations = {}

  annotations['tl_x']   = raw_annotations[0]
  annotations['tl_y']   = raw_annotations[1]
  annotations['size_x'] = raw_annotations[2]
  annotations['size_y'] = raw_annotations[3]
  annotations['re_x']   = raw_annotations[4]
  annotations['re_y']   = raw_annotations[5]
  annotations['le_x']   = raw_annotations[6]
  annotations['le_y']   = raw_annotations[7]
  annotations['n_x']    = raw_annotations[8]
  annotations['n_y']    = raw_annotations[9]
  annotations['yaw']    = raw_annotations[10]
    
  annotations['forehead'] = raw_annotations[17-6]
  annotations['eyes']     = raw_annotations[18-6]
  annotations['nm']       = raw_annotations[19-6]
  annotations['indoor']   = raw_annotations[20-6]
  annotations['gender']   = raw_annotations[21-6]
  annotations['skin']     = raw_annotations[22-5]
  annotations['age']      = raw_annotations[23-6]


  return annotations


