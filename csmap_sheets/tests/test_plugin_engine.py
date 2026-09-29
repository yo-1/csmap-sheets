import unittest
import tempfile
from pathlib import Path
import numpy as np
from csmap_sheets.engine.filters import numpy_gaussian, numpy_valid_minimum
from csmap_sheets.engine import pipeline
from csmap_sheets.engine.progress import check_cancel, gdal_progress, CancelledError


class PluginEngineTests(unittest.TestCase):
    def test_numpy_gaussian_against_scipy(self):
        try:from scipy.ndimage import gaussian_filter
        except ImportError:self.skipTest('SciPy reference is unavailable')
        a=np.random.default_rng(42).normal(size=(39,45))
        for sigma in (.6,2.,3.):
            radius=int(np.ceil(4*sigma))
            np.testing.assert_allclose(numpy_gaussian(a,sigma,radius),
                gaussian_filter(a,sigma,radius=radius,mode='constant',cval=0),atol=1e-14)

    def test_numpy_mask_against_scipy(self):
        try:from scipy.ndimage import minimum_filter
        except ImportError:self.skipTest('SciPy reference is unavailable')
        a=np.ones((40,45),dtype=np.uint8)
        a[12,30]=0
        for size in (1,3,9,25,101):
            np.testing.assert_array_equal(numpy_valid_minimum(a,size),
                minimum_filter(a,size=size,mode='constant',cval=0))

    def test_entire_render_numpy_backend(self):
        y,x=np.mgrid[:91,:95]
        a=500+np.sin(x/8)*4+np.cos(y/11)*6
        valid=np.ones(a.shape,dtype=bool)
        valid[33,50]=False
        args=(a,valid,1,3,.05,60,[0,3000])
        reference=pipeline.relief(*args)
        gauss,minimum=pipeline.gaussian_filter,pipeline.minimum_filter
        try:
            pipeline.gaussian_filter=numpy_gaussian
            pipeline.minimum_filter=numpy_valid_minimum
            actual=pipeline.relief(*args)
        finally:
            pipeline.gaussian_filter, pipeline.minimum_filter=gauss,minimum
        np.testing.assert_array_equal(reference[0][:,:,3],actual[0][:,:,3])
        self.assertLessEqual(int(np.abs(reference[0].astype(int)-actual[0].astype(int)).max()),1)
        np.testing.assert_allclose(reference[1],actual[1],atol=1e-12)
        np.testing.assert_allclose(reference[2],actual[2],atol=1e-10)

    def test_brackets_in_local_filename(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            f=root/'DEM[1].tif'
            f.write_bytes(b'placeholder')
            c=pipeline.validate_config(dict(inputs=[str(f)],output_dir=str(root/'out'),
                target_crs='EPSG:6677',plane_zone=9,cell_size=1,confirm_elevation_metres=True),root)
            self.assertEqual(c['inputs'],[str(f)])

    def test_cancellation(self):
        class Feedback:
            def isCanceled(self):return True
        with self.assertRaises(CancelledError):check_cancel(Feedback())
        self.assertEqual(gdal_progress(Feedback())(.5,'',None),0)


if __name__=='__main__':unittest.main(verbosity=2)
