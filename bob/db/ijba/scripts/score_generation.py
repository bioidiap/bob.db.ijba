#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Tiago de Freitas Pereira<tiago.pereira@idiap.ch>
# Thu 12 Nov 2015 17:05:18 CET 
#
# Copyright (C) 2011-2013 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the ipyplotied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Converts the 4 columns score format to the NIST format.
The format is the following:

ENROLL_TEMPLATE_ID VERIF_TEMPLATE_ID ENROLL_TEMPLATE_SIZE_BYTES VERIF_TEMPLATE_SIZE_BYTES RETCODE SIMILARITY_SCORE

Usage:
  score_generation.py <input-score-file> <output-score-file> [--template-size=<n>]
  score_generation.py -h | --help

Options:
  -h --help     Show this screen.
  --template-size=<n>     The default template size in BYTES [default: 100]
  
"""

from docopt import docopt
import bob.measure
import os
import bob.io.base

def main(command_line_parameters=None):

  args = docopt(__doc__, version='NIST Score Generation')  
  
  template_size = int(args['--template-size'])
  output_file   = args['<output-score-file>']
  
  bob.io.base.create_directories_safe(os.path.dirname(output_file))
  
  print("Writing scores in {0}".format(output_file))
  
  f = open(output_file,'w')
  f.write('ENROLL_TEMPLATE_ID VERIF_TEMPLATE_ID ENROLL_TEMPLATE_SIZE_BYTES VERIF_TEMPLATE_SIZE_BYTES RETCODE SIMILARITY_SCORE\n')
  for template_id,probe_id,template_file,score in bob.measure.load.four_column(args['<input-score-file>']):
    f.write("{0} {1} {2} {3} 0 {4}\n".format(template_id, probe_id, template_size, template_size, score))
    
  del f
  print("Done!!!")
  

if __name__ == "__main__":
  main()
