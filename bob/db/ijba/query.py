#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""Database interface allowing the user to query the IJB-A database.
"""

import os
from bob.db.base import utils

#from .models import *

from .driver import Interface
from .reader import get_templates, get_comparisons

import bob.db.base


class Database(bob.db.base.Database):
  """The database class opens and maintains a connection opened to the Database.

  It provides many different ways to probe for the characteristics of the data
  and for the data itself inside the database.
  """

  def __init__(self, original_directory = None, annotations_directory=None, original_extension=None):

    # call base class constructor
    self.original_directory = original_directory
    self.original_extension = original_extension

    #Creating our data structure to deal with the db files
    self.memory_db = {}
    self.templates = {} #Dictionary with the templates in a unique list

    if(annotations_directory is None):#Get the default location
      import pkg_resources
      annotations_directory = pkg_resources.resource_filename(__name__, 'data')

    self.annotations_directory = annotations_directory


  def _solve_comparisons(self, protocol):
    """
    Given a protocol, try to solve the filename verify_comparisons_[n].csv where n is the split number
    """

    relative_dir = "IJB-A_11_sets"

    #Getting the split
    for i in range(1,10):
      split = "split{0}".format(i)
      if(split in protocol):
        relative_dir = os.path.join(self.annotations_directory,relative_dir,split,"verify_comparisons_{0}.csv".format(i))
        break

    return relative_dir


  def _solve_filename(self, protocol, purpose):
    """
    Given a protocol and the purpose, try to solve the filename
    """

    relative_dir = ""

    #Getting the recognition task
    if("search" in protocol):
      relative_dir = "IJB-A_1N_sets"
    else:
      relative_dir = "IJB-A_11_sets"

    #Getting the split
    for i in range(1,10):
      split = "split{0}".format(i)
      if(split in protocol):
        relative_dir = os.path.join(relative_dir,split)
        split_number = i
        break

    #Getting the file
    if purpose=="train":
      return os.path.join(self.annotations_directory, relative_dir,"train_{0}.csv".format(split_number))

    if("search" in protocol):
      if purpose=="enroll":
        return os.path.join(self.annotations_directory,relative_dir,"search_gallery_{0}.csv".format(split_number))
      else:
        return os.path.join(self.annotations_directory,relative_dir,"search_probe_{0}.csv".format(split_number))

    else:
      #comparison
      return os.path.join(self.annotations_directory, relative_dir,"verify_metadata_{0}.csv".format(split_number))


  def _load_data(self, protocol, group, purpose):
    """
    Check and load the data from a specific protocol in the variable self.memory_db
    """

    if not protocol in self.memory_db:
      self.memory_db[protocol] = {}

    #Training set is the same for both major protocols (search and comparison)
    if purpose=="train":
      self.memory_db[protocol][purpose] = get_templates(self._solve_filename(protocol,purpose))
      return

    #Special treatment for the comparison
    if "search" in protocol:
      if not purpose in self.memory_db[protocol]:
        templates =                       get_templates(self._solve_filename(protocol,purpose))
        self.memory_db[protocol][purpose] = templates

        self.templates.update(templates)
    else:
      if not 'comparison-templates' in self.memory_db[protocol]:
        templates                                        = get_templates(self._solve_filename(protocol,""))
        self.memory_db[protocol]['comparison-templates'] = templates
        self.memory_db[protocol]['comparisons']          = get_comparisons(self._solve_comparisons(protocol))
        self.templates.update(templates)



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
    return ('world', 'dev')


  def clients(self, groups=None, protocol='search_split1'):
    """Same as client_id

    Keyword Parameters:

    groups
      One or several groups to which the models belong ('world', 'dev', 'eval').
      If not specified, all groups are returned.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    Returns: A list containing all the client ids which have the desired properties.
    """

    return self.client_ids(groups = groups, protocol = protocol)


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

    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    groups = self.check_parameters_for_validity(groups, "group", self.groups())

    if "search" in protocol:
      objects = self.objects(groups=groups, protocol=protocol)
    else:

      objects = []
      for g in groups:
          if g == "world":
            objects.extend(self.objects(groups=g, protocol=protocol))
          else:
            self._load_data(protocol, "dev", "")
            objects.extend([o for t in self.memory_db[protocol]['comparison-templates'] for o in self.memory_db[protocol]['comparison-templates'][t].files ])

    ids = list(set([o.client_id for o in objects ]))

    return ids


  def model_ids(self, groups=None, protocol='search_split1', purposes='enroll', model_ids=None):
    """Returns a list of model ids for the specific query by the user.

    Keyword Parameters:

    groups
      Ignored; only model ids from the 'dev' group will be used.

    protocol
      One of the available protocol names, see :py:meth:`protocol_names`.

    purposes

    Returns: A list containing all the model ids for the given protocol.
    """

    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())
    groups = self.check_parameters_for_validity(groups, "group", self.groups())
    purposes = self.check_parameters_for_validity(purposes, "purpose", ["enroll","probe"])

    ids = []
    if "search" in protocol:
      for p in purposes:
        self._load_data(protocol, "dev", p)
        ids.extend([t for t in self.memory_db[protocol][p]])
    else:
      self._load_data(protocol, "dev", "")
      for p in purposes:

        if p == "enroll":
          for c in self.memory_db[protocol]['comparisons']:
            ids.append(c)
        else:
          if(model_ids is None):
            for c in self.memory_db[protocol]['comparisons']:
              for probe in self.memory_db[protocol]['comparisons'][c]:
                ids.append(probe)
          else:
            for c in model_ids:
              for probe in self.memory_db[protocol]['comparisons'][c]:
                ids.append(probe)

    return ids



  def template_ids(self, protocol='search_split1'):
    """Returns a list of valid template ids, where :py:class:`Template`'s can be used both for model enrollment or probing.

    This function returns a list of actual template_ids.
    The according templates might differ between the protocols.
    """
    return self.model_ids(protocol)



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

    # collect the queries
    objects = []
    if 'world' in groups:
      self._load_data(protocol, "world", "train")
      objects.extend([o for t in self.memory_db[protocol]['train'] for o in self.memory_db[protocol]['train'][t].files ])

    if 'dev' in groups:

      #Dealing with the search protocol
      if "search" in protocol:
        if 'enroll' in purposes:
          self._load_data(protocol, "dev", "enroll")

          if(model_ids is None):
            objects.extend([o for t in self.memory_db[protocol]['enroll'] for o in self.memory_db[protocol]['enroll'][t].files])
          else:
            objects.extend([o for t in model_ids for o in self.memory_db[protocol]['enroll'][t].files])


        if 'probe' in purposes:
          self._load_data(protocol, "dev", "probe")

          #The probes for the search are the same for all users
          objects.extend([o for t in self.memory_db[protocol]['probe'] for o in self.memory_db[protocol]['probe'][t].files])


      #Dealing with comparisons
      else:

        self._load_data(protocol, "dev", "")

        if 'enroll' in purposes:

          if model_ids is None:
            for c in self.memory_db[protocol]['comparisons']:
              objects.extend(self.memory_db[protocol]['comparison-templates'][c].files)
          else:
            for m in model_ids:
              objects.extend(self.memory_db[protocol]['comparison-templates'][m].files)


        if 'probe' in purposes:
          if(model_ids is None):
            for t in self.memory_db[protocol]['comparison-templates']:
              objects.extend(self.memory_db[protocol]['comparison-templates'][t].files)
            #import ipdb; ipdb.set_trace();
            #raise ValueError("`model_ids` parameter required for the protocol `{0}`. For the comparison protocols, each model has an specific set of probes.".format(protocol))
          else:
            for c in model_ids:
              for probe in self.memory_db[protocol]['comparisons'][c]:
                objects.extend(self.memory_db[protocol]['comparison-templates'][probe].files)


    # we have collected all queries, now extract the File objects
    return objects


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

    # check that every parameter is as expected
    #groups = self.check_parameters_for_validity(groups, "group", ["dev","world"])
    purposes = self.check_parameters_for_validity(purposes, "purpose", ["enroll","probe"])
    protocol = self.check_parameter_for_validity(protocol, "protocol", self.protocol_names())

    templates = []
    self._load_data(protocol, "dev", "enroll")
    self._load_data(protocol, "dev", "probe")
    for p in purposes:
      for m in model_ids:
        if "probe" in p:
          template_ids = self.model_ids(groups="dev", protocol=protocol, purposes=p, model_ids=[m])
          if "search" in protocol:
            for t in template_ids:
              templates.append(self.memory_db[protocol][p][t])
          else:
             for t in template_ids:
               templates.append(self.memory_db[protocol]['comparison-templates'][t])

        else:
          templates.extend(self.memory_db[protocol][p][m])

    return templates



  def annotations(self, file):
    """Returns the annotations for the given :py:class:`File` object as a
    dictionary, see :py:func:`read_annotations` for details.
    """

    return file.annotations


  def protocol_names(self):
    """Returns all registered protocol names, which are usually ``['NoTrain'] + ['split%d' for d in range(1,11)]``"""
    return self.protocols()


  def protocols(self):
    """Returns all possible protocols."""

    protocol_choices = ['search_split%d' % d for d in range(1,11)]
    protocol_choices += ['compare_split%d' % d for d in range(1,11)]

    return protocol_choices



  def has_protocol(self, name):
    """Tells if a certain protocol is available"""
    return name in self.protocols()


  def get_client_id_from_model_id(self, model_id):

    # Since we don't have the protocol information we have to load them all
    # TODO: Last minute solution for this problem, think in a better solution
    for p in self.protocols():
      if "search" in p:
        self._load_data(p, "dev", "enroll")
        self._load_data(p, "dev", "probe")
      else:
        self._load_data(p, "dev", "")

    return self.templates[model_id].client_id



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
    file_name = file.make_path(self.original_directory, file.extension)
    if not check_existence or os.path.exists(file_name):
      return file_name
    raise ValueError("The file '%s' was not found. Please check the original directory '%s'?" % (file_name, self.original_directory))
