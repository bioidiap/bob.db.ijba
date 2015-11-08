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

"""Table models and functionality for the JANUS database.
"""

import sqlalchemy
from sqlalchemy import Table, Column, Integer, Float, String, Boolean, ForeignKey, or_, and_, not_
from bob.db.base.sqlalchemy_migration import Enum, relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base
import os

import bob.db.verification.utils

Base = declarative_base()


""" Defining protocols. Yes, they are static """
GROUPS    = ('world', 'dev')


class Client(Base):
  """The subjects of the JANUS database.

  Each subject contains exactly the ID that is identical with the subject_id of the JANUS database.
  Furthermore, after creation of the database, the list of :py:class:`Template`'s and the list of :py:class:`File`'s of this subject is available using ``self.templates`` and ``self.files``.
  """
  __tablename__ = 'client'

  id = Column(Integer, primary_key=True)

  def __init__(self, subject_id):
    self.id = subject_id


class Annotation(Base):
  """Annotations of the JANUS database consists at least of the ``topleft`` corner of the bounding box and its according ``size``.
  There is exactly one annotation for each :py:class:`File`, which after creation of the database can be obtained using ``self.file``.
  Note that there might be several annotations for each physical image file.
  Please use only the faces specified by the bounding box, all others do not belong to the face recognition protocol.

  Additional to the bounding box, three facial feature points might be labeled, the left and right eye ``leye, reye`` as well as the nose base ``nose`` (which is actually the nose tip).
  Also, a face ``yaw`` angle is annotated.

  Finally, some flags with integral values are given.
  For the exact meaning of these values, please refer to the JANUS database report:

  - ``forhead-visible``
  - ``eyes-visible``
  - ``nose-mouth-visible``
  - ``indoor``
  - ``gender``
  - ``skin-tone``
  - ``age``
  """
  __tablename__ = 'annotation'

  id = Column(Integer, primary_key=True)
  file_id = Column(Integer, ForeignKey('file.id'))

  tl_x = Column(Float) # top-left position
  tl_y = Column(Float)
  size_x = Column(Float) # size of face
  size_y = Column(Float)
  le_x = Column(Float) # left eye
  le_y = Column(Float)
  re_x = Column(Float) # right eye
  re_y = Column(Float)
  n_x = Column(Float) # nose base
  n_y = Column(Float)
  yaw = Column(Float) # face yaw
  forehead = Column(Integer) # forehead visible
  eyes = Column(Integer) # eyes visible
  nm = Column(Integer) # nose mouth visible
  indoor = Column(Integer) # indoor
  gender = Column(Integer) # gender
  skin = Column(Integer) # skin tone
  age = Column(Integer) # age (not the real age, but some age indicator)

  def __init__(self, file_id, annotations, extras):
    self.file_id = file_id

    assert len(annotations) == 11
    assert len(extras) == 7
    # assert that at least the face bounding box is labeled
    assert not any(a is None for a in annotations[:4])
    self.tl_x = annotations[0]
    self.tl_y = annotations[1]
    self.size_x = annotations[2]
    self.size_y = annotations[3]
    self.re_x = annotations[4]
    self.re_y = annotations[5]
    self.le_x = annotations[6]
    self.le_y = annotations[7]
    self.n_x = annotations[8]
    self.n_y = annotations[9]
    self.yaw = annotations[10]
    self.forehead = extras[0]
    self.eyes = extras[1]
    self.nm = extras[2]
    self.indoor = extras[3]
    self.gender = extras[4]
    self.skin = extras[5]
    self.age = extras[6]

  def __call__(self):
    """Returns the annotations of this database in a dictionary, such as {'reye' : (re_y, re_x), 'leye' : (le_y, le_x), 'topleft' : (tl_y, tl_x), 'bottomright' : (br_y, br_x)} and some more.
    The actual annotations might change between Files.
    Note that some of the annotations might be ``None``, tuples of ``None`` or absent.
    """
    annots = {
      'topleft' : (self.tl_y, self.tl_x),
      'size' : (self.size_y, self.size_x),
      'bottomright' : (self.tl_y + self.size_y, self.tl_x + self.size_x),
      'forehead-visible' : self.forehead,
      'eyes-visible' : self.eyes,
      'nose-mouth-visible' : self.nm,
      'indoor' : self.indoor,
      'gender' : self.gender,
      'skin-tone' : self.skin,
      'age' : self.age
    }

    if all(a is not None for a in (self.re_y, self.re_x)): annots['reye'] = (self.re_y, self.re_x)
    if all(a is not None for a in (self.le_y, self.le_x)): annots['leye'] = (self.le_y, self.le_x)
    if all(a is not None for a in (self.n_y, self.n_x)): annots['nose'] = (self.n_y, self.n_x)
    if self.yaw is not None: annots['yaw'] = self.yaw

    return annots

  def __repr__(self):
    return "<Annotation('%d')>" % self.file_id


