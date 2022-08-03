obspyh5
=======
HDF5 write/read support for obspy
---------------------------------

|buildstatus| |coverage| |version| |pyversions| |zenodo|

.. |buildstatus| image:: https://github.com/trichter/obspyh5/workflows/tests/badge.svg
   :target: https://github.com/trichter/obspyh5/actions

.. |coverage| image:: https://codecov.io/gh/trichter/obspyh5/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/trichter/obspyh5

.. |version| image:: https://img.shields.io/pypi/v/obspyh5.svg
   :target: https://pypi.python.org/pypi/obspyh5

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/obspyh5.svg
   :target: https://python.org

.. |zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3953668.svg
   :target: https://doi.org/10.5281/zenodo.3953668


Saves and writes ObsPy streams to hdf5 files.
Stats attributes are preserved if they are numbers, strings,
UTCDateTime objects or numpy arrays.
It can be used as a plugin to obspy's read function to read a whole hdf5 file.
Alternatively you can iterate over the traces in a hdf5 file with the iterh5
function.

Installation
^^^^^^^^^^^^
Install h5py and obspy. After that install obspyh5 using pip by::

    pip install obspyh5

With conda the package can be installed into a fresh environment with::

    conda config --add channels conda-forge
    conda create -n obsh5 numpy obspy h5py
    conda activate obsh5
    pip install obspyh5

Usage
^^^^^
Basic example using the obspy plugin::

    >>> from obspy import read
    >>> stream = read()  # load example stream
    >>> print(stream)
    ..3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    >>> stream.write('test.h5', 'H5')  # declare 'H5' as format
    >>> print(read('test.h5'))  # order is preserved only for default index
    3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples

Example iterating over traces in a huge hdf5 file. After each iteration the
trace is not kept in memory and therefore it is possible to process a huge hdf5
file on a PC without problems. ::

    >>> from obspyh5 import iterh5
    >>> for trace in iterh5('huge_in.h5')
            trace.do_something()
            trace.write('huge_out.h5', 'H5', mode='a')  # append mode to write into file

Alternative indexing
^^^^^^^^^^^^^^^^^^^^
obspyh5 supports alternative indexing. ::

    >>> from obspy import read
    >>> import obspyh5
    >>> print(obspyh5._INDEX)  # default index
    waveforms/{trc_num:03d}_{id}_{starttime.datetime:%Y-%m-%dT%H:%M:%S}_{duration:.1f}s

The index gets populated by the stats object and the trace number when writing a trace, e.g. ::

    'waveforms/000_BW.RJOB..EHZ/2009-08-24T00:20:03_30.0s'

To change the index use set_index. ::

    >>> obspyh5.set_index('flat')  # flat index wihtout trace number, writing a trace with the same metadata twice will overwrite
    >>> obspyh5.set_index('nested')  # nested index
    >>> obspyh5.set_index('xcorr')  # xcorr indexing
    >>> obspyh5.set_index('waveforms/{network}.{station}/{distance}')  # custom indexing
    >>> obspyh5.set_index('waveforms/{trc_num:03d}_{station}')  # use of the trace number
    >>> obspyh5.set_index()  # default index

When using the 'xcorr' indexing stats needs the entries 'network1', 'station1',
'location1', 'channel1', 'network2', 'station2', 'location2' and 'channel2'
of the first and second station. An example: ::

    >>> from obspy import read
    >>> import obspyh5
    >>> obspyh5.set_index('xcorr')  # activate xcorr indexing
    >>> stream = read()
    >>> for i, tr in enumerate(stream):  # manipulate stats object
            station1, station2 = 'ST1', 'ST%d' % i
            channel1, channel2 = 'HHZ', 'HHN'
            s = tr.stats
            # we manipulate seed id so that important information gets
            # printed by obspy
            s.network, s.station = s.station1, s.channel1 = station1, channel1
            s.location, s.channel = s.station2, s.channel2 = station2, channel2
            s.network1 = s.network2 = 'BW'
            s.location1 = s.location2 = ''
    >>> print(stream)
    ST1.HHZ.ST0.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST1.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST2.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    >>> stream.write('test_xcorr.h5', 'H5')
    >>> print(read('test_xcorr.h5'))
    ST1.HHZ.ST0.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST1.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST2.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples


Note
^^^^
See also ASDF_ for a more comprehensive approach.

Use case: Cross-correlation of late Okhotsk coda (notebook_).

.. _ASDF: https://seismic-data.org/

.. _notebook: http://nbviewer.jupyter.org/github/trichter/notebooks/blob/master/cross_correlation_okhotsk_coda.ipynb