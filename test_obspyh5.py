import unittest
import warnings

import numpy as np
from obspy.core.util import NamedTemporaryFile
from obspy import read
from obspy.core import UTCDateTime as UTC
from obspyh5 import (read_hdf5, write_hdf5, trace2hdf)
import obspyh5
import h5py


class HDF5TestCase(unittest.TestCase):

    def setUp(self):
        self.stream = read().sort()
        self.stream[0].stats.onset = UTC()
        self.stream[0].stats.header = 42
        self.stream[0].stats.header2 = 'Test entry'

    def test_is_utc(self):
        self.assertTrue(obspyh5._is_utc(UTC()))
        self.assertFalse(obspyh5._is_utc(110))

    def test_hdf5_plugin(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            stream2 = read(fname).sort()
            for tr in stream2:
                del tr.stats._format
            self.assertEqual(stream, stream2)

    def test_hdf5_basic(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            # write stream and read again, append data
            write_hdf5(stream[:1], fname)
            self.assertTrue(obspyh5.is_obspyh5(fname))
            stream2 = read_hdf5(fname)
            write_hdf5(stream[1:], fname, mode='a')
            stream3 = read_hdf5(fname)
            self.assertEqual(stream[:1], stream2)
            self.assertEqual(stream, stream3)
            # read only header
            stream3 = read_hdf5(fname, headonly=True)
            self.assertEqual(stream2[0].stats, stream3[0].stats)
            self.assertEqual(len(stream3[0].data), 0)
            # test if group was really created
            with h5py.File(fname) as f:
                self.assertTrue('waveforms' in f)
            # test numpy headers, check for warning
            stream[0].stats.num = np.array([[5, 4, 3], [1, 2, 3.]])
            stream[0].stats.toomuch = {1: 3}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                write_hdf5(stream, fname)
                self.assertEqual(len(w), 1)
            stream2 = read_hdf5(fname)
            # stream/stats comparison not working for arrays
            # therefore checking directly
            np.testing.assert_array_equal(stream[0].stats.num,
                                          stream2[0].stats.num)
            del stream[0].stats.num
            del stream[0].stats.toomuch

    def test_hdf5_interface(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            with h5py.File(ft.name) as f:
                trace2hdf(stream[0], f)
                # test override
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    trace2hdf(stream[0], f)
                    self.assertEqual(len(w), 1)
                with self.assertRaises(KeyError):
                    trace2hdf(stream[0], f, key=None, override='raise')
                # is_obspyh5 is only working with file names
                self.assertFalse(obspyh5.is_obspyh5(f))

def suite():
    return unittest.makeSuite(HDF5TestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
