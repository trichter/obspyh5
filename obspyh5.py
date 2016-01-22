"""
obspyh5
=======
hdf5 write/read support for obspy
---------------------------------

Welcome!

Saves and writes ObsPy streams to hdf5 files.
Stats attributes are preserved if they are numbers, strings,
UTCDateTime objects or numpy arrays.
Its best used as a plugin to obspy.

For some examples have a look at the README.rst_.

.. _README.rst: https://github.com/trichter/obspyh5

"""

# The following lines are for Py2/Py3 support with the future module.
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import (  # analysis:ignore
    bytes, dict, int, list, object, range, str,
    ascii, chr, hex, input, next, oct, open,
    pow, round, super, map, zip)
import sys
IS_PY3 = sys.version_info.major == 3

from numpy import string_
from os.path import splitext
from warnings import warn
from obspy.core import Trace, Stream, UTCDateTime as UTC


try:
    import h5py
except ImportError:
    pass

_IGNORE = ('endtime', 'sampling_rate', 'npts', '_format')

_INDEXES = {
    'standard': ('{network}.{station}/{location}.{channel}/'
                 '{starttime.datetime:%Y-%m-%dT%H:%M:%S}_'
                 '{endtime.datetime:%Y-%m-%dT%H:%M:%S}'),
    'xcorr': ('{network1}.{station1}-{network2}.{station2}/'
              '{location1}.{channel1}-{location2}.{channel2}/'
              '{starttime.datetime:%Y-%m-%dT%H:%M:%S}_'
              '{endtime.datetime:%Y-%m-%dT%H:%M:%S}')}

_INDEX = _INDEXES['standard']


def _is_utc(utc):
    utc = str(utc)
    return len(utc) == 27 and utc.endswith('Z')


def set_index(index='standard'):
    """
    Set index for newly created files.

    Some indexes are hold by the module variable _INDEXES ('standard' and
    'xcorr'). The index can also be set to a custom value, e.g.

    >>> set_index('{network}.{station}/{otherstrangeheader}')

    This string gets evaluated by a call to its format method,
    with the stats of each trace as kwargs, e.g.

    >>> '{network}.{station}/{otherstrangeheader}'.format(**stats)

    This means, that headers used in the index must exist for a trace to write.
    The index is stored inside the HDF5 file.

    :param index: 'standard' (default), 'xcorr' or other string.
    """
    global _INDEX
    if index in _INDEXES.keys():
        _INDEX = _INDEXES[index]
    else:
        _INDEX = index


def is_obspyh5(fname):
    """
    Check if file is a hdf5 file and if it was written by obspyh5.
    """
    try:
        if not h5py.is_hdf5(fname):
            return False
        with h5py.File(fname, 'r') as f:
            return f.attrs['file_format'].lower() == 'obspyh5'
    except:
        return False


def iterh5(fname, mode='r', group='/waveforms', headonly=False, readonly=None):
    """
    Iterate over traces in hdf5 file. See readh5 for doc of kwargs.
    """
    def visit(group):
        """Visit all items iteratively and yield datasets as traces."""
        if isinstance(group, h5py.Dataset):
            yield dataset2trace(group, headonly=headonly)
        else:
            for sub in group:
                for subgroup in visit(group[sub]):
                    yield subgroup
    with h5py.File(fname, mode) as f:
        if readonly is not None:
            try:
                index = f.attrs['index']
            except KeyError:
                index = _INDEX
            index1 = index.split('/')
            index2 = []
            for i in index1:
                try:
                    index2.append(i.format(**readonly))
                except KeyError:
                    break
            group = '/'.join([group] + index2)
        for v in visit(f[group]):
            yield v


