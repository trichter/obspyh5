from setuptools import setup

VERSION = '0.2.3-dev'

with open('README.rst') as f:
    README = f.read()
if not 'dev' in VERSION:  # get image for correct version from travis-ci
    README = README.replace('branch=master', 'branch=v%s' % VERSION)
DESCRIPTION = README.split('\n')[2]
LONG_DESCRIPTION = '\n'.join(README.split('\n')[5:])

ENTRY_POINTS = {
    'obspy.plugin.waveform': ['H5 = obspyh5'],
    'obspy.plugin.waveform.H5': [
        'isFormat = obspyh5:is_obspyh5',
        'readFormat = obspyh5:readh5',
        'writeFormat = obspyh5:writeh5']}

setup(name='obspyh5',
      version=VERSION,
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
