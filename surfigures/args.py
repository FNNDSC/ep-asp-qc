from surfigures import __version__
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

parser = ArgumentParser(description='Create figures of surfaces and vertex-wise data',
                        formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')

parser.add_argument('-s', '--suffix', default='.txt', type=str,
                    help='file extension of vertex-wise data file inputs')
parser.add_argument('-o', '--output', default='{}.png', type=str,
                    help='output file template and file type. "{}" is replaced by the subject name.')

# TODO: feature bloat.
# This should be its own ChRIS plugin, https://github.com/FNNDSC/pl-abs
# but I'm doing it here in Python because I am out of time!
parser.add_argument('-a', '--abs', default='.disterr.txt', type=str,
                    help='file extension of input files which should have their absolute values be taken.')

parser.add_argument('-r', '--range', default='.disterr.txt:-2.0:2.0,.smtherr.txt:0.0:2.0',
                    type=str, help='Ranges for specific file extensions.')
parser.add_argument('--min', type=str, default='0.0', help='Default range minimum value')
parser.add_argument('--max', type=str, default='10.0', help='Default range maximum value')
