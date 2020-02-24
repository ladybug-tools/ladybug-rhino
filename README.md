[![Build Status](https://travis-ci.org/ladybug-tools/ladybug-rhino.svg?branch=master)](https://travis-ci.org/ladybug-tools/ladybug-rhino)

[![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)


# ladybug-rhino
A library for communicating between Ladybug Tools core libraries and Rhinoceros CAD.

This library is used by both the Grasshopper and Rhino plugins to communicate with the
ladybug and honeybee cores.

## Installation
```
pip install ladybug-rhino
```

## QuickStart
```python
import ladybug_rhino

```

## [API Documentation](http://ladybug-tools.github.io/ladybug-rhino/docs/)

## Local Development
1. Clone this repo locally
```
git clone git@github.com:ladybug-tools/ladybug-rhino

# or

git clone https://github.com/ladybug-tools/ladybug-rhino
```
2. Install dependencies:
```
cd ladybug-rhino
pip install -r dev-requirements.txt
pip install -r requirements.txt
pip install pythonnet
pip install rhinoinside
```

3. Generate Documentation:
```console
sphinx-apidoc -f -e -d 4 -o ./docs ./ladybug_rhino
sphinx-build -b html ./docs ./docs/_build/docs
```
