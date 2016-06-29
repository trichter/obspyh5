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
if 'dev' not in version:  # get image for correct version from travis-ci
    README = README.replace('branch=master', 'branch=v%s' % version)
DESCRIPTION = README.split('\n')[2]
LONG_DESCRIPTION = '\n'.join(README.split('\n')[5:])

ENTRY_POINTS = {
    'obspy.plugin.waveform': ['H5 = obspyh5'],
    'obspy.plugin.waveform.H5': [
        'isFormat = obspyh5:is_obspyh5',
        'readFormat = obspyh5:readh5',
        'writeFormat = obspyh5:writeh5']}

setup(name='obspyh5',
      version=version,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      url='https://github.com/trichter/obspyh5',
      author='Tom Eulenfeld',
      author_email='tom.eulenfeld@gmail.com',
      license='MIT',
      py_modules=['obspyh5'],
      install_requires=['future', 'obspy', 'h5py', 'numpy'],
      entry_points=ENTRY_POINTS,
      zip_safe=False,
      include_package_data=True
      )
