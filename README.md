# ASP Quality Control

[![Version](https://img.shields.io/docker/v/fnndsc/ep-asp-qc?sort=semver)](https://hub.docker.com/r/fnndsc/ep-asp-qc)
[![MIT License](https://img.shields.io/github/license/fnndsc/ep-asp-qc)](https://github.com/FNNDSC/ep-asp-qc/blob/main/LICENSE)
[![ci](https://github.com/FNNDSC/ep-asp-qc/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/ep-asp-qc/actions/workflows/ci.yml)

`ep-asp-qc` is a [_ChRIS_](https://chrisproject.org/)
_ds_ plugin which takes in ...  as input files and
creates ... as output files.

## Abstract

...

## Installation

`ep-asp-qc` is a _[ChRIS](https://chrisproject.org/) plugin_, meaning it can
run from either within _ChRIS_ or the command-line.

[![Get it from chrisstore.co](https://raw.githubusercontent.com/FNNDSC/ChRIS_store_ui/963938c241636e4c3dc4753ee1327f56cb82d8b5/src/assets/public/badges/light.svg)](https://chrisstore.co/plugin/ep-asp-qc)

## Local Usage

To get started with local command-line usage, use [Apptainer](https://apptainer.org/)
(a.k.a. Singularity) to run `ep-asp-qc` as a container:

```shell
apptainer exec docker://fnndsc/ep-asp-qc verify_fit [--args values...] input/ output/
```

To print its available options, run:

```shell
apptainer exec docker://fnndsc/ep-asp-qc verify_fit --help
```

## Examples

`verify_fit` requires two positional arguments: a directory containing
input data, and a directory where to create output data.
First, create the input directory and move input data into it.

```shell
mkdir incoming/ outgoing/
mv some.dat other.dat incoming/
apptainer exec docker://fnndsc/ep-asp-qc:latest verify_fit [--args] incoming/ outgoing/
```

## Development

Instructions for developers.

### Building

Build a local container image:

```shell
docker build -t localhost/fnndsc/ep-asp-qc .
```

### Running

Mount the source code `verify_fit.py` into a container to try out changes without rebuild.

```shell
docker run --rm -it --userns=host -u $(id -u):$(id -g) \
    -v $PWD/verify_fit.py:/usr/local/lib/python3.10/site-packages/verify_fit.py:ro \
    -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw -w /outgoing \
    localhost/fnndsc/ep-asp-qc verify_fit /incoming /outgoing
```

### Testing

Run unit tests using `pytest`.
It's recommended to rebuild the image to ensure that sources are up-to-date.
Use the option `--build-arg extras_require=dev` to install extra dependencies for testing.

```shell
docker build -t localhost/fnndsc/ep-asp-qc:dev --build-arg extras_require=dev .
docker run --rm -it localhost/fnndsc/ep-asp-qc:dev pytest
```

## Release

Steps for release can be automated by [Github Actions](.github/workflows/ci.yml).
This section is about how to do those steps manually.

### Increase Version Number

Increase the version number in `setup.py` and commit this file.

### Push Container Image

Build and push an image tagged by the version. For example, for version `1.2.3`:

```
docker build -t docker.io/fnndsc/ep-asp-qc:1.2.3 .
docker push docker.io/fnndsc/ep-asp-qc:1.2.3
```

### Get JSON Representation

Run [`chris_plugin_info`](https://github.com/FNNDSC/chris_plugin#usage)
to produce a JSON description of this plugin, which can be uploaded to a _ChRIS Store_.

```shell
docker run --rm localhost/fnndsc/ep-asp-qc:dev chris_plugin_info > chris_plugin_info.json
```

