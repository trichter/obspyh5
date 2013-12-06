obspyh5
=======
hdf5 write/read support for obspy
---------------------------------

Welcome!

Saves and writes ObsPy streams to hdf5 files.
Stats attributes are preserved if they are numbers, strings,
UTCDateTime objects or numpy arrays.
You can use it as a plugin to obspy or you can use the internal api
e.g. to iterate over traces in a huge hdf5 file.

Installation
^^^^^^^^^^^^
Requires obspy and h5py. Install by::

    pip install https://github.com/trichter/obspyh5/archive/master.zip

or download and run::

    python setup.py install

Usage
^^^^^
Obspy plugin example: ::

    >>> from obspy import read
    >>> stream = read()  # load example stream
    >>> print stream
    ..3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    >>> stream.write('test.h5', 'H5')
    >>> print read('test.h5')  # Order is not preserved!
    3 Trace(s) in Stream:
    BW.RJOB..EHZ | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHE | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples
    BW.RJOB..EHN | 2009-08-24T00:20:03.000000Z - 2009-08-24T00:20:32.990000Z | 100.0 Hz, 3000 samples

Example using internal api: ::

    import hpy5
    from obspyh5 import hdf2stream, stream2hdf
    fin = hpy5.File('huge.h5') # file with a lot of groups, each containing some datasets with saved traces
    fout = hpy5.File('results.h5')
    for group in fin:
        stream = hfd2stream(group)  # reads stream from group from file
        stream.do_something()
        stream2hdf(stream, fout.requires_group(group.name))  # saves stream into group to file
    fin.close()
    fout.close()

Note
^^^^

Development stays on a low level in favour of sdf_.

.. _sdf: https://github.com/krischer/SDF/wiki