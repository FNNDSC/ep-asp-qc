# Surface QC Figure Generation

[![Version](https://img.shields.io/docker/v/fnndsc/pl-surfigures?sort=semver)](https://hub.docker.com/r/fnndsc/pl-surfigures)
[![MIT License](https://img.shields.io/github/license/fnndsc/pl-surfigures)](https://github.com/FNNDSC/pl-surfigures/blob/main/LICENSE)
[![ci](https://github.com/FNNDSC/pl-surfigures/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pl-surfigures/actions/workflows/ci.yml)

![example output](examples/outgoing/same_folder.png)

`pl-surfigures` is a [_ChRIS_](https://chrisproject.org/)
_ds_ plugin which creates PNG figures visualizing MNI .obj surfaces
and vertex-wise data.

## Pipelining

`pl-surfigures` works well for the outputs of
[pl-surfdisterr](https://github.com/FNNDSC/pl-surfdisterr)
and [pl-smoothness-error](https://github.com/FNNDSC/pl-smoothness-error).

Any number of surfaces per subject is supported. For instance:

- 1 surface output from [pl-fetal-surface-extract](https://github.com/FNNDSC/pl-fetal-surface-extract)
- 2 surfaces, WM and GM from [CLASP](https://github.com/FNNDSC/ep-surface_fit_parameterized)
- 3 or more surfaces from... anywhere, for whatever purpose

## Installation

`pl-surfigures` is a _[ChRIS](https://chrisproject.org/) plugin_, meaning it can
run from either within _ChRIS_ or the command-line.

[![Get it from chrisstore.co](https://raw.githubusercontent.com/FNNDSC/ChRIS_store_ui/963938c241636e4c3dc4753ee1327f56cb82d8b5/src/assets/public/badges/light.svg)](https://chrisstore.co/plugin/pl-surfigures)

## Naming Convention

`surfigures` discovers inputs based on naming conventions.
Two conventions are supported:

- left and right surfaces are in the same directory, where file names contain either the words "left" or "right", in the same position. e.g. `subject001/wm_left.obj subject001/wm_right.obj`
- left and right surfaces are in sibling directories. File names are exactly the same, parent directory names must contain either the words "left" or "right", in the same position, e.g. `subject001-left/wm.obj subject001-right/wm.obj`

## Local Usage

To get started with local command-line usage, use [Apptainer](https://apptainer.org/)
(a.k.a. Singularity) to run `pl-surfigures` as a container:

```shell
apptainer exec docker://fnndsc/pl-surfigures surfigures [--args values...] input/ output/
```

To print its available options, run:

```shell
apptainer exec docker://fnndsc/pl-surfigures surfigures --help
```

### Colors

Valid values for the options `--font-color` and `--background-color` are described here: https://imagemagick.org/script/color.php

Valid values for `--color-map` are described in `colour_object -help`.

> gray, hot, hot_inv, cold_metal, cold_metal_inv,
> green_metal, green_metal_inv, lime_metal, lime_metal_inv,
> red_metal, red_metal_inv, purple_metal, purple_metal_inv,
> spectral, red, green, blue, label, rgba

## Examples

`surfigures` requires two positional arguments: a directory containing
input data, and a directory where to create output data.

```shell
apptainer exec docker://fnndsc/pl-surfigures:latest surfigures incoming/ outgoing/
```

For a dark theme:

```shell
apptainer exec docker://fnndsc/pl-surfigures:latest surfigures \
    --font-color green1 --background-color black \
    incoming/ outgoing/
```

Let's say your vertex-wise data files use the file extensions `.area.s5`
and `.depth.s5`, where the range for values of `.area.s5` data are between
0 and 1, and the range for values of `.depth.s5` is `-0.5` to `0.5`.
Use the `--range` option to specify this. The format is`file_extension:min:max`, multiple values are comma-delimited.

```shell
apptainer exec docker://fnndsc/pl-surfigures:latest surfigures \
    --range .area.s5:0.0:1.0,.depth.s5:0.0:5.0 \
    incoming/ outgoing/
```
