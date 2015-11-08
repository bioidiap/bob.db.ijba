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

"""This module provides the Database interface allowing the user to query the JANUS database.
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

  def __init__(self, original_directory = None):
    # call base class constructor
    bob.db.verification.utils.SQLiteDatabase.__init__(self, SQLITE_FILE, File, original_directory=original_directory, original_extension=None)


  def provides_file_set_for_protocol(self, protocol=None):
    """As this database provides the file set interface (i.e., each probe contains several files) for all protocols, this function returns ``True`` throughout.

    Keyword Parameters:

    protocol
      Ignored.
    """
    return True


  def groups(self):
    """Returns a list of groups for the given protocol.

    Keyword Parameters:

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: a list of groups for the given protocol.
    """
    return Protocol_Template_Association.group_choices


  def clients(self, groups=None, protocol='search_split1'):
    """Returns a list of :py:class:`Client` objects for the specific query by the user.

    Keyword Parameters:

    groups
      One or several groups to which the models belong ``('world', 'dev', 'eval')``.
      If not specified, all groups are returned.Protocol_Template_Association.group_choicesdef cli

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the :py:class:`Client` objects which have the desired properties.
    """
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    groups = self.check_parameters_for_validity(groups, "group", self.groups())

    query = self.query(Client)\
                .outerjoin(File)\
                .outerjoin(Template, File.templates)\
                .outerjoin(Protocol_Template_Association)\
                .outerjoin(Protocol)\
                .filter(Protocol.name == protocol)\
                .group_by(File.client_id) \

    if groups is not None:
      query = query.filter(Protocol_Template_Association.group.in_(groups))


    return list(query)


  def client_ids(self, groups=None, protocol='search_split1'):
    """Returns a list of client ids (aka. subject_id) for the specific query by the user.

    Keyword Parameters:

    groups
      One or several groups to which the models belong ('world', 'dev', 'eval').
      If not specified, all groups are returned.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the client ids which have the desired properties.
    """
    return [client.id for client in self.clients(groups, protocol)]


  def model_ids(self, groups=None, protocol='search_split1'):
    """Returns a list of model ids for the specific query by the user.

    Keyword Parameters:

    groups
      Ignored; only model ids from the 'dev' group will be used.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the model ids for the given protocol.
    """
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())

    query = self.query(Template)\
                .outerjoin(Comparisons                  , Comparisons.template_A                    == Template.id)\
                .outerjoin(Protocol_Template_Association, Protocol_Template_Association.template_id == Comparisons.template_A)\
                .outerjoin(Protocol)\
                .filter(Protocol_Template_Association.group == 'dev')\
                .filter(Protocol.name == protocol) \
                .group_by(Template.id)
                

    return [template.template_id for template in query]


  def template_ids(self):
    """Returns a list of valid template ids, where :py:class:`Template`'s can be used both for model enrollment or probing.

    This function returns a list of actual template_ids.
    The according templates might differ between the protocols.
    """
    query = self.query(Template)
    return self.uniquify([template.template_id for template in query])


  def get_client_id_from_file_id(self, file_id, **kwargs):
    """Returns the client_id attached to the given file_id

    Keyword Parameters:

    file_id
      The file_id to consider, which is expected to be the unique :py:attr:`File.id`.

    Returns: The client_id attached to the given file_id
    """
    query = self.query(File)\
                .filter(File.id == file_id)

    assert query.count() == 1
    return query.first().client_id


  def get_client_id_from_path(self, path):
    """Returns the client_id attached to the given path

    Keyword Parameters:

    path
      The path to consider :py:attr:`File.path`.

    Returns: The client_id attached to the given file_id
    """
    query = self.query(File)\
                .filter(File.path == path)

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


  def objects(self, groups=None, protocol='search_split1', purposes=None, model_ids=None, media_ids=None, frames=None):
    """Using the specified restrictions, this function returns a list of File objects.

    Keyword Parameters:

    groups : str or [str] or ``None``
      One or several groups to which the models belong ('world', 'dev').

    protocol : str
      One of the available protocol names, see :py:meth:`protocol_names`.

    purposes : str or [str] or ``None``
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
    """

    # check that every parameter is as expected
    groups = self.check_parameters_for_validity(groups, "group", ["dev","world"])
    purposes = self.check_parameters_for_validity(purposes, "purpose", ["enroll","probe"])
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())

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

    def _filter_probes(query):
      #Getting the original template id in order to get the 
      templates_ids = []
      if not model_ids is None:
        query_templates = self.query(Template)\
          .outerjoin(Protocol_Template_Association)\
          .outerjoin(Protocol)\
          .filter(Protocol.name==protocol) \
          .filter(Template.template_id.in_(model_ids))
      
        templates_ids = [t.id for t in query_templates.all()]
        
      #Now selecting the probes for a given template. This is useful for the comparison protocol
      return _filter_others(query if model_ids is None else query.filter(Comparisons.template_A.in_(templates_ids)))


    # collect the queries
    queries = []
    if 'world' in groups:
      queries.append(
        _filter_models(
          self.query(File)\
              .outerjoin(Template, File.templates)\
              .outerjoin(Protocol_Template_Association)\
              .outerjoin(Protocol)\
              .filter(Protocol_Template_Association.group=="world") \
              .filter(Protocol.name==protocol)
        )
      )

    if 'dev' in groups:
    
      if( (len(purposes)>1) and (model_ids is None)):
        #Faster query
        queries.append(
          self.query(File)\
          .outerjoin(Template, File.templates)\
          .outerjoin(Protocol_Template_Association, Protocol_Template_Association.template_id == Template.id)\
          .outerjoin(Protocol)\
          .filter(Protocol.name==protocol)\
          .filter(Protocol_Template_Association.group==("dev")) \
          .group_by(File.id)
        )

    
      else:
        if 'enroll' in purposes:        
          queries.append(
              _filter_models(
              self.query(File)\
                  .outerjoin(Template, File.templates)\
                  .outerjoin(Comparisons, Comparisons.template_A == Template.id)\
                  .outerjoin(Protocol_Template_Association, Protocol_Template_Association.template_id == Comparisons.template_A)\
                  .outerjoin(Protocol)\
                  .filter(Protocol.name==protocol)\
                  .filter(Protocol_Template_Association.group=="dev") \
                  .group_by(File.id)
               )
          )

        if 'probe' in purposes:
          queries.append(
              _filter_probes(
              self.query(File)\
                  .outerjoin(Template, File.templates)\
                  .outerjoin(Comparisons, Comparisons.template_B == Template.id)\
                  .outerjoin(Protocol_Template_Association, Protocol_Template_Association.template_id == Comparisons.template_B)\
                  .outerjoin(Protocol)\
                  .filter(Protocol.name==protocol)\
                  .filter(Protocol_Template_Association.group=="dev") \
                  .group_by(File.id)
               )
          )

    # we have collected all queries, now extract the File objects
    return self.uniquify([file for query in queries for file in query])


  def object_sets(self, groups='dev', protocol='search_split1', purposes='probe', model_ids=None, media_ids=None, frames=None):
    """Using the specified restrictions, this function returns a list of :py:class:`Template` objects.

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
    """

    #TODO: SET purposes and group as IGNORED

    # check that every parameter is as expected
    #groups = self.check_parameters_for_validity(groups, "group", ["dev","world"])
    #purposes = self.check_parameters_for_validity(purposes, "purpose", ["enroll","probe"])    
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    

    # assure that the given model ids are in an iteratable container
    if isinstance(model_ids, int): model_ids = [model_ids]
    #if isinstance(media_ids, int): media_ids = (media_ids,)
    #if isinstance(frames, int): frames = (frames,)



    #query = self.query(Template)\
    #            .join(File, Template.files)\
    #            .join(ProtocolPurpose)\
    #            .filter(ProtocolPurpose.sgroup == 'dev')\
    #            .filter(ProtocolPurpose.purpose == 'probe')\
    #            .join(Protocol)\
    #            .filter(Protocol.name == protocol)
                
                
    if model_ids is None:

      query = self.query(bob.db.ijba.Template)\
                .outerjoin(bob.db.ijba.Comparisons, bob.db.ijba.Comparisons.template_B == bob.db.ijba.Template.id)\
                .outerjoin(bob.db.ijba.Protocol_Template_Association, bob.db.ijba.Protocol_Template_Association.template_id == bob.db.ijba.Comparisons.template_B)\
                .outerjoin(bob.db.ijba.Protocol) \
                .filter(bob.db.ijba.Protocol.name==protocol)\
                .filter(bob.db.ijba.Protocol_Template_Association.group=="dev") \
                .group_by(bob.db.ijba.Template.id)
    
    else:
      model_str = ""
      for m in model_ids:
        model_str += "'{0}',".format(str(m))
      model_str = model_str.rstrip(",")  

      sql = "SELECT comparisons.template_B " \
        "FROM template " \
        "LEFT OUTER JOIN comparisons ON comparisons.template_A = template.id " \
        "LEFT OUTER JOIN protocol_template_association ON protocol_template_association.template_id = comparisons.template_A " \
        "LEFT OUTER JOIN protocol ON protocol.id = protocol_template_association.protocol_id " \
        "WHERE protocol.name = \"" + protocol + "\" AND protocol_template_association.\"group\" = \"dev\" AND template.template_id IN ("+ model_str +") "

      template_ids    = [t[0] for t in self.m_session.execute(sql)]
      query = self.query(bob.db.ijba.Template) \
                  .filter(bob.db.ijba.Template.id.in_(template_ids))
  

    # filter other criteria
    #if media_ids is not None: query = query.filter(File.media_id.in_(media_ids))
    #if frames is not None: query = query.filter(File.frame.in_(frames))

    return list(query)



  def annotations(self, file):
    """Returns the annotations for the given :py:class:`File` object as a dictionary, see :py:class:`Annotation` for details."""
    self.assert_validity()
    # return annotations as obtained from the __call__ command of the Annotation class
    return file.annotation()


  def protocol_names(self):
    """Returns all registered protocol names, which are usually ``['NoTrain'] + ['split%d' for d in range(1,11)]``"""
    return [str(p.name) for p in self.protocols()]


  def protocols(self):
    """Returns all registered :py:class:`Protocol` objects."""
    return list(self.query(Protocol))


  def has_protocol(self, name):
    """Tells if a certain protocol is available"""
    return self.query(Protocol).filter(Protocol.name==name).count() != 0


  def original_file_name(self, file, check_existence = True):
    """Returns the original image file name with the correct file name extension.
    To be able to call this function, the ``original_directory`` must have been specified in the :py:class:`Database` constructor.

    Keyword parameters:

    file : :py:class:`File`
      The ``File`` object to get the original file name from.

    check_existence : bool
      If set to True (the default), the existence of the original image file is checked, prior to returning the files name.
    """
    if not self.original_directory:
      raise ValueError("The original_directory was not specified in the constructor.")
    # extract file name
    file_name = file.make_path(self.original_directory, file.extension, add_sighting_id=False)
    if not check_existence or os.path.exists(file_name):
      return file_name
    raise ValueError("The file '%s' was not found. Please check the original directory '%s'?" % (file_name, self.original_directory))