class File(Base, bob.db.verification.utils.File):
  """Information about the files of the JANUS database.

  Note that there might be several ``File`` objects for each physical file of the JANUS database.
  To make the :py:meth:`make_path` function generate a unique filename for this actual ``File`` object, the ``sighting_id`` might be appended to the real file name.

  Each File includes:

  * the ``media_id`` (the name of the image or video without frame number)
  * the ``sighting_id`` (to identify different faces in the same image)
  * the ``frame`` number (might be None if not a video)
  * the ``client_id`` (aka, the subject id)
  * the ``path`` excluding filename extension
  * the filename ``extension`` of the original file
  * a numerical ``id``, used as a unique key for the SQL query only

  Additionally, some fields will be available, once the database is created:

  * ``templates``: a list of :py:class:`Template`'s, in which this file is used
  * ``annotation``: the :py:class:`Annotation`, which belongs to this file

  """
  import itertools

  __tablename__ = 'file'

  id = Column(Integer, primary_key=True)
  path = Column(String(100))
  extension = Column(Enum(".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG"))

  media_id = Column(Integer)
  sighting_id = Column(Integer)
  client_id = Column(Integer, ForeignKey('client.id'))
  frame = Column(Integer)

  # one-to-one relationship between annotations and files
  annotation = relationship("Annotation", backref=backref("file", order_by=id, uselist=False), uselist=False)

  def __init__(self, path, client_id, media_id, sighting_id, frame):

    path_, self.extension = os.path.splitext(path)

    # call base class constructor
    bob.db.verification.utils.File.__init__(self, client_id = client_id, path = path_)

    # set the data
    self.media_id = media_id
    self.frame = frame
    self.sighting_id = sighting_id

  def make_path(self, directory = None, extension = None, add_sighting_id = True):
    """Wraps the current path so that a complete path is formed.
    By default, the file name will be a unique file name, as there might be several ``File`` objects with the same path.
    To get the original file name, please use the :py:meth:`Database.original_file_name` function instead, or set the ``add_sighting_id`` flag to ``False``.

    Keyword parameters:

    directory : str or ``None``
      An optional directory name that will be prefixed to the returned result.

    extension : str or ``None``
      An optional extension that will be suffixed to the returned filename.
      The extension normally includes the leading ``.`` character as in ``.jpg`` or ``.hdf5``.

    add_sighting_id : bool
      By default, the sighting_id is added to generate a unique path.
      If set to false, the sighting_id will not be added.

    Returns a string containing the newly generated file path, which by default is unique.
    """

    # assure that directory and extension are actually strings
    if not directory: directory = ''
    if not extension: extension = ''
    path = "%s-%d%s" % (self.path, self.sighting_id, extension) if add_sighting_id else "%s%s" % (self.path, extension)
    # create the path
    return str(os.path.join(directory, path))


#Defines a bi-directional relation between A ProtocolPurpose and a Template
#file_template_association = Table(
#    'file_template_association',
#    Base.metadata,
#    Column('file_id', Integer, ForeignKey('file.id')),
#    Column('template_id', Integer, ForeignKey('template.id'))
#)


