import unittest
import os
from tempfile import gettempdir

from obspy import read
from obspy.core import UTCDateTime as UTC
import obspyh5

class ObsPyH5TestCase(unittest.TestCase):
    
    def test_is_utc(self):
        self.assertTrue(obspyh5._is_utc(UTC()))
        self.assertFalse(obspyh5._is_utc(110))
        
    def test_obspyh5(self):
        fname = os.path.join(gettempdir(), 'test.hdf5')
        stream=read()
        stream[0].stats.onset = UTC()
        stream[0].stats.crazyheader = 11.5
        stream[0].stats.crazyheader2 = 'HEY'
        
        # write stream and read again, append data
        obspyh5.write(fname, stream)
        self.assertTrue(obspyh5.is_hdf5(fname))
        stream2 = obspyh5.read(fname)
        obspyh5.write(fname, stream, mode='a')
        stream3 = obspyh5.read(fname)
        self.assertEqual(stream, stream2)
        self.assertEqual(stream+stream, stream3)
        
        # read only header
        stream3 = obspyh5.read(fname, headonly=True)
        self.assertEqual(stream2[0].stats, stream3[0].stats)
        self.assertEqual(len(stream3[0].data), 0)
       
        os.remove(fname)
        
        # create hdf5 file object, extend f twice with stream
        # read stream with slices, delete and overwrite some traces
        # and see that all makes sense
        with obspyh5.StreamFile(fname) as f:
            f.extend(stream)
            f.extend(stream)
            
            self.assertEqual(f[1], stream[1])
            self.assertEqual(f[-3], stream[0])
            self.assertEqual(f[:4]+f[4:], stream+stream)
            self.assertEqual(len(f[:4]), 4)
            self.assertEqual(len(f[6:10]), 0)
            self.assertEqual(len(f[:-1]), 5)
            
            del f['2']
            del f[0:2]
            self.assertEqual(f[:], stream)
            f[:2] = stream[:2]
            f[-1] = stream[0]
        with obspyh5.StreamFile(fname) as f:
            self.assertEqual(f[:2], stream[:2])
            self.assertEqual(f[-1], stream[0])
            
          
            #stream[0].stats.stillok = [[3, 5, 6], [3, 2, 1]]
            #stream[0].stats.convtostr = {'hey':3, 'ho':1}.items()
            #stream[0].stats.toomuch={5:4}
            #f.append(stream[1])
            #f.append(stream[0])
            #print f[-1].stats
            #f.extend(stream, use_id=True)
            #def func(name, obj):
               #print name, type(obj)
            #f.visititems(func)
               
        
    
def suite():
    return unittest.makeSuite(ObsPyH5TestCase, 'test')

def main():
    unittest.main(defaultTest='suite')
    
if __name__ == '__main__':
    main()
    