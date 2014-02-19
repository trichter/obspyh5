"""
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
"""

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
    Set index

    Possible values: 'standard', 'xcorr' or index itself.
    """
    global _INDEX
    if index in _INDEXES.keys():
        _INDEX = _INDEXES[index]
    else:
        _INDEX = index


def is_obspyh5(fname):
    """
    Check if file is hdf5 file and if it was written by obspyh5
    """
    try:
        if not h5py.is_hdf5(fname):
            return False
        with h5py.File(fname, 'r') as f:
            return f.attrs['file_format'].lower() == 'obspyh5'
    except:
        return False

_return_value_apply2trace = [None]
def read_hdf5(fname, mode='r', group='/waveforms', headonly=False,
              apply2trace=None, **kwargs):
    # These keywords get handled inside obspy
    if apply2trace is None:
        for key in ('nearest_sample', 'starttime', 'endtime'):
            try:
                del kwargs[key]
            except KeyError:
                pass
    with h5py.File(fname, mode) as f:
        def _apply2item(index, dataset):
            if isinstance(dataset, h5py.Dataset):
                tr = dataset2trace(dataset, headonly=headonly)
                return apply2trace(tr)
        group = f[group]
        if apply2trace is None:
            traces = []
            apply2trace = traces.append
        else:
            traces = [Trace()]
        if isinstance(group, h5py.Dataset):
            _apply2item(None, group)
        else:
            group.visititems(_apply2item)
    return Stream(traces=traces)


def write_hdf5(stream, fname, mode='w', group='/waveforms', **kwargs):
    if not splitext(fname)[1]:
        fname = fname + '.h5'
    with h5py.File(fname, mode, libver='latest') as f:
        f.attrs['file_format'] = 'obspyh5'
        stream2hdf(stream, f.require_group(group), **kwargs)


def trace2hdf(trace, group, override='warn', ignore=(), **kwargs):
    """Write trace into group"""
    if override not in ('warn', 'raise', 'ignore', 'dont'):
        msg = "Override has to be one of ('warn', 'raise', 'ignore', 'dont')."
        raise ValueError(msg)
    index = _INDEX.format(**trace.stats)
    if index in group:
        msg = "Index '%s' already exists." % index
        if override == 'warn':
            warn(msg + ' Will override trace.')
        elif override == 'raise':
            raise KeyError(msg)
        elif override == 'dont':
            return
        del group[index]
    dataset = group.create_dataset(index, trace.data.shape, trace.data.dtype,
                                   **kwargs)
    ignore = tuple(ignore) + _IGNORE
    dataset[:] = trace.data
    for key, val in trace.stats.items():
        if key not in ignore:
            if isinstance(val, basestring) or _is_utc(val):
                dataset.attrs[key] = string_(val)
            else:
                try:
                    dataset.attrs[key] = val
                except TypeError:
                    warn(("Writing header '%s' is not supported. Only h5py "
                          "types and UTCDateTime are supported.") % key)


def stream2hdf(stream, group, **kwargs):
    """Write stream into group"""
    for tr in stream:
        trace2hdf(tr, group, **kwargs)


def dataset2trace(dataset, headonly=False):
    """Load trace from dataset"""
    stats = dict(dataset.attrs)
    for key, val in stats.items():
        if _is_utc(val):
            stats[key] = UTC(val)
    if headonly:
        stats['npts'] = len(dataset)
        tr = Trace(header=stats)
    else:
        tr = Trace(data=dataset[...], header=stats)
    return tr
