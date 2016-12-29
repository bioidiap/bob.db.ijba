#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

from __future__ import print_function

"Evaluates the score files and computes EER, HTER and plots CMC and ROC curves"

import bob.measure

import argparse
import numpy, math
import os

# matplotlib stuff
import matplotlib; matplotlib.use('pdf') #avoids TkInter threaded start
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages

# enable LaTeX interpreter
matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif')
matplotlib.rc('lines', linewidth = 4)
# increase the default font size
matplotlib.rc('font', size=18)

import bob.core
logger = bob.core.log.setup("bob.bio.base")


def command_line_arguments(command_line_parameters):
  """Parse the program options"""

  # set up command line parser
  parser = argparse.ArgumentParser(description=__doc__,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

  parser.add_argument('-d', '--dev-files', required=True, nargs='+', help = "A list of score files of the development set.")
  #parser.add_argument('-e', '--eval-files', nargs='+', help = "A list of score files of the evaluation set; if given it must be the same number of files as the --dev-files.")

  parser.add_argument('-s', '--directory', default = '.', help = "A directory, where to find the --dev-files and the --eval-files")

  parser.add_argument('-c', '--criterion', choices = ('EER', 'HTER'), help = "If given, the threshold of the development set will be computed with this criterion.")
  #parser.add_argument('-x', '--cllr', action = 'store_true', help = "If given, Cllr and minCllr will be computed.")
  #parser.add_argument('-m', '--mindcf', action = 'store_true', help = "If given, minDCF will be computed.")
  parser.add_argument('--cost', default=0.99,  help='Cost for FAR in minDCF')
  parser.add_argument('-r', '--rr', action = 'store_true', help = "If given, the Recognition Rate will be computed.")
  parser.add_argument('-l', '--legends', nargs='+', help = "A list of legend strings used for ROC, CMC and DET plots; THE NUMBER OF PLOTS SHOULD BE MULTIPLE OF THE NUMBER OF LEGGENDS. IN THAT WAY, EACH SEGMENT WILL BE AVERAGED")
  parser.add_argument('-F', '--legend-font-size', type=int, default=18, help = "Set the font size of the legends.")
  parser.add_argument('-P', '--legend-position', type=int, help = "Set the font size of the legends.")
  parser.add_argument('-R', '--roc', help = "If given, ROC curves will be plotted into the given pdf file.")
  parser.add_argument('-D', '--det', help = "If given, DET curves will be plotted into the given pdf file.")
  parser.add_argument('-C', '--cmc', help = "If given, CMC curves will be plotted into the given pdf file.")
  parser.add_argument('--parser', default = '4column', choices = ('4column', '5column'), help="The style of the resulting score files. The default fits to the usual output of score files.")

  # add verbose option
  bob.core.log.add_command_line_option(parser)

  # parse arguments
  args = parser.parse_args(command_line_parameters)

  # set verbosity level
  bob.core.log.set_verbosity_level(logger, args.verbose)


  # some sanity checks:
  # update legends when they are not specified on command line
  if args.legends is None:
    args.legends = [f.replace('_', '-') for f in args.dev_files]
    logger.warn("Legends are not specified; using legends estimated from --dev-files: %s", args.legends)

  # check that the legends have the same length as the dev-files
  if (len(args.dev_files) % len(args.legends)) != 0:
    logger.error("The number of --dev-files (%d) is not multiple of --legends (%d) ", len(args.dev_files), len(args.legends))

  return args


def _plot_roc(scores_input, colors, labels, title, fontsize=18, position=None):
  if position is None: position = 4
  figure = pyplot.figure()

  logger.info("Computing CAR curves on the development " )
  fars = [math.pow(10., i * 0.25) for i in range(-16,0)] + [1.]
  frrs = [bob.measure.roc_for_far(scores[0], scores[1], fars) for scores in scores_input]

  offset = 0
  step   = int(len(scores_input)/len(labels))

  #For each group of labels
  for i in range(len(labels)):

    frrs_accumulator = numpy.zeros((step,frrs[0][0].shape[0]))
    fars_accumulator = numpy.zeros((step,frrs[0][1].shape[0]))
    for j in range(offset,offset+step):
      frrs_accumulator[j-i*step,:] = frrs[j][0]
      fars_accumulator[j-i*step,:] = frrs[j][1]

    frr_average = numpy.mean(frrs_accumulator, axis=0)
    far_average = numpy.mean(fars_accumulator, axis=0); far_std = numpy.std(fars_accumulator, axis=0)

    pyplot.semilogx(frr_average*100, 100. - 100.0*far_average, color=colors[i], lw=2, ms=10, mew=1.5, label=labels[i])
    pyplot.errorbar(frr_average*100, 100. - 100.0*far_average, far_std*100, lw=0.5, ms=10)

    offset += step

  # plot FAR and CAR for each algorithm
  #for i in range(len(frrs)):
    #pyplot.semilogx([100.0*f for f in frrs[i][0]], [100. - 100.0*f for f in frrs[i][1]], color=colors[i+1], lw=0.5, ls='--', ms=10, mew=1.5, label=str(i))

  # finalize plot
  pyplot.plot([0.1,0.1],[0,100], "--", color=(0.3,0.3,0.3))
  pyplot.axis([frrs[0][0][0]*100,100,0,100])
  pyplot.xticks((0.01, 0.1, 1, 10, 100), ('0.01', '0.1', '1', '10', '100'))
  pyplot.xlabel('FAR (\%)')
  pyplot.ylabel('CAR (\%)')
  pyplot.grid(True, color=(0.6,0.6,0.6))
  pyplot.legend(loc=position, prop = {'size':fontsize})
  pyplot.title(title)

  return figure


def _plot_det(scores_input, colors, labels, title, fontsize=18, position=None):
  if position is None: position = 1
  # open new page for current plot
  figure = pyplot.figure(figsize=(8.2,8))

  dets = [bob.measure.det(scores[0], scores[1], 1000) for scores in scores_input]

  offset = 0
  step   = int(len(scores_input)/len(labels))

  #For each group of labels
  for i in range(len(labels)):

    frrs_accumulator = numpy.zeros((step,dets[0][0].shape[0]))
    fars_accumulator = numpy.zeros((step,dets[0][1].shape[0]))
    for j in range(offset,offset+step):
      frrs_accumulator[j,:] = dets[j][0]
      fars_accumulator[j,:] = dets[j][1]
    frr_average = numpy.mean(frrs_accumulator, axis=0)
    far_average = numpy.mean(fars_accumulator, axis=0); far_std = numpy.std(fars_accumulator, axis=0)

    pyplot.plot(frr_average, far_average, color=colors[i], lw=2, ms=10, mew=1.5, label=labels[i])
    pyplot.errorbar(frr_average, far_average, far_std, lw=0.5, ms=10)
    offset += step

  # plot the DET curves
  #for i in range(len(dets)):
    #pyplot.plot(dets[i][0], dets[i][1], color=colors[i], lw=0.5, ls="--", ms=10, mew=1.5, label=str(i))

  # change axes accordingly
  det_list = [0.0002, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.7, 0.9, 0.95]
  ticks = [bob.measure.ppndf(d) for d in det_list]
  labels = [("%.5f" % (d*100)).rstrip('0').rstrip('.') for d in det_list]
  pyplot.xticks(ticks, labels)
  pyplot.yticks(ticks, labels)
  pyplot.axis((ticks[0], ticks[-1], ticks[0], ticks[-1]))

  pyplot.xlabel('FAR (\%)')
  pyplot.ylabel('FRR (\%)')
  pyplot.legend(loc=position, prop = {'size':fontsize})
  pyplot.title(title)

  return figure

def _plot_cmc(cmcs, colors, labels, title, fontsize=18, position=None):
  if position is None: position = 4
  # open new page for current plot
  figure = pyplot.figure()

  offset = 0
  step   = int(len(cmcs)/len(labels))

  #For each group of labels
  max_x   =  0 #Maximum CMC size
  for i in range(len(labels)):

    #Computing the CMCs
    cmc_curves = []
    for j in range(offset,offset+step):
      cmc_curves.append(bob.measure.cmc(cmcs[j]))
      max_x = max(len(cmc_curves[j-offset]), max_x)

    #Adding the padding with '1's
    cmc_accumulator = numpy.zeros(shape=(step,max_x), dtype='float')
    for j in range(step):
      padding_diff =  max_x-len(cmc_curves[j])
      cmc_accumulator[j,:] = numpy.pad(cmc_curves[j],(0,padding_diff), 'constant',constant_values=(1))
      #cmc_average  += numpy.pad(cmc_curves[j],(0,padding_diff), 'constant',constant_values=(1))
    cmc_std     = numpy.std(cmc_accumulator, axis=0); cmc_std[-1]
    cmc_average = numpy.mean(cmc_accumulator, axis=0)

    pyplot.semilogx(range(1, cmc_average.shape[0]+1), cmc_average * 100, lw=2, ms=10, mew=1.5, label=labels[i])
    pyplot.errorbar(range(1, cmc_average.shape[0]+1), cmc_average*100, cmc_std*100, lw=0.5, ms=10)
    offset += step

  # change axes accordingly
  ticks = [int(t) for t in pyplot.xticks()[0]]
  pyplot.xlabel('Rank')
  pyplot.ylabel('Probability (\%)')
  pyplot.xticks(ticks, [str(t) for t in ticks])
  pyplot.axis([0, max_x, 0, 100])
  pyplot.legend(loc=position, prop = {'size':fontsize})
  pyplot.title(title)
  pyplot.grid(True)

  return figure


def main(command_line_parameters=None):
  """Reads score files, computes error measures and plots curves."""

  args = command_line_arguments(command_line_parameters)

  # get some colors for plotting
  cmap = pyplot.cm.get_cmap(name='hsv')
  colors = [cmap(i) for i in numpy.linspace(0, 1.0, len(args.dev_files)+1)]

  if args.criterion or args.roc or args.det:
    score_parser = {'4column' : bob.measure.load.split_four_column, '5column' : bob.measure.load.split_five_column}[args.parser]

    # First, read the score files
    logger.info("Loading %d score files of the development set", len(args.dev_files))
    scores_dev = [score_parser(os.path.join(args.directory, f)) for f in args.dev_files]


    if args.criterion:
      logger.info("Computing %s on the development " % args.criterion )
      for i in range(len(scores_dev)):
        # compute threshold on development set
        threshold = {'EER': bob.measure.eer_threshold, 'HTER' : bob.measure.min_hter_threshold} [args.criterion](scores_dev[i][0], scores_dev[i][1])
        # apply threshold to development set
        far, frr = bob.measure.farfrr(scores_dev[i][0], scores_dev[i][1], threshold)
        print("The %s of the development set of '%s' is %2.3f%%" % (args.criterion, args.legends[i], (far + frr) * 50.)) # / 2 * 100%



    if args.roc:
      logger.info("Plotting ROC curves to file '%s'", args.roc)
      try:
        # create a multi-page PDF for the ROC curve
        pdf = PdfPages(args.roc)
        # create a separate figure for dev and eval
        pdf.savefig(_plot_roc(scores_dev, colors, args.legends, "ROC curve for development set", args.legend_font_size, args.legend_position))
        #del frrs_dev
        pdf.close()
      except RuntimeError as e:
        raise RuntimeError("During plotting of ROC curves, the following exception occured:\n%s\nUsually this happens when the label contains characters that LaTeX cannot parse." % e)

    if args.det:
      logger.info("Computing DET curves on the development ")
      #dets_dev = [bob.measure.det(scores[0], scores[1], 1000) for scores in scores_dev]

      logger.info("Plotting DET curves to file '%s'", args.det)
      try:
        # create a multi-page PDF for the ROC curve
        pdf = PdfPages(args.det)
        # create a separate figure for dev and eval
        pdf.savefig(_plot_det(scores_dev, colors, args.legends, "DET plot for development set", args.legend_font_size, args.legend_position))
        #del dets_dev
        pdf.close()
      except RuntimeError as e:
        raise RuntimeError("During plotting of ROC curves, the following exception occured:\n%s\nUsually this happens when the label contains characters that LaTeX cannot parse." % e)


  if args.cmc or args.rr:
    logger.info("Loading CMC data on the development ")
    cmc_parser = {'4column' : bob.measure.load.cmc_four_column, '5column' : bob.measure.load.cmc_five_column}[args.parser]
    cmcs_dev = [cmc_parser(os.path.join(args.directory, f)) for f in args.dev_files]

  if args.cmc:
    logger.info("Plotting CMC curves to file '%s'", args.cmc)
    try:
      # create a multi-page PDF for the ROC curve
      pdf = PdfPages(args.cmc)
      # create a separate figure for dev and eval
      pdf.savefig(_plot_cmc(cmcs_dev, colors, args.legends, "CMC curve for development set", args.legend_font_size, args.legend_position))
      pdf.close()
    except RuntimeError as e:
      raise RuntimeError("During plotting of ROC curves, the following exception occured:\n%s\nUsually this happens when the label contains characters that LaTeX cannot parse." % e)

  if args.rr:
    logger.info("Computing recognition rate on the development ")
    for i in range(len(cmcs_dev)):
      rr = bob.measure.recognition_rate(cmcs_dev[i])
      print("The Recognition Rate of the development set of '%s' is %2.3f%%" % (args.legends[i], rr * 100.))

