#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""This is the Bob database entry for the IJB-A database.
"""

from .query import Database
from .reader import File, Template, get_templates, read_annotations


def get_config():
  """Returns a string containing the configuration information.
  """
  import bob.extension
  return bob.extension.get_config(__name__)


# gets sphinx autodoc done right - don't remove it
def __appropriate__(*args):
  """Says object was actually declared here, an not on the import module.

  Parameters:

    *args: An iterable of objects to modify

  Resolves `Sphinx referencing issues
  <https://github.com/sphinx-doc/sphinx/issues/3048>`
  """
  for obj in args: obj.__module__ = __name__

__appropriate__(
    Database,
    File,
    Template,
    get_templates,
    read_annotations,
    )

__all__ = [_ for _ in dir() if not _.startswith('_')]