class File_Template_Association(Base):
  """
  Defines a bi-directional relation between A ProtocolPurpose and a Template
  """
  __tablename__ = 'file_template_association'

  protocol_id = Column('file_id', Integer, ForeignKey('file.id'), primary_key=True)
  template_id = Column('template_id', Integer, ForeignKey('template.id'), primary_key=True)  

  def __init__(self, file_id, template_id):
    self.file_id     = file_id
    self.template_id = template_id


class Template(Base):
  """A ``Template`` contains a list of :py:class:`File` objects belonging to the same subject (there might be several templates per subject).
  These are listed in the ``self.files`` field.

  A ``Template`` can serve for training, model enrollment, or for probing.
  Each template belongs specifically to a certain protocol, as the template_id in the original file lists might differ for different protocols.
  The according :py:class:`ProtocolPurpose` can be obtained using the ``self.protocol_purpose`` after creation of the database.

  Note that the ``template_id`` corresponds to the template_id of the file lists, while the ``id`` is only used as a unique key for querying the database.
  For convenience, the template also contains a ``path``, which is a concatenation of the first :py:attr:`File.media_id` of the first file, and the ``self.template_id``, making it unique (at least per protocol).
  """
  __tablename__ = 'template'

  id = Column(Integer, primary_key=True)
  template_id = Column(String(100)) #TIAGO: Here I will add a tag called T for the data from the training set
  client_id = Column(Integer, ForeignKey('client.id')) # aka the subject ID
  path = Column(String(100)) # only used to write into score files

  client = relationship("Client", backref=backref("templates", order_by=id), uselist=False)
  files = relationship("File", secondary="file_template_association", backref=backref("templates", order_by=id))

  def __init__(self, template_id, subject_id):
    self.template_id = template_id
    self.client_id = subject_id

  def add_file(self, file):
    self.files.append(file)
    # set template path, if not yet specified
    if self.path is None:
      self.path = "%s-%s" % (file.media_id, self.template_id)


class Protocol(Base):
  """The protocols of the JANUS database.

  There are 11 different protocols defined.
  The first, which we call ``NoTrain``, contains no training set, but all 500 subjects are used as gallery (enrollment) and probing.
  The remaining 10 protocols split up these Templates into training, enrollment and probe, using 10 randomized splits.
  Please report the recognition rates for each of the splits independently.
  """
  __tablename__ = 'protocol'

  # query protocols start from index 2
  protocol_choices = ['search_split%d' % d for d in range(1,11)]
  protocol_choices += ['compare_split%d' % d for d in range(1,11)]  

  id = Column(Integer, primary_key=True)
  name = Column(Enum(*protocol_choices), unique=True)

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "<Protocol('%d', '%s')>" % (self.id, self.name)



class Protocol_Template_Association(Base):
  """
  Describe the protocols
  """
  __tablename__ = 'protocol_template_association'

  group_choices = GROUPS

  protocol_id = Column('protocol_id', Integer, ForeignKey('protocol.id'), primary_key=True)
  template_id = Column('template_id', Integer, ForeignKey('template.id'), primary_key=True)  
  group    = Column('group', Enum(*GROUPS), primary_key=True)

  def __init__(self, protocol_id, template_id, group):
    self.protocol_id  = protocol_id
    self.template_id  = template_id
    self.group     = group



class Comparisons(Base):
  """
  Describe the comparisons between templates
  
  BY DEFINITION TEMPLATE_A IS ENROLL and TEMPLATE_B IS PROBE
  
  """
  __tablename__ = 'comparisons'

  protocol = Column('protocol_id', Integer, ForeignKey('protocol.id'), primary_key=True)
  template_A = Column('template_A', Integer, ForeignKey('protocol_template_association.template_id'), primary_key=True)
  template_B = Column('template_B', Integer, ForeignKey('protocol_template_association.template_id'), primary_key=True)  

  def __init__(self, protocol, template_A, template_B):
    self.protocol    = protocol
    self.template_A  = template_A
    self.template_B  = template_B


