from surfigures import __version__
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(description='Create figures of surfaces and vertex-wise data',
                        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')

parser.add_argument('-s', '--suffix', default='.txt', type=str,
                    help='file extension of vertex-wise data file inputs')
parser.add_argument('-o', '--output', default='{}.png', type=str,
                    help='output file template and file type. "{}" is replaced by the subject name.')

parser.add_argument('-r', '--range', default='.disterr.txt:-2.0:2.0,.abs.disterr.txt:0.0:2.0,.smtherr.txt:0.0:2.0',
                    type=str, help='Ranges for specific file extensions.')
parser.add_argument('--min', type=str, default='0.0', help='Default range minimum value')
parser.add_argument('--max', type=str, default='10.0', help='Default range maximum value')
parser.add_argument('-b', '--background-color', type=str, default='white',
                    help='Figure background color')
parser.add_argument('-f', '--font-color', type=str, default='green',
                    help='Figure labels font color')
parser.add_argument('-c', '--color-map', type=str, default='spectral',
                    help='color map to use for data value visualization')
