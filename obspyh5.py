from warnings import warn
from numpy import string_
from obspy.core import Trace, Stream, UTCDateTime as UTC
try:
    from h5py import is_hdf5, File
except ImportError:
    is_hdf5 = lambda x: False
    File = object
    
_IGNORE_HEADERS = ('endtime', 'delta')    
    
def _is_utc(utc):
    utc = str(utc)
    return len(utc) == 27 and utc.endswith('Z')

def read(fname, headonly=False):
    with StreamFile(fname, 'r') as f:
        return f.read(headonly=headonly)

def write(fname, stream, mode='w', ignore_headers=()):
    if not fname.endswith('.hdf5'):
        fname = fname + '.hdf5' 
    with StreamFile(fname, mode) as f:
        f.extend(stream, ignore_headers=ignore_headers)

class StreamFile(File):
    """
    Supports partial reading, appending and deleting of Streams in hdf5 files.
    """ 
    def read(self, **kwargs):
        return self.__getitem__(slice(None), **kwargs)
    
    def settrace(self, trace, key=None, ignore_headers=(), warn_override=True, **kwargs):
        ignore_headers = tuple(ignore_headers) + _IGNORE_HEADERS
        if key is None:
            key = tr.id
        if key in self:
            if warn_override:
                warn('Key %s already existing. Will override trace.' % key)
            del self[key]
        dat = self.create_dataset(key, trace.data.shape, trace.data.dtype, **kwargs)
        dat[:] = trace.data
        for key, val in trace.stats.items():
            if key not in ignore_headers:
                if isinstance(val, basestring) or _is_utc(val):
                    dat.attrs[key] = string_(val)
                else:
                    try:
                        dat.attrs[key] = val
                    except TypeError:
                        warn(("Writing header '%s' is not supported with h5py. " 
                              "Only h5py types and UTCDateTime are supported.") % key)
                              
    def gettrace(self, key, headonly=False):
        dat = self[key]
        stats = dict(dat.attrs)
        for key2, val in stats.items():
            if _is_utc(val):
                stats[key2] = UTC(val)
        if headonly:
            tr = Trace(header=stats)
        else:
            tr = Trace(data=dat[...], header=stats)
        return tr

    def append(self, trace, **kwargs):
        try:
            N = max(int(key) for key in self)+1
        except:                
            N = len(self)
        self.settrace(trace, key=str(N), **kwargs)            
            
    def extend(self, stream, **kwargs):
        try:
            N = max(int(key) for key in self)+1
        except:                
            N = len(self)
        for i, tr in enumerate(stream):
            self.settrace(tr, key=str(i+N), **kwargs)
        
    def __getitem__(self, index, **kwargs):
        if isinstance(index, int):
            return self.gettrace(self.keys()[index], **kwargs)
        elif isinstance(index, slice):
            traces = [self.gettrace(key, **kwargs) for key in self.keys()[index]]
            return Stream(traces=traces)
        else:
            return super(self.__class__, self).__getitem__(index, **kwargs)

    def __setitem__(self, index, val, **kwargs):
        if isinstance(index, int):
            self.settrace(val, key=self.keys()[index], warn_override=False, **kwargs)
        elif isinstance(index, slice):
            for key, v in zip(self.keys()[index], val):
                self.settrace(v, key=key, warn_override=False, **kwargs)
        else:
            super(self.__class__, self).__setitem__(index, val, **kwargs)
        
    def __delitem__(self, index):
        if isinstance(index, int):
            del self[keys()[index]]
        elif isinstance(index, slice):
            for key in self.keys()[index]:
                del self[key]
        else:
            return super(self.__class__, self).__delitem__(index)        
  
__all__ = [read, write, is_hdf5, StreamFile]         
