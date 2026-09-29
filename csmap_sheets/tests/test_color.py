import unittest
import hashlib
import numpy as np
from csmap_sheets.engine.pipeline import relief, color_settings, rendering_settings
from csmap_sheets.engine.color_fme import (
    FME_COLORS, FME_WEIGHTS, apply_stretch, lut2, lut3, normalise_index,
    render_fme, rendering_record, validate_fme_settings,
)


class ColorTests(unittest.TestCase):
    def render(self, tone, a=None):
        if a is None:
            y,x=np.mgrid[:81,:81]
            a=500+5*np.sin(x/6)+3*np.cos(y/9)
        return relief(a,np.isfinite(a),1,2,.05,60,[0,3000],tone)

    def test_only_colours_change(self):
        base,slope,curvature=self.render({})
        edited,s2,c2=self.render(dict(saturation=.3,gamma=1.2,slope_darkness=.2))
        np.testing.assert_array_equal(slope,s2)
        np.testing.assert_array_equal(curvature,c2)
        np.testing.assert_array_equal(base[:,:,3],edited[:,:,3])
        self.assertFalse(np.array_equal(base[:,:,:3],edited[:,:,:3]))

    def test_grayscale_and_transparency(self):
        a=np.full((81,81),100.)
        a[40,40]=np.nan
        img,_,_=self.render(dict(saturation=0,brightness=2,gamma=1.5),a)
        np.testing.assert_array_equal(img[:,:,0],img[:,:,1])
        np.testing.assert_array_equal(img[:,:,1],img[:,:,2])
        self.assertFalse(img[40,40].any())

    def test_custom_palette(self):
        img,_,_=self.render(dict(neutral_rgb=[40,80,120],curvature_strength=0,
                                elevation_mix=0,slope_darkness=0))
        np.testing.assert_array_equal(img[40,40], [40,80,120,255])

    def test_middle_colour_is_an_independent_stop(self):
        tone=dict(valley_rgb=[0,0,255],neutral_rgb=[255,255,0],ridge_rgb=[255,0,0],
                  curvature_strength=1,elevation_mix=0,slope_darkness=0)
        flat=np.full((81,81),500.)
        img,_,curvature=self.render(tone,flat)
        self.assertAlmostEqual(float(curvature[40,40]),0.0)
        np.testing.assert_array_equal(img[40,40], [255,255,0,255])

    def test_fme_middle_colour_changes_flat_curvature_output(self):
        flat=np.full((81,81),500.)
        base=relief(flat,np.isfinite(flat),1,2,.1,60,[200,2000],{},'fme_manual')[0]
        edited=relief(flat,np.isfinite(flat),1,2,.1,60,[200,2000],{},'fme_manual',
                      {'colors':{'curvature_b_mid':[0,255,0]}})[0]
        self.assertFalse(np.array_equal(base[40,40,:3],edited[40,40,:3]))
        np.testing.assert_array_equal(base[:,:,3],edited[:,:,3])

    def test_independent_v040_regression_hash(self):
        y,x=np.mgrid[:97,:103]
        a=500+5*np.sin(x/6)+3*np.cos(y/9)+.001*(x-51)**2-.002*(y-48)**2
        valid=np.isfinite(a);valid[20,30]=False;a[20,30]=np.nan
        rgba=relief(a,valid,1,2,.05,60,[0,3000],None,'independent_v040')[0]
        self.assertEqual(hashlib.sha256(rgba.tobytes()).hexdigest(),
            '32448c448f375a16ac6a29321204af8540fd86e5f9ae566b985004e96199227b')

    def test_brightness_direction(self):
        base,_,_=self.render({})
        dark,_,_=self.render(dict(brightness=.7))
        light,_,_=self.render(dict(gamma=1.4))
        self.assertTrue(np.all(dark[40,40,:3]<base[40,40,:3]))
        self.assertTrue(np.all(light[40,40,:3]>base[40,40,:3]))

    def test_validation(self):
        for invalid in ({'valley_rgb':[256,0,0]}, {'ridge_rgb':[0,1]},
                        {'brightness':float('nan')}, {'gamma':0},
                        {'slope_darkness':1.1}, {'saturation':-1}, {'typo':1}):
            with self.assertRaises(ValueError):color_settings(invalid)


