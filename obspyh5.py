from numpy import string_
from os.path import splitext
from warnings import warn
from obspy.core import Trace, Stream, UTCDateTime as UTC

try:
    import h5py
except ImportError:
    pass

_IGNORE = ('endtime', 'sampling_rate', 'npts', '_format')
_INDEX = ('{station}.{network}.{location}.{channel}_'
          '{starttime.datetime:%Y-%m-%dT%H:%M:%S}_'
          '{endtime.datetime:%Y-%m-%dT%H:%M:%S}')


def _is_utc(utc):
    utc = str(utc)
    return len(utc) == 27 and utc.endswith('Z')


def is_hdf5(fname):
    try:
        return h5py.is_hdf5(fname)
    except:
        return False


def read_hdf5(fname, group='/waveforms', **kwargs):
    # These keywords get handled inside obspy
    for key in ('nearest_sample', 'starttime', 'endtime'):
        try:
            del kwargs[key]
        except KeyError:
            pass
    with h5py.File(fname, 'r') as f:
        return hdf2stream(f[group], **kwargs)


def write_hdf5(stream, fname, mode='w', group='/waveforms', **kwargs):
    if isinstance(fname, file):
        f = fname
        fname = f.name
        f.close()
    if not splitext(fname)[1]:
        fname = fname + '.h5'
    with h5py.File(fname, mode, libver='latest') as f:
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


def hdf2stream(group, headonly=False):
    """Load stream from group"""
    def _collect_traces(index, dataset):
        if isinstance(dataset, h5py.Dataset):
            tr = dataset2trace(dataset, headonly=headonly)
            traces.append(tr)
    traces = []
    group.visititems(_collect_traces)
    return Stream(traces=traces)