def readh5(fname, mode='r', group='/waveforms', headonly=False, readonly=None,
           **kwargs):
    """
    Read hdf5 file and return Stream object.

    :param fname: name of file to read
    :param mode: 'r' (read-only, default), 'a' (append) or other.
        Argument is passed to h5py.File. Use 'a' if you want to write in the
        same file, while it is open for reading.
    :param group: group or subgroup to read, defaults to '/waveforms'
        This can alos point to a dataset. group can be used to read only a
        part of the hdf5 file.
    :param headonly: read only the headers of the traces
    :param readonly: read only traces determined by given dict.
        E.g. readonly={'network':'CX', 'station':'PB01'} will return traces
        from CX.PB01. This will only work if the index is the same as it was
        for wrting the stream. Additionally the index has to be
        filled from the beginning to represent a hdf5 group.
        E.g. with the standard index a dict with the following keys will work:
        ('network', 'station'),
        ('network', 'station', 'location', 'channel') or
        ('network', 'station', 'location', 'channel', 'starttime', 'endtime').
    :param **kwargs: other kwargs are ignored!
    """
    traces = []
    for tr in iterh5(fname, mode=mode, group=group, headonly=headonly,
                     readonly=readonly):
        traces.append(tr)
    return Stream(traces=traces)


def writeh5(stream, fname, mode='w', group='/waveforms', headonly=False,
            **kwargs):
    """
    Write stream to hdf5 file.

    :param stream: Stream to write.
    :param fname: hdf5 filename
    :param mode: 'w' (write, default), 'a' (append) or other.
        Argument is passed to h5py.File. Use 'a' to write into an existing
        file. 'w' will create a new empty file in any case.
    :param group: defaults to '/waveforms', not recommended to change.
    :param headonly: write only the header of the traces
    :param override: 'warn' (default, warn and override), 'raise' (raise
        Exception), 'ignore' (override, without warning), 'dont' (do not
        override, without warning).
        Behaviour if dataset with the same index already exists.
        For headonly=True this parameter is ignored.
    :param ignore: iterable
        Do not write headers listed inside ignore. Additionally the headers
        'endtime', 'sampling_rate', 'npts' and '_format' are ignored.
        'npts' is written for headonly=True.
    :param **kwargs: Additional kwargs are passed to create_dataset in h5py.
    """
    if headonly and format == 'w':
        raise ValueError("headonly=True is only supported for format='a'")
    if not splitext(fname)[1]:
        fname = fname + '.h5'
    with h5py.File(fname, mode, libver='latest') as f:
        f.attrs['file_format'] = 'obspyh5'
        if 'index' not in f.attrs:
            f.attrs['index'] = _INDEX
        group = f.require_group(group)
        for tr in stream:
            trace2group(tr, group, headonly=headonly, **kwargs)


def trace2group(trace, group, headonly=False, override='warn', ignore=(),
                **kwargs):
    """Write trace into group."""
    if override not in ('warn', 'raise', 'ignore', 'dont'):
        msg = "Override has to be one of ('warn', 'raise', 'ignore', 'dont')."
        raise ValueError(msg)
    try:
        index = group.file.attrs['index']
    except KeyError:
        index = group.file.attrs['index'] = _INDEX
    index = index.format(**trace.stats)
    if index in group and not headonly:
        msg = "Index '%s' already exists." % index
        if override == 'warn':
            warn(msg + ' Will override trace.')
        elif override == 'raise':
            raise KeyError(msg)
        elif override == 'dont':
            return
        del group[index]
    if headonly:
        try:
            dataset = group[index]
        except KeyError:
            msg = ("Index '%s' does not exist. headonly=True only supports "
                   "writing headers of existing data.")
            raise KeyError(msg % index)
    else:
        dataset = group.create_dataset(index, trace.data.shape,
                                       trace.data.dtype, **kwargs)
        dataset[:] = trace.data
    ignore = tuple(ignore) + _IGNORE
    for key, val in trace.stats.items():
        if key not in ignore:
            if isinstance(val, str) or _is_utc(val):
                dataset.attrs[key] = string_(val)
            else:
                try:
                    dataset.attrs[key] = val
                except (KeyError, TypeError):
                    warn(("Writing header '%s' is not supported. Only h5py "
                          "types and UTCDateTime are supported.") % key)


def dataset2trace(dataset, headonly=False):
    """Load trace from dataset."""
    stats = dict(dataset.attrs)
    for key, val in stats.items():
        # next two lines are a quick and dirty hack for Python3
        if IS_PY3 and isinstance(val, bytes):
            stats[key] = val = val.decode('utf-8')
        if _is_utc(val):
            stats[key] = UTC(val)
    if headonly:
        stats['npts'] = len(dataset)
        trace = Trace(header=stats)
    else:
        trace = Trace(data=dataset[...], header=stats)
    return trace
