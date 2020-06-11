[![Build Status](https://travis-ci.org/ladybug-tools/ladybug-rhino.svg?branch=master)](https://travis-ci.org/ladybug-tools/ladybug-rhino)

[![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

# ladybug-rhino

A library for communicating between Ladybug Tools core libraries and Rhinoceros CAD.

This library is used by both the Grasshopper and Rhino plugins to communicate with
the ladybug core Python library. Note that this library has dependencies
on Rhino SDK and Grasshopper SDK. It is NOT intended to be run with cPython with
the exception of running the CLI.

## Installation

`pip install -U ladybug-rhino`

If you want to also include the command line interface try:

`pip install -U ladybug-rhino[cli]`

To check if Ladybug Rhino command line is installed correctly try `ladybug-rhino viz`
and you should get a `viiiiiiiiiiiiizzzzzzzzz!` back in response!

## [API Documentation](http://ladybug-tools.github.io/ladybug-rhino/docs/)

## Local Development

1. Clone this repo locally

```python
git clone git@github.com:ladybug-tools/ladybug-rhino

# or

git clone https://github.com/ladybug-tools/ladybug-rhino
```

2. Install dependencies

```console
cd ladybug-rhino
pip install -r dev-requirements.txt
pip install -r requirements.txt
pip install pythonnet
pip install rhinoinside
```

3. Generate Documentation

```console
sphinx-apidoc -f -e -d 4 -o ./docs ./ladybug_rhino
sphinx-build -b html ./docs ./docs/_build/docs
```
