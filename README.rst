obspyh5
=======
hdf5 write/read support for obspy
---------------------------------

Welcome!

Requirements
^^^^^^^^^^^^

obspy and h5py

Installation
^^^^^^^^^^^^
Requires obspy and h5py. Install by::

    pip install https://github.com/trichter/obspyh5/archive/master.zip

or download and run::

    python setup.py install

Usage
^^^^^
::

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


Note
^^^^

Development stays on a low level in favour of sdf_.

.. _sdf: https://github.com/krischer/SDF/wiki