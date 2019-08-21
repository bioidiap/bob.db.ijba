#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""
WARNING!!!! THIS IS DEPRECATED

Converts the 4 columns score format to the NIST format.

Each row of the NIST format is composed of the following fields:

 * ENROLL_TEMPLATE_ID
 * VERIF_TEMPLATE_ID
 * ENROLL_TEMPLATE_SIZE_BYTES
 * VERIF_TEMPLATE_SIZE_BYTES
 * RETCODE
 * SIMILARITY_SCORE


Usage:

  score_generation.py <input-scores> <output-scores> [--template-size=<n>]
  score_generation.py -h | --help


Arguments:

  <input-scores>   Path to input score files
  <output-scores>  Path to output score files


Options:

  -h --help            Show this screen.
  --template-size=<n>  The default template size in BYTES [default: 100]

"""


from docopt import docopt
import bob.bio.base
import os
import bob.io.base


def main(command_line_parameters=None):

  args = docopt(__doc__, version='NIST Score Generation')

  template_size = int(args['--template-size'])
  output_file   = args['<output-scores>']

  bob.io.base.create_directories_safe(os.path.dirname(output_file))

  print("Writing scores in {0}".format(output_file))

  f = open(output_file,'w')
  f.write('ENROLL_TEMPLATE_ID VERIF_TEMPLATE_ID ENROLL_TEMPLATE_SIZE_BYTES VERIF_TEMPLATE_SIZE_BYTES RETCODE SIMILARITY_SCORE\n')
  for template_id,probe_id,template_file,score in bob.bio.base.score.load.four_column(args['<input-scores>']):
    f.write("{0} {1} {2} {3} 0 {4}\n".format(template_id, probe_id, template_size, template_size, score))

  del f
  print("Done!")
