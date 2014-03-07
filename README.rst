obspyh5
=======
hdf5 write/read support for obspy
---------------------------------

Welcome!

Saves and writes ObsPy streams to hdf5 files.
Stats attributes are preserved if they are numbers, strings,
UTCDateTime objects or numpy arrays.
Its best used as a plugin to obspy.

Installation
^^^^^^^^^^^^
Requires obspy and h5py. Install by::

    pip install https://github.com/trichter/obspyh5/archive/master.zip

or download and run::

    python setup.py install

Usage
^^^^^
Basic example::

    >>> from obspy import read
    >>> stream = read()  # load example stream
    >>> print stream
    ..3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    >>> stream.write('test.h5', 'H5')  # declare 'H5' as format
    >>> print read('test.h5')  # Order is not preserved!
    3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples

Example to iterate over traces in hdf5 file::

    >>> from obspyh5 import iter_hdf5
    >>> for trace in iter_hdf5('huge_in.h5')
            trace.do_something()
            trace.write('huge_out.h5', 'H5', mode='a')  # append mode to write into file


Example using apply2trace keyword to process traces "on the fly".: ::

    >>> from obspy import read
    >>> def apply(trace):
            trace.do_something()
            trace.write('huge_out.h5', 'H5', mode='a')  # append mode to write into file

We tell obspy the format, so that it does not have to read the huge file several times to check the format itself.
Traces ar now passed to apply and removed from memory afterwards. Read returns a dummy stream in this case. ::

    >>> dummy = read('huge_in.h5', 'H5', apply2trace=apply)
    >>> print dummy
    1 Trace(s) in Stream:
    ... | 1970-01-01T00:00:00.000000Z - 1970-01-01T00:00:00.000000Z | 1.0 Hz, 0 samples

Both interfaces (iterate_hdf5 and apply2trace kwarg) allow iterating over traces in a huge file.

Alternative indexing
^^^^^^^^^^^^^^^^^^^^
obspyh5 supports alternative indexing. ::

    >>> from obspy import read
    >>> import obspyh5
    >>> print obspyh5._INDEX  # default index
    {network}.{station}/{location}.{channel}/{starttime.datetime:%Y-%m-%dT%H:%M:%S}_{endtime.datetime:%Y-%m-%dT%H:%M:%S}

The index gets populated by the stats object when writing a trace, e.g. ::

    >>> stats = read()[0].stats
    >>> print obspyh5._INDEX.format(**stats)
    'BW.RJOB/.EHZ/2009-08-24T00:20:03_2009-08-24T00:20:32'

To change the index use set_index. ::

    >>> obspyh5.set_index('xcorr')  # xcorr indexing
    >>> obspyh5.set_index('{newtork}.{station}/{distance}')  # custom indexing

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
    >>> print stream
    ST1.HHZ.ST0.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST1.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST2.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    >>> stream.write('test_xcorr.h5', 'H5')
    >>> print read('test_xcorr.h5')
    ST1.HHZ.ST0.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST1.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    ST1.HHZ.ST2.HHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples

Note
^^^^
This module is experimental and the interface possibly changes with time.
Development stays on a low level in favour of sdf_.

.. _sdf: https://github.com/krischer/SDF/wiki