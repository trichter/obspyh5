import unittest
import warnings

import numpy as np
from obspy.core.util import NamedTemporaryFile, skipIf
from obspy import read
from obspy.core import UTCDateTime as UTC
from obspyh5 import (read_hdf5, write_hdf5, stream2hdf, hdf2stream, trace2hdf,
                     dataset2trace)
import obspyh5

try:
    import h5py
except ImportError:
    h5py = None


class HDF5TestCase(unittest.TestCase):

    def setUp(self):
        self.stream = read()
        self.stream[0].stats.onset = UTC()
        self.stream[0].stats.header = 42
        self.stream[0].stats.header2 = 'Test entry'
        
    def test_is_utc(self):
        self.assertTrue(obspyh5._is_utc(UTC()))
        self.assertFalse(obspyh5._is_utc(110))

    @skipIf(h5py is None, 'h5py missing')
    def test_hdf5_basic(self):
        stream = self.stream
        group = '/traces/test'
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            # write stream and read again, append data
            write_hdf5(fname, stream, group=group)
            self.assertTrue(obspyh5.is_hdf5(fname))
            stream2 = read_hdf5(fname, group=group)
            write_hdf5(fname, stream, mode='a', group=group)
            stream3 = read_hdf5(fname, group=group)
            self.assertEqual(stream[1:], stream2[1:])
            self.assertEqual(stream + stream, stream3)
            # read only header
            stream3 = read_hdf5(fname, group=group, headonly=True)
            self.assertEqual(stream2[0].stats, stream3[0].stats)
            self.assertEqual(len(stream3[0].data), 0)
            # test if group was really created
            with h5py.File(fname) as f:
                self.assertTrue(group in f)
                self.assertTrue(len(f[group]) == 6)
            # write with id indexing, order is not preserved
            write_hdf5(fname, stream, indexing='id')
            stream2 = read_hdf5(fname)
            self.assertEqual(stream, stream2[::-1])
            # test numpy headers, check for warning
            stream[0].stats.num = np.array([[5, 4, 3], [1, 2, 3.]])
            stream[0].stats.toomuch = {1: 3}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                write_hdf5(fname, stream)
                self.assertEqual(len(w), 1)
            stream2 = read_hdf5(fname)
            # stream/stats comparison not working for arrays
            # therefore checking directly
            np.testing.assert_array_equal(stream[0].stats.num,
                                          stream2[0].stats.num)
            del stream[0].stats.num
            del stream[0].stats.toomuch

    @skipIf(h5py is None, 'h5py missing')
    def test_hdf5_interface(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            with h5py.File(ft.name) as f:
                stream2hdf(f, stream)
                trace2hdf(f, stream[0], key=None)  # key = trace.id
                self.assertEqual(dataset2trace(f[stream[0].id]), stream[0])
                # test override
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    trace2hdf(f, stream[0], key=None)
                    self.assertEqual(len(w), 1)
                with self.assertRaises(KeyError):
                    trace2hdf(f, stream[0], key=None, override='raise')
                # is_hdf5 is only working with file names
                self.assertFalse(obspyh5.is_hdf5(f))
                # test that subgroup does not interfere
                stream2hdf(f.create_group('test'), stream[-1:])
                N = len(hdf2stream(f))
                self.assertEqual(N, 4)
                # test recursive option
                self.assertEqual(len(hdf2stream(f, recursive=True)), N + 1)
                # test num indexing if not all entries are nums
                stream2hdf(f, stream[-1:])

def suite():
    return unittest.makeSuite(HDF5TestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
