#!/usr/bin/env python
import os
import sys
from pathlib import Path
import itertools

from loguru import logger
from chris_plugin import chris_plugin

from surfigures import DISPLAY_TITLE, __version__
from surfigures.args import parser
from surfigures.options import Options
from surfigures.inputs.find import SubjectMapper
from concurrent.futures import ThreadPoolExecutor

from surfigures.run import run_surfigures


@chris_plugin(
    parser=parser,
    title='MNI Surfaces Figures',
    category='Visualization',
    min_memory_limit='500Mi',
    min_cpu_limit='1000m',
    min_gpu_limit=0
)
def main(given_args, inputdir: Path, outputdir: Path):
    print(DISPLAY_TITLE, file=sys.stderr)
    print(f'\tversion: {__version__}\n', file=sys.stderr, flush=True)

    options = Options.from_args(given_args)

    mapper = SubjectMapper(input_dir=inputdir, output_dir=outputdir)
    usable_mapper, skipped_inputs = zip(*mapper.map(given_args.suffix, given_args.output))

    skipped_inputs = list(filter(is_some, skipped_inputs))
    if skipped_inputs:
        logger.error('Unable to resolve inputs: {}', skipped_inputs)
        sys.exit(1)

    nproc = len(os.sched_getaffinity(0))
    logger.debug('Using {} threads', nproc)

    with ThreadPoolExecutor(max_workers=nproc) as pool:
        timings = pool.map(__call_surfigures, filter(is_some, usable_mapper), itertools.repeat(options))

    timings = list(timings)
    if any(t is None for t in timings):
        logger.warning("errors occurred, see above.")
        sys.exit(1)
    average = sum(timings) / len(timings)
    logger.info(f'All done! Average time: {average:.1f}s')


def __call_surfigures(t, o):
    return run_surfigures(*t, o)


def is_some(x):
    return x is not None


if __name__ == '__main__':
    main()
