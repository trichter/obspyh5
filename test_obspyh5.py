# Copyright 2013-2016 Tom Eulenfeld, MIT license
import unittest
import warnings

import h5py
import numpy as np
from obspy import read
from obspy.core import UTCDateTime as UTC
from obspy.core.util import NamedTemporaryFile
from obspyh5 import readh5, writeh5, trace2group, iterh5, set_index
import obspyh5


class HDF5TestCase(unittest.TestCase):

    def setUp(self):
        self.stream = read()
        # add processing info
        self.stream.decimate(2)
        self.stream.differentiate()
        self.stream[0].stats.onset = UTC()
        self.stream[0].stats.header = 42
        self.stream[0].stats.header2 = 'Test entry'
        self.stream[0].stats.header3 = u'Test entry unicode'
        stack = dict(group='all', count=5, type=['pw', 2])
        self.stream[0].stats.stack = stack
        for tr in self.stream:
            if 'response' in tr.stats:
                del tr.stats.response

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

    def test_hdf5_plugin_and_xcorr_index(self):
        try:
            set_index('xcorr')
            stream = self.stream.copy()
            for i, tr in enumerate(stream):  # manipulate stats object
                station1, station2 = 'ST1', 'ST%d' % i
                channel1, channel2 = 'HHZ', u'HHN'
                s = tr.stats
                # we manipulate seed id so that important information gets
                # printed by obspy
                s.network, s.station = s.station1, s.channel1 = station1, channel1
                s.location, s.channel = s.station2, s.channel2 = station2, channel2
                s.network1 = s.network2 = 'BW'
                s.location1 = s.location2 = ''
            stream.sort()
            with NamedTemporaryFile(suffix='.h5') as ft:
                fname = ft.name
                stream.write(fname, 'H5')
                stream2 = read(fname).sort()
            for tr in stream2:
                del tr.stats._format
            self.assertEqual(stream, stream2)
        finally:
            set_index()

    def test_flat_and_nested_index(self):
        for index in ('flat', 'nested'):
            set_index(index)
            stream = self.stream.copy()
            try:
                with NamedTemporaryFile(suffix='.h5') as ft:
                    fname = ft.name
                    stream.write(fname, 'H5')
                    stream2 = read(fname)
                    if index == 'nested':
                        stream3 = read(fname, grop='waveforms/BW.RJOB')
            finally:
                set_index()
            for tr in stream2:
                del tr.stats._format
            self.assertEqual(stream.sort(), stream2.sort())
        for tr in stream3:
            del tr.stats._format
        self.assertEqual(stream.sort(), stream3.sort())


    def test_hdf5_basic(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            # write stream and read again, append data
            writeh5(stream[:1], fname)
            self.assertTrue(obspyh5.is_obspyh5(fname))
            stream2 = readh5(fname)
            writeh5(stream[1:], fname, mode='a')
            stream3 = readh5(fname)
            self.assertEqual(stream[:1], stream2)
            self.assertEqual(stream, stream3)
            # read only header
            stream3 = readh5(fname, headonly=True)
            self.assertEqual(stream2[0].stats, stream3[0].stats)
            self.assertEqual(len(stream3[0].data), 0)
            # test if group was really created
            with h5py.File(fname, mode='r') as f:
                self.assertTrue('waveforms' in f)
#           # test numpy headers
            stream[0].stats.num = np.array([[5, 4, 3], [1, 2, 3.]])
            writeh5(stream, fname)
            stream2 = readh5(fname)
            # stream/stats comparison not working for arrays
            # therefore checking directly
            np.testing.assert_array_equal(stream[0].stats.num,
                                          stream2[0].stats.num)
            del stream[0].stats.num
            # check for warning for unsupported types
            stream[0].stats.toomuch = object()
            with warnings.catch_warnings(record=True) as w:
                writeh5(stream, fname)
                warnings.simplefilter("always")
                self.assertEqual(len(w), 1)
            del stream[0].stats.toomuch

    def test_hdf5_interface(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            with h5py.File(ft.name, mode='w') as f:
                trace2group(stream[0], f)
                # test override
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    trace2group(stream[0], f)
                    self.assertEqual(len(w), 1)
                with self.assertRaises(KeyError):
                    trace2group(stream[0], f, key=None, override='raise')
                # is_obspyh5 is only working with file names
                self.assertFalse(obspyh5.is_obspyh5(f))

    def test_hdf5_iter(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            traces = []
            for tr in iterh5(fname):
                traces.append(tr)
            self.assertEqual(stream.traces, traces)

    def test_hdf5_readonly(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            ro = {'network': 'BW', 'station': u'RJOB', 'location': '',
                  'channel': 'EHE'}
            stream2 = read(fname, 'H5', readonly=ro)
            self.assertEqual(stream[0].id, stream2[0].id)
            ro = {'network': 'BW', 'station': 'RJOB'}
            stream2 = read(fname, 'H5', readonly=ro)
            self.assertEqual(len(stream2), 3)

    def test_hdf5_headonly(self):
        stream = self.stream
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            stream2 = read(fname, 'H5', headonly=True)
            stream2[0].stats.header = -42
            self.assertEqual(len(stream2[0]), 0)

    def test_stored_index(self):
        stream = self.stream
        try:
            with NamedTemporaryFile(suffix='.h5') as ft:
                fname = ft.name
                stream.write(fname, 'H5')
                set_index('nonesens')
                stream.write(fname, 'H5', mode='a', override='ignore')
        finally:
            set_index()

    def test_read_files_saved_prior_version_0_3(self):
        stream = self.stream
        index_v_0_2 = ('{network}.{station}/{location}.{channel}/'
                       '{starttime.datetime:%Y-%m-%dT%H:%M:%S}_'
                       '{endtime.datetime:%Y-%m-%dT%H:%M:%S}')
        set_index(index_v_0_2)
        try:
            with NamedTemporaryFile(suffix='.h5') as ft:
                fname = ft.name
                stream.write(fname, 'H5', group='waveforms')
                stream2 = read(fname, 'H5', group='waveforms')
                stream3 = read(fname, 'H5')
        finally:
            set_index()
        for tr in stream2:
            del tr.stats._format
        for tr in stream3:
            del tr.stats._format
        self.assertEqual(stream, stream2)
        self.assertEqual(stream, stream3)

    def test_trc_num(self):
        stream = self.stream.copy()
        set_index('waveforms/{trc_num:03d}')
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            stream.write(fname, 'H5', mode='a')
            stream2 = read(fname, 'H5')
        for tr in stream2:
            del tr.stats._format
        set_index()
        self.assertEqual(len(stream2), 6)
        self.assertEqual(stream2[::2], stream)
        self.assertEqual(stream2[1::2], stream)

    def test_attrib_dict(self):
        stream = self.stream.copy()
        stream[0].stats.ad = {'bla': 0, 'bla2': 'test', 'bla3': [4, 5]}
        stream[0].stats.ad.nested = {'x': 'next', 'y': 'level'}
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            stream2 = read(fname, 'H5')
        for tr in stream2:
            del tr.stats._format
        self.assertEqual(stream2, stream)

    def test_without_json(self):
        stream = self.stream.copy()
        for tr in stream:
            del tr.stats.processing
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')
            stream2 = read(fname, 'H5')
        for tr in stream2:
            del tr.stats._format
        self.assertEqual(stream2, stream)

    def test_empty_seedid(self):
        stream = self.stream.copy()
        for tr in stream:
            del tr.stats.processing
            tr.id = '...'
        with NamedTemporaryFile(suffix='.h5') as ft:
            fname = ft.name
            stream.write(fname, 'H5')


def suite():
    return unittest.makeSuite(HDF5TestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
