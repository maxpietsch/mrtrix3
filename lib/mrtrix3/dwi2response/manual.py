def usage(base_parser, subparsers): #pylint: disable=unused-variable
  parser = subparsers.add_parser('manual', parents=[base_parser])
  parser.setAuthor('Robert E. Smith (robert.smith@florey.edu.au)')
  parser.setSynopsis('Derive a response function using an input mask image alone (i.e. pre-selected voxels)')
  parser.add_argument('input', help='The input DWI')
  parser.add_argument('in_voxels', help='Input voxel selection mask')
  parser.add_argument('output', help='Output response function text file')
  options = parser.add_argument_group('Options specific to the \'manual\' algorithm')
  options.add_argument('-dirs', help='Manually provide the fibre direction in each voxel (a tensor fit will be used otherwise)')



def checkOutputPaths(): #pylint: disable=unused-variable
  from mrtrix3 import app
  app.checkOutputPath(app.args.output)



def getInputs(): #pylint: disable=unused-variable
  import os
  from mrtrix3 import app, fsys, run
  mask_path = fsys.toTemp('mask.mif', False)
  if os.path.exists(mask_path):
    app.warn('-mask option is ignored by algorithm \'manual\'')
    os.remove(mask_path)
  run.command('mrconvert ' + fsys.fromUser(app.args.in_voxels, True) + ' ' + fsys.toTemp('in_voxels.mif', True))
  if app.args.dirs:
    run.command('mrconvert ' + fsys.fromUser(app.args.dirs, True) + ' ' + fsys.toTemp('dirs.mif', True) + ' -strides 0,0,0,1')



def needsSingleShell(): #pylint: disable=unused-variable
  return False



def execute(): #pylint: disable=unused-variable
  import os, shutil
  from mrtrix3 import app, fsys, image, MRtrixException, run

  shells = [ int(round(float(x))) for x in image.mrinfo('dwi.mif', 'shell_bvalues').split() ]

  # Get lmax information (if provided)
  lmax = [ ]
  if app.args.lmax:
    lmax = [ int(x.strip()) for x in app.args.lmax.split(',') ]
    if not len(lmax) == len(shells):
      raise MRtrixException('Number of manually-defined lmax\'s (' + str(len(lmax)) + ') does not match number of b-value shells (' + str(len(shells)) + ')')
    for l in lmax:
      if l%2:
        raise MRtrixException('Values for lmax must be even')
      if l<0:
        raise MRtrixException('Values for lmax must be non-negative')

  # Do we have directions, or do we need to calculate them?
  if not os.path.exists('dirs.mif'):
    run.command('dwi2tensor dwi.mif - -mask in_voxels.mif | tensor2metric - -vector dirs.mif')

  # Get response function
  bvalues_option = ' -shells ' + ','.join(map(str,shells))
  lmax_option = ''
  if lmax:
    lmax_option = ' -lmax ' + ','.join(map(str,lmax))
  run.command('amp2response dwi.mif in_voxels.mif dirs.mif response.txt' + bvalues_option + lmax_option)

  run.function(shutil.copyfile, 'response.txt', fsys.fromUser(app.args.output, False))
  if app.args.voxels:
    run.command('mrconvert in_voxels.mif ' + fsys.fromUser(app.args.voxels, True) + app.mrconvertOutputOption(fsys.fromUser(app.args.input, True)))
