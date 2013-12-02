import unittest
import os
from tempfile import gettempdir
import warnings

from obspy import read as read_example
from obspy.core import UTCDateTime as UTC
from obspyh5 import (read_hdf5, write_hdf5, stream2hdf, hdf2stream, trace2hdf,
                     dataset2trace)
import obspyh5
import h5py
import numpy as np


class HDF5TestCase(unittest.TestCase):

    def test_is_utc(self):
        self.assertTrue(obspyh5._is_utc(UTC()))
        self.assertFalse(obspyh5._is_utc(110))

    def test_obspyh5(self):
        def subtest(fname, group='/'):
            # write_hdf5 stream and read_hdf5 again, append data
            write_hdf5(fname, stream, group=group)
            self.assertTrue(obspyh5.is_hdf5(fname))
            stream2 = read_hdf5(fname, group=group)
            write_hdf5(fname, stream, mode='a', group=group)
            stream3 = read_hdf5(fname, group=group)
            self.assertEqual(stream[1:], stream2[1:])
            self.assertEqual(stream + stream, stream3)
            # read_hdf5 only header
            stream3 = read_hdf5(fname, group=group, headonly=True)
            self.assertEqual(stream2[0].stats, stream3[0].stats)
            self.assertEqual(len(stream3[0].data), 0)
            # test if group was really created
            with h5py.File(fname) as f:
                self.assertTrue(group in f)
                self.assertTrue(len(f[group]) == 6)
            # test numpy headers, check for warning
            stream[0].stats.num = np.array([[5, 4, 3], [1, 2, 3.]])
            stream[0].stats.toomuch = {1: 3}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                write_hdf5(fname, stream, group=group)
                self.assertEqual(len(w), 1)
            stream2 = read_hdf5(fname, group=group)
            np.testing.assert_array_equal(stream[0].stats.num,
                                          stream2[0].stats.num)
            del stream[0].stats.num
            del stream[0].stats.toomuch
            os.remove(fname)
        stream = read_example()
        stream[0].stats.onset = UTC()
        stream[0].stats.header = 11.5
        stream[0].stats.header2 = 'HEY'
        fname1 = os.path.join(gettempdir(), 'test.hdf5')
        # write into file
        subtest(fname1)
        # write into specific group
        subtest(fname1, group='/traces/test')
        # write with id indexing, order is not preserved
        write_hdf5(fname1, stream, indexing='id')
        stream2 = read_hdf5(fname1)
        self.assertEqual(stream, stream2[::-1])
        os.remove(fname1)

        # use direct interface
        with h5py.File(fname1) as f:
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
            self.assertFalse(obspyh5.is_hdf5(f))  # only fnames can be checked
            stream2hdf(f.create_group('test'), stream[-1:])
            # test that subgroup does not interfere
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
