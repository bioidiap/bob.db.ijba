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

"""Table models and functionality for the CAS-PEAL database.
"""

import sqlalchemy
from sqlalchemy import Table, Column, Integer, Float, String, Boolean, ForeignKey, or_, and_, not_
from bob.db.base.sqlalchemy_migration import Enum, relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base
import os

import bob.db.verification.utils

Base = declarative_base()


class Client(Base):
  """The clients of the JANUS database"""
  __tablename__ = 'client'

  id = Column(Integer, primary_key=True)

  def __init__(self, subject_id):
    self.id = subject_id


class Annotation(Base):
  """Annotations of the CAS-PEAL database consists only of the left and right eye positions.
  There is exactly one annotation for each file."""
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
#    self.br_x = self.tl_x + annotations[2] if annotations[2] is not None else None
#    self.br_y = self.tl_y + annotations[3] if annotations[3] is not None else None
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
    The actual annotations might change between versions.
    Note that some of the annotations might be ``None`` or tuples of ``None``.
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
  """Information about the files of the JANUS database. Each file includes

  * the media id
  * the frame number (might be None if not a video)
  * the template id (i.e., to which template this file belongs)
  * the client id (aka, the subject id), which is stored in the template
  * the path
  """
  import itertools

  __tablename__ = 'file'

  id = Column(Integer, primary_key=True)
#  path = Column(String(100), unique=True)
  path = Column(String(100))
  extension = Column(Enum(".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG"))

  media_id = Column(Integer)
  sighting_id = Column(Integer)
  client_id = Column(Integer)
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
    The file name will be a unique file name, as there might be several file objects with the same path.
    To get the original file name, please use the :py:meth:`Database.original_file_name` function instead.

    Keyword parameters:

    directory : str or None
      An optional directory name that will be prefixed to the returned result.

    extension : str or None
      An optional extension that will be suffixed to the returned filename.
      The extension normally includes the leading ``.`` character as in ``.jpg`` or ``.hdf5``.

    add_sighting_id : bool
      By default, the sighting_id is added to generate a unique path.
      If set to false, the sighting_id will not be added.

    Returns a string containing the newly generated file path.
    """

    # assure that directory and extension are actually strings
    if not directory: directory = ''
    if not extension: extension = ''
    path = "%s-%d%s" % (self.path, self.sighting_id, extension) if add_sighting_id else "%s%s" % (self.path, extension)
    # create the path
    return str(os.path.join(directory, path))


# Defines a bi-directional relation between A ProtocolPurpose and a Template
file_template_association = Table(
    'file_template_association',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('file.id')),
    Column('template_id', Integer, ForeignKey('template.id'))
)


class Template(Base):
  """A file list of File objects belonging to the same template ID (there are several templates per person).
  A template can serve for training, model enrollment, or for probing."""
  __tablename__ = 'template'

  id = Column(Integer, primary_key=True)
  template_id = Column(Integer)
  client_id = Column(Integer, ForeignKey('client.id')) # aka the subject ID
  protocol_purpose_id = Column(Integer, ForeignKey("protocol_purpose.id"))
  path = Column(String(100)) # only used to write into score files

  client = relationship("Client", backref=backref("templates", order_by=id), uselist=False)
  protocol_purpose = relationship("ProtocolPurpose", backref=backref("templates", order_by=id))
  files = relationship("File", secondary=file_template_association, backref=backref("templates", order_by=id))

  def __init__(self, template_id, subject_id, protocol_purpose_id):
    self.template_id = template_id
    self.client_id = subject_id
    self.protocol_purpose_id = protocol_purpose_id
#    self.path = "%s-%s" % (str(subject_id), str(template_id))

  def add_file(self, file):
    self.files.append(file)
    # set template path, if not yet specified
    if self.path is None:
      self.path = "%s-%d" % (file.media_id, self.template_id)


class Protocol(Base):
  """The probe protocols of the CAS-PEAL database. Training and enrollment is identical for all protocols of CAS-PEAL."""
  __tablename__ = 'protocol'

  # query protocols start from index 2
  protocol_choices = ["NoTrain"] + ['split%d' % d for d in range(1,11)]

  id = Column(Integer, primary_key=True)
  name = Column(Enum(*protocol_choices), unique=True)

  def __init__(self, name):
    self.name = name

  def __repr__(self):
    return "<Protocol('%d', '%s')>" % (self.id, self.name)


class ProtocolPurpose(Base):
  """This class defines the groups and purposes, i.e., which templates should be used for which puopose in  each protocol"""
  __tablename__ = "protocol_purpose"

  purpose_choices = ("train", "enroll", "probe")
  group_choices = ("world", "dev")

  id = Column(Integer, primary_key=True)
  purpose = Column(Enum(*purpose_choices))
  sgroup = Column(Enum(*group_choices))
  protocol_id = Column(Integer, ForeignKey("protocol.id"))

  # The protocol using this ProtocolPurpose
  protocol = relationship("Protocol", backref=backref("purposes", order_by=id))

  def __init__(self, purpose, protocol_id):
    if purpose == "gallery": purpose = "enroll"
    self.purpose = purpose
    self.sgroup = self.group_choices[purpose != self.purpose_choices[0]]
    self.protocol_id = protocol_id
