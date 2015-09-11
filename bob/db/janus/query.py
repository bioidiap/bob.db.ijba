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

"""This module provides the Database interface allowing the user to query the
CAS-PEAL database.
"""

import os
from bob.db.base import utils
from .models import *
from .driver import Interface

import bob.db.verification.utils

SQLITE_FILE = Interface().files()[0]

class Database(bob.db.verification.utils.SQLiteDatabase):
  """The database class opens and maintains a connection opened to the Database.

  It provides many different ways to probe for the characteristics of the data
  and for the data itself inside the database.
  """

  def __init__(self, original_directory = None, original_extension = ''):
    # call base class constructor
    bob.db.verification.utils.SQLiteDatabase.__init__(self, SQLITE_FILE, File, original_directory=original_directory, original_extension=original_extension)

  def provides_file_set_for_protocol(self, protocol=None):
    """As this database provides the file set interface (i.e., each probe contains several files) for all protocols, this function returns ``True`` throughout.

    Keyword Parameters:

    protocol
      Ignored.
    """
    return True


  def groups(self, protocol='split1'):
    """Returns a list of groups for the given protocol

    Keyword Parameters:

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: a list of groups for the given protocol
    """
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    # for A and B protocol there is only the dev group, for the others it is world and dev
    return ProtocolPurpose.group_choices[1:] if protocol == 'NoTrain' else ProtocolPurpose.group_choices


  def clients(self, groups=None, protocol='split1'):
    """Returns a list of Client objects for the specific query by the user.

    Keyword Parameters:

    groups
      One or several groups to which the models belong ('world', 'dev', 'eval').
      If not specified, all groups are returned.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the Client objects which have the desired properties.
    """
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    groups = self.check_parameters_for_validity(groups, "group", self.groups())

    query = self.query(Client)\
                .join(Template)\
                .join(ProtocolPurpose)\
                .join(Protocol)\
                .filter(Protocol.name == protocol)

    if groups is not None:
      query = query.filter(ProtocolPurpose.sgroup.in_(groups))

    return list(query)


  def client_ids(self, groups=None, protocol='split1'):
    """Returns a list of client ids for the specific query by the user.

    Keyword Parameters:

    groups
      One or several groups to which the models belong ('world', 'dev', 'eval').
      If not specified, all groups are returned.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the client ids which have the desired properties.
    """
    return [client.id for client in self.clients(groups, protocol)]


  def model_ids(self, groups=None, protocol='split1'):
    """Returns a list of model ids for the specific query by the user.

    Keyword Parameters:

    groups
      Ignored; only model ids from the dev group will be used.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the model ids for the given protocol.
    """
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())

    query = self.query(Template)\
                .join(ProtocolPurpose)\
                .filter(ProtocolPurpose.sgroup == 'dev')\
                .filter(ProtocolPurpose.purpose == 'enroll')\
                .join(Protocol)\
                .filter(Protocol.name == protocol)

    return [template.template_id for template in query]


  def template_ids(self):
    """Returns a list of valid Template ids, where Templates can be used both for model enrollment or probing."""
    query = self.query(Template)
    return [template.template_id for template in query]


  def get_client_id_from_file_id(self, file_id, **kwargs):
    """Returns the client_id attached to the given file_id

    Keyword Parameters:

    file_id
      The file_id to consider

    Returns: The client_id attached to the given file_id
    """
    query = self.query(File)\
                .filter(File.id == file_id)

    assert query.count() == 1
    return query.first().client_id


  def get_client_id_from_model_id(self, model_id):
    """Returns the client_id attached to the given model_id

    Keyword Parameters:

    model_id
      The model id to consider

    Returns: The client_id attached to the given model_id
    """
    query = self.query(Template)\
                .filter(Template.template_id == model_id)

    assert all(t.client_id == query.first().client_id for t in query)
    return query.first().client_id


  def objects(self, groups=None, protocol='split1', purposes=None, model_ids=None, media_ids=None, frames=None, annotated=None):
    """Using the specified restrictions, this function returns a list of File objects.

    Keyword Parameters:

    groups : str or [str]
      One or several groups to which the models belong ('world', 'dev').

    protocol : str
      One of the available protocol names, see :py:meth:`protocol_names`.

    purposes : str or [str]
      One or several purposes for which files should be retrieved ('enroll', 'probe').
      Note: this field is ignored for group 'world'.

    model_ids : int or [int] or ``None``
      If given (as a list of model id's or a single one), only the files belonging to the specified model id is returned.
      For 'probe' purposes, this field is ignored since probe files are identical for all models.
      Remember that the database provides only identification protocols.

    media_ids : int or [int] or ``None``
      If given, only the files with the given media ids are returned.

    frames : int or [int] or ``None``
      If given, only the video files with the given frame number are returned.
      Note that the images of the database will be ignored, when this option is selected.

    annotated : ``True``, ``False`` or ``None``
      For some files, the facial landmark annotations are absent (if the image does not contain a face) or incomplete (when the face is shown in profile view).
      With this parameter, you can define, how to handle these annotations.
      If ``True``, only files that are fully annotated are returned.
      If ``False``, only files that are not fully annotated are returned.
      If ``None``, all files are returned.
    """

    # check that every parameter is as expected
    groups = self.check_parameters_for_validity(groups, "group", ProtocolPurpose.group_choices)
    purposes = self.check_parameters_for_validity(purposes, "purpose", ProtocolPurpose.purpose_choices)
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    assert annotated in (True, False, None)

    # assure that the given model ids are in an iteratable container
    if isinstance(model_ids, int): model_ids = (model_ids,)
    if isinstance(media_ids, int): media_ids = (media_ids,)
    if isinstance(frames, int): frames = (frames,)

    def _filter_others(query):
      if media_ids is not None: query = query.filter(File.media_id.in_(media_ids))
      if frames is not None: query = query.filter(File.frame.in_(frames))
      return query

    def _filter_models(query):
      return _filter_others(query if model_ids is None else query.filter(Template.template_id.in_(model_ids)))


    # collect the queries
    queries = []
    if 'world' in groups:
      queries.append(
        _filter_models(
          self.query(File)\
              .join(Template, File.templates)\
              .join(ProtocolPurpose)\
              .filter(ProtocolPurpose.sgroup=='world')\
              .join(Protocol)\
              .filter(Protocol.name == protocol)
        )
      )

    if 'dev' in groups:
      if 'enroll' in purposes:
        queries.append(
          _filter_models(
            self.query(File)\
                .join(Template, File.templates)\
                .join(ProtocolPurpose)\
                .filter(ProtocolPurpose.sgroup=='dev')\
                .filter(ProtocolPurpose.purpose=='enroll')\
                .join(Protocol)\
                .filter(Protocol.name == protocol)
          )
        )

      if 'probe' in purposes:
        queries.append(
          _filter_others(
            self.query(File)\
                .join(Template, File.templates)\
                .join(ProtocolPurpose)\
                .filter(ProtocolPurpose.sgroup=='dev')\
                .filter(ProtocolPurpose.purpose=='probe')\
                .join(Protocol)\
                .filter(Protocol.name == protocol)
          )
        )

    # we have collected all queries, now extract the File objects
    return self.uniquify([file for query in queries for file in query])


  def object_sets(self, groups='dev', protocol='split1', purposes='probe', model_ids=None, media_ids=None, frames=None, annotated=None):
    """Using the specified restrictions, this function returns a list of a list of File objects.
    Each sub-list contains all files belonging to a certain probe template.

    Keyword Parameters:

    groups : str or [str]
      Only the 'dev' group is accepted.

    protocol : str
      One of the available protocol names, see :py:meth:`protocol_names`.

    purposes : str or [str]
      Only the 'probe' purpose is accepted.

    model_ids : int or [int] or ``None``
      ignored

    media_ids : int or [int] or ``None``
      If given, only the files with the given media ids are returned.

    frames : int or [int] or ``None``
      If given, only the video files with the given frame number are returned.
      Note that the images of the database will be ignored, when this option is selected.

    annotated : ``True``, ``False`` or ``None``
      For some files, the facial landmark annotations are absent (if the image does not contain a face) or incomplete (when the face is shown in profile view).
      With this parameter, you can define, how to handle these annotations.
      If ``True``, only files that are fully annotated are returned.
      If ``False``, only files that are not fully annotated are returned.
      If ``None``, all files are returned.
    """

    # check that every parameter is as expected
    groups = self.check_parameters_for_validity(groups, "group", ProtocolPurpose.group_choices[1:])
    purposes = self.check_parameters_for_validity(purposes, "purpose", ProtocolPurpose.purpose_choices[2:])
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    assert annotated in (True, False, None)

    # assure that the given model ids are in an iteratable container
    if isinstance(model_ids, int): model_ids = (model_ids,)
    if isinstance(media_ids, int): media_ids = (media_ids,)
    if isinstance(frames, int): frames = (frames,)

    query = self.query(Template)\
                .join(File, Template.files)\
                .join(ProtocolPurpose)\
                .filter(ProtocolPurpose.sgroup == 'dev')\
                .filter(ProtocolPurpose.purpose == 'probe')\
                .join(Protocol)\
                .filter(Protocol.name == protocol)

    # TODO: When criteria are selected, assure that only files with the according criteria are returned within the FileSet

    # filter other criteria
    if media_ids is not None: query = query.filter(File.media_id.in_(media_ids))
    if frames is not None: query = query.filter(File.frame.in_(frames))

    # TODO: implement the sub-selection of Files based on the annotated parameter

    return list(query)

    # we have collected all queries, now extract the File objects
    files = self.uniquify([file for query in queries for file in query])

    if annotated is not None:
      # query all desired annotations
      annotations = list(self.query(Annotation).join(File).filter(File.id.in_([f.id for f in files])))
      # short-cut annotations in dict structure
      annotations = {a.file_id : a for a in annotations}
      if annotated:
        # all files must be completely annotated
        return [f for f in files if f.id in annotations and all([k is not None for v in annotations[f.id]().values() for k in v])]
      else:
        # all files must contain missing annotations
        return [f for f in files if f.id not in annotations or any([k is None for v in annotations[f.id]().values() for k in v])]

    return files


  def annotations(self, file):
    """Returns the annotations for the given file id as a dictionary {'reye':(y,x), 'leye':(y,x)}."""
    self.assert_validity()
    # return annotations as obtained from the __call__ command of the Annotation class
    return file.annotation() if file.annotation is not None else None


  def protocol_names(self):
    """Returns all registered protocol names"""
    return [str(p.name) for p in self.protocols()]


  def protocols(self):
    """Returns all registered protocols"""
    return list(self.query(Protocol))


  def has_protocol(self, name):
    """Tells if a certain protocol is available"""
    return self.query(Protocol).filter(Protocol.name==name).count() != 0


  def original_file_name(self, file, check_existence = True):
    """Returns the filename with the correct filename extension."""
    if not self.original_directory:
      raise ValueError("The original_directory was not specified in the constructor.")
    # extract file name
    file_name = file.make_path(self.original_directory, file.extension, add_sighting_id=False)
    if not check_existence or os.path.exists(file_name):
      return file_name
    raise ValueError("The file '%s' was not found. Please check the original directory '%s'?" % (file_name, self.original_directory))
