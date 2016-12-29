#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""This is the Bob database entry for the JANUS database.
"""

from .query import Database
from .reader import get_templates

#from .models import Client, File, Annotation, Template, Protocol, Comparisons, Protocol_Template_Association
#, File_Template_Association

def get_config():
  """Returns a string containing the configuration information.
  """
  import bob.extension
  return bob.extension.get_config(__name__)


# gets sphinx autodoc done right - don't remove it
__all__ = [_ for _ in dir() if not _.startswith('_')]
