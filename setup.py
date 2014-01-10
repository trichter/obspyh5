from setuptools import setup

ENTRY_POINTS = {
    'obspy.plugin.waveform': ['H5 = obspyh5'],
    'obspy.plugin.waveform.H5': [
        'isFormat = obspyh5:is_obspyh5',
        'readFormat = obspyh5:read_hdf5',
        'writeFormat = obspyh5:write_hdf5']}

setup(name='obspyh5',
      version='0.0.1.dev',
      description='hdf5 write/read support for obspy',
      url='https://github.com/trichter/obspyh5',
      author='Tom Richter',
      author_email='richter@gfz-potsdam.de',
      license='MIT',
      py_modules=['obspyh5'],
      install_requires=['obspy', 'h5py', 'numpy'],
      entry_points=ENTRY_POINTS,
      zip_safe=False)