class FMEColorTests(unittest.TestCase):
    def test_two_colour_lut_endpoints(self):
        for low,high in [('elevation_low','elevation_high'),('slope_a_low','slope_a_high'),
                         ('slope_b_low','slope_b_high'),('curvature_a_low','curvature_a_high')]:
            table=lut2(FME_COLORS[low],FME_COLORS[high])
            np.testing.assert_array_equal(table[0],FME_COLORS[low])
            np.testing.assert_array_equal(table[255],FME_COLORS[high])

    def test_curvature_b_endpoints_and_double_middle(self):
        table=lut3(FME_COLORS['curvature_b_low'],FME_COLORS['curvature_b_mid'],
                   FME_COLORS['curvature_b_high'])
        np.testing.assert_array_equal(table[0],[50,96,207])
        np.testing.assert_array_equal(table[127],[255,254,190])
        np.testing.assert_array_equal(table[128],[255,254,190])
        np.testing.assert_array_equal(table[255],[198,72,59])

    def test_normalisation_clips_and_curvature_sign(self):
        np.testing.assert_array_equal(normalise_index([-2,-.1,0,.1,2],-.1,.1),[0,0,128,255,255])
        table=lut3(FME_COLORS['curvature_b_low'],FME_COLORS['curvature_b_mid'],
                   FME_COLORS['curvature_b_high'])
        self.assertGreater(table[0,2],table[0,0])
        self.assertGreater(table[255,0],table[255,2])

    def test_weights_and_hand_calculated_composite(self):
        self.assertAlmostEqual(sum(FME_WEIGHTS.values()),1.0)
        rgb=render_fme(np.array([[200.]]),np.array([[0.]]),np.array([[-.1]]),
                       [200,2000],[0,60],[-.1,.1])
        expected=(np.array([36,36,36])*.125+np.array([247,213,213])*.25+
                  np.array([246,246,246])*.25+np.array([42,95,131])*.125+
                  np.array([50,96,207])*.25)
        np.testing.assert_allclose(rgb[0,0],expected,rtol=0,atol=1e-12)

    def test_stretch_bounds_and_validation(self):
        values=np.array([[[65.,57.,66.],[234.,229.,216.]]])
        stretched=apply_stretch(values,'custom',[[65,234],[57,229],[66,216]])
        np.testing.assert_array_equal(stretched[0,0],[0,0,0])
        np.testing.assert_array_equal(stretched[0,1],[255,255,255])
        for invalid in (
            {'stretch_mode':'bad'}, {'stretch_mode':'custom','stretch_ranges':[[1,1],[0,1],[0,1]]},
            {'weights':{'elevation':.2}}, {'colors':{'curvature_b_mid':[256,0,0]}}):
            with self.assertRaises(ValueError):validate_fme_settings(invalid)

    def test_rendering_record_is_reproducible(self):
        record=rendering_record([200,2000],[0,60],[-.1,.1],{'stretch_mode':'nagano_reference'})
        self.assertEqual(record['mode_id'],'fme_manual')
        self.assertEqual(record['colors']['curvature_b_mid'],[255,254,190])
        self.assertEqual(record['stretch']['ranges_rgb'],[[65.,234.],[57.,229.],[66.,216.]])

    def test_pipeline_manifest_record_contains_complete_fme_spec(self):
        record=rendering_settings(dict(render_mode='fme_manual',elevation_range=[200,2000],
            slope_max=60,curvature_limit=.1,sigma_m=3,input_type='forest',
            fme=validate_fme_settings({'stretch_mode':'none'})))
        self.assertEqual(record['mode_id'],'fme_manual')
        self.assertEqual(len(record['colors']),11)
        self.assertEqual(len(record['weights']),5)
        self.assertEqual(record['terrain_calculation']['input_type'],'forest')


if __name__=='__main__':unittest.main(verbosity=2)
