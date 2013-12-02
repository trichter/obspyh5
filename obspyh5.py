from numpy import string_
from warnings import warn
from obspy.core import Trace, Stream, UTCDateTime as UTC

try:
    import h5py
except ImportError:
    pass

_IGNORE = ('endtime', 'delta')


def _is_utc(utc):
    utc = str(utc)
    return len(utc) == 27 and utc.endswith('Z')


def is_hdf5(fname):
    try:
        return h5py.is_hdf5(fname)
    except:
        return False


def read_hdf5(fname, group='/', **kwargs):
    with h5py.File(fname, 'r') as f:
        group = f.require_group(group)
        return hdf2stream(group, **kwargs)


def write_hdf5(fname, stream, mode='w', group='/', **kwargs):
    if not fname.endswith('.hdf5'):
        fname = fname + '.hdf5'
    with h5py.File(fname, mode, libver='latest') as f:
        group = f.require_group(group)
        stream2hdf(group, stream, **kwargs)


def trace2dataset(dataset, trace, ignore=()):
    """Write trace.data and trace.stats into dataset"""
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


def trace2hdf(group, trace, key=None, override='warn', ignore=(), **kwargs):
    """Write trace into group"""
    if override not in ('warn', 'raise', 'ignore', 'dont'):
        msg = "Override has to be one of ('warn', 'raise', 'ignore', 'dont')."
        raise ValueError(msg)
    key = key or trace.id
    if key in group:
        msg = "Key '%s' already exists." % key
        if override == 'warn':
            warn(msg + ' Will override trace.')
        elif override == 'raise':
            raise KeyError(msg)
        elif override == 'dont':
            return
        del group[key]
    dataset = group.create_dataset(key, trace.data.shape, trace.data.dtype,
                                   **kwargs)
    trace2dataset(dataset, trace, ignore=ignore)


def stream2hdf(group, stream, indexing='num', **kwargs):
    """Write stream into group"""
    if indexing == 'num':
        Ns = [0]
        for k in group:
            try:
                Ns.append(int(k) + 1)
            except ValueError:
                pass
        N = max(Ns)
    elif indexing != 'id':
        raise ValueError("Indexing has to be one of ('num', 'id').")
    for i, tr in enumerate(stream):
        key = str(N + i) if indexing == 'num' else None
        trace2hdf(group, tr, key=key, **kwargs)


def dataset2trace(dataset, headonly=False):
    """Load trace from dataset"""
    stats = dict(dataset.attrs)
    for key, val in stats.items():
        if _is_utc(val):
            stats[key] = UTC(val)
    if headonly:
        tr = Trace(header=stats)
    else:
        tr = Trace(data=dataset[...], header=stats)
    return tr


def hdf2stream(group, recursive=False, headonly=False):
    """Load stream from group"""
    def _helper(g):
        for key, val in g.items():
            if isinstance(val, h5py.Dataset):
                tr = dataset2trace(val, headonly=headonly)
                traces.append(tr)
            elif recursive:
                _helper(val)
    traces = []
    _helper(group)
    return Stream(traces=traces)
