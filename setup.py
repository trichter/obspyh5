# Copyright 2013-2017 Tom Eulenfeld, MIT license
import os.path
import re

from setuptools import setup


def find_version(*paths):
    fname = os.path.join(os.path.dirname(__file__), *paths)
    with open(fname) as fp:
        code = fp.read()
    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", code, re.M)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")

version = find_version('obspyh5.py')

with open('README.rst') as f:
    README = f.read()
DESCRIPTION = README.split('\n')[2]
LONG_DESCRIPTION = '\n'.join(README.split('\n')[20:])

ENTRY_POINTS = {
    'obspy.plugin.waveform': ['H5 = obspyh5'],
    'obspy.plugin.waveform.H5': [
        'isFormat = obspyh5:is_obspyh5',
        'readFormat = obspyh5:readh5',
        'writeFormat = obspyh5:writeh5']}

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Scientific/Engineering :: Physics'
    ]

setup(name='obspyh5',
      version=version,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      url='https://github.com/trichter/obspyh5',
      author='Tom Eulenfeld',
      author_email='tom.eulenfeld@gmail.com',
      license='MIT',
      py_modules=['obspyh5'],
      install_requires=['h5py', 'numpy', 'obspy', 'setuptools'],
      entry_points=ENTRY_POINTS,
      zip_safe=False,
      include_package_data=True,
      classifiers=CLASSIFIERS
      )
