import importlib.util
import errno
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import numpy as np
from csmap_sheets.engine import input_sources as inputs, gsi_dem as gsi, point_inputs as points, forest_dem as forest


def config(**kwargs):
    return {**inputs.DEFAULTS,'cell_size':1.,'source_nodata':None,'target_crs':'EPSG:6677',
            'max_pixels':10000000,**kwargs}


def xml(values='地表面,10\n地表面,0\n海水面,0\n地表面,-9999\n地表面,-2',start='1 0',crs='fguuid:jgd2011.bl',order='+x+y'):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Dataset xmlns="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema" xmlns:gml="http://www.opengis.net/gml/3.2">
<DEM><mesh>533900</mesh><coverage>
<gml:boundedBy><gml:Envelope srsName="{crs}"><gml:lowerCorner>35 139</gml:lowerCorner><gml:upperCorner>35.002 139.003</gml:upperCorner></gml:Envelope></gml:boundedBy>
<gml:gridDomain><gml:Grid dimension="2"><gml:limits><gml:GridEnvelope><gml:low>0 0</gml:low><gml:high>2 1</gml:high></gml:GridEnvelope></gml:limits></gml:Grid></gml:gridDomain>
<gml:rangeSet><gml:DataBlock><gml:tupleList>{values}</gml:tupleList></gml:DataBlock></gml:rangeSet>
<gml:coverageFunction><gml:GridFunction><gml:sequenceRule order="{order}">Linear</gml:sequenceRule><gml:startPoint>{start}</gml:startPoint></gml:GridFunction></gml:coverageFunction>
</coverage></DEM></Dataset>'''.encode('utf-8')


class InputTests(unittest.TestCase):
    def test_network_discovery_retries_transient_smb_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'dem.tif';source.touch()
            real_stat=inputs.os.stat;calls={'count':0}
            def flaky_stat(path,*args,**kwargs):
                if os.fspath(path)==str(source) and calls['count']==0:
                    calls['count']+=1
                    exc=OSError(errno.EIO,'network share disconnected');exc.winerror=64
                    raise exc
                if os.fspath(path)==str(source):calls['count']+=1
                return real_stat(path,*args,**kwargs)
            with patch.object(inputs.os,'stat',side_effect=flaky_stat), \
                 patch.object(inputs.time,'sleep') as sleep:
                found=inputs.discover([str(source)],tmp,config())
            self.assertEqual(found,[str(source)])
            self.assertEqual(calls['count'],2)
            sleep.assert_called_once_with(1.0)

    def test_network_folder_scan_retries_transient_smb_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'dem.tif';source.touch()
            real_scandir=inputs.os.scandir;calls={'count':0}
            def flaky_scandir(path):
                if str(path)==tmp and calls['count']==0:
                    calls['count']+=1
                    exc=OSError(errno.EIO,'network share disconnected');exc.winerror=64
                    raise exc
                if str(path)==tmp:calls['count']+=1
                return real_scandir(path)
            with patch.object(inputs.os,'scandir',side_effect=flaky_scandir), \
                 patch.object(inputs.time,'sleep') as sleep:
                found=inputs.discover([tmp],tmp,config())
            self.assertEqual(found,[str(source)])
            self.assertEqual(calls['count'],2)
            sleep.assert_called_once_with(1.0)

    def test_network_discovery_fails_with_actionable_message_after_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'dem.tif'
            def disconnected(*args,**kwargs):
                exc=OSError(errno.EIO,'network share disconnected');exc.winerror=64
                raise exc
            with patch.object(inputs.os,'stat',side_effect=disconnected), \
                 patch.object(inputs.time,'sleep') as sleep:
                with self.assertRaisesRegex(OSError,'ネットワーク共有へアクセスできません'):
                    inputs.discover([str(source)],tmp,config())
            self.assertEqual(sleep.call_count,3)

    def test_direct_file_discovery_uses_single_metadata_stat(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'dem.tif';source.touch()
            real_stat=inputs.os.stat;checked=[]
            def counting_stat(path,*args,**kwargs):
                if os.fspath(path)==str(source):checked.append(path)
                return real_stat(path,*args,**kwargs)
            with patch.object(inputs.os,'stat',side_effect=counting_stat):
                found=inputs.discover([str(source)],tmp,config())
            self.assertEqual(found,[str(source)])
            self.assertEqual(len(checked),1)

    def test_raw_qgis_file_parameter_is_authoritative(self):
        selected=['C:/gis_data/kouchi_pref/04HD722.copc.laz']
        self.assertEqual(inputs.explicit_file_parameter(selected),selected)
        self.assertEqual(inputs.explicit_file_parameter('a.laz;b.laz'),['a.laz','b.laz'])
        self.assertEqual(inputs.explicit_file_parameter(None),[])

    def test_unicode_lidar_path_is_staged_with_ascii_name(self):
        with tempfile.TemporaryDirectory(prefix='csmap_ascii_') as tmp:
            root=Path(tmp);source=root/'日本語点群.laz';source.write_bytes(b'test')
            staged,staged_path,method=points.stage_unicode_source(source,root/'work',0)
            self.assertTrue(staged.isascii())
            self.assertEqual(Path(staged).read_bytes(),b'test')
            self.assertIn(method,('hardlink','copy'))
            staged_path.unlink()

    def test_ascii_lidar_path_is_not_replaced(self):
        with tempfile.TemporaryDirectory(prefix='csmap_ascii_') as tmp:
            source=Path(tmp)/'cloud.laz';source.write_bytes(b'test')
            staged,staged_path,method=points.stage_unicode_source(source,Path(tmp)/'work',0)
            self.assertEqual(staged,str(source.resolve()))
            self.assertIsNone(staged_path);self.assertIsNone(method)

    def test_lem_metadata_and_fixed_width_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);header=root/'09aa00.csv';lem=root/'09aa00.lem'
            header.write_text('東西方向の点数,3\n南北方向の点数,2\n東西方向のデータ間隔,1\n南北方向のデータ間隔,1\n区画左下X座標,0\n区画左下Y座標,0\n区画右上X座標,200\n区画右上Y座標,300\n平面直角座標系番号,9\n',encoding='cp932')
            lines=[]
            for row,values in enumerate(([1000,-9999,1020],[1100,1110,-1111]),1):
                lines.append(' '*6+f'{row:4d}'+''.join(f'{v:5d}' for v in values))
            lem.write_text('\r\n'.join(lines)+'\r\n',encoding='ascii')
            a,gt,meta=forest.read_lem(lem,header,100)
            np.testing.assert_array_equal(a,[[100,inputs.NODATA,102],[110,111,inputs.NODATA]])
            self.assertEqual(gt,(0.,1.,0.,2.,0.,-1.));self.assertEqual(meta['zone'],9)

    def test_forest_classification_and_xyz_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);grid=root/'grid.csv';grid.write_text('X,Y,Z\n10,20,30\n11,20,31\n')
            tif=root/'dem.tif';tif.touch();tfw=root/'dem.tfw';tfw.touch()
            records=forest.classify_sources([grid,tif,tfw])
            self.assertEqual([r['kind'] for r in records],['grid','raster'])
            detected=forest.autodetect_xyz(grid)
            self.assertEqual(detected['text_skip_rows'],1);self.assertEqual(detected['text_delimiter'],'comma')
            self.assertEqual(detected['text_axis_order'],'north_east')

    def test_world_file_pair_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tif=root/'DEM.TIF';tif.touch()
            self.assertFalse(inputs.has_world_file(tif))
            (root/'dem.TFW').touch()
            self.assertTrue(inputs.has_world_file(tif))

    def test_forest_grid_cell_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'grid.csv'
            p.write_text('X,Y,Z\n100,200,1\n100.5,200,2\n100,199.5,3\n100.5,199.5,4\n')
            detected=forest.autodetect_xyz(p)
            self.assertEqual(inputs.infer_grid_cell(p,{**config(),**detected}),.5)

    def test_forest_zip_extracts_pairs_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'forest.zip'
            header='東西方向の点数,1\n南北方向の点数,1\n東西方向のデータ間隔,1\n南北方向のデータ間隔,1\n区画左下X座標,0\n区画左下Y座標,0\n区画右上X座標,100\n区画右上Y座標,100\n'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('tile/a.csv',header.encode('cp932'));z.writestr('tile/a.lem',' '*6+'   1'+' 1000\r\n')
                z.writestr('readme.pdf',b'ignored')
            paths,archives=forest.expand_sources([archive],root/'work')
            self.assertEqual(len(forest.classify_sources(paths)),1);self.assertEqual(archives[0]['members'],2)
            bad=root/'bad.zip'
            with zipfile.ZipFile(bad,'w') as z:z.writestr('../evil.csv','1,2,3')
            with self.assertRaises(ValueError):forest.extract_archive(bad,root/'badwork')

    def test_forest_expand_sources_scans_each_directory_once(self):
        # 2026-09-28 ユーザー報告(「Lemが流れない」)の再発防止テスト。
        # 対応CSVを持たないLEMファイルが大量にある場合でも、companion.exists()が
        # Falseになるたびフォルダ全体をglob()し直す(=O(件数^2))のではなく、
        # ディレクトリごとに一度だけ.csv一覧をキャッシュして引くこと(=O(件数))を確認する。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            names=[]
            for i in range(50):
                lem=root/f'{i:03d}lc999_1g.lem'
                lem.write_text(' '*6+'   1'+' 1000\r\n',encoding='ascii')
                names.append(lem)
            original_glob=Path.glob
            calls=[]
            def counting_glob(self,pattern):
                if pattern=='*':
                    calls.append(self)
                return original_glob(self,pattern)
            with patch.object(Path,'glob',counting_glob):
                expanded,archives=forest.expand_sources(names,root/'work')
            # 対応CSVが存在しないため展開結果は入力LEM数のまま(companionは追加されない)。
            self.assertEqual(len(expanded),50)
            self.assertEqual(archives,[])
            # 同一ディレクトリに対するglob('*.csv')は1回だけ(キャッシュが効いている)。
            self.assertEqual(len(calls),1)

    def test_forest_expand_sources_finds_case_insensitive_companion_via_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            lem=root/'a.lem';lem.write_text(' '*6+'   1'+' 1000\r\n',encoding='ascii')
            # ステム大文字小文字違いの.csvでもキャッシュ経由で検出できることを確認する。
            (root/'A.CSV').write_text('東西方向の点数,1\n',encoding='utf-8')
            expanded,_=forest.expand_sources([lem],root/'work')
            self.assertEqual(len(expanded),2)

    LEM_HEADER = ('東西方向の点数,1\n南北方向の点数,1\n東西方向のデータ間隔,1\n'
                  '南北方向のデータ間隔,1\n区画左下X座標,0\n区画左下Y座標,0\n'
                  '区画右上X座標,100\n区画右上Y座標,100\n')

    def test_forest_expand_sources_accepts_txt_companion_when_no_csv(self):
        # 2026-09-30 ユーザー報告: 森林航空レーザ成果のデータでは、LEMの対応
        # メタデータファイルの拡張子が規則上は.csvだが実態は.txtの場合が多い。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            lem=root/'06je983_1g.lem';lem.write_text(' '*6+'   1'+' 1000\r\n',encoding='ascii')
            (root/'06je983_1g.txt').write_text(self.LEM_HEADER,encoding='cp932')
            expanded,_=forest.expand_sources([lem],root/'work')
            self.assertEqual(len(expanded),2)
            records=forest.classify_sources(expanded)
            self.assertEqual([r['kind'] for r in records],['lem'])

    def test_forest_classify_sources_prefers_csv_over_txt_companion(self):
        # 同一stemに.csvと.txtが両方存在する場合は.csvを優先する(仮定・明記)。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            lem=root/'a.lem';lem.write_text(' '*6+'   1'+' 1000\r\n',encoding='ascii')
            csv_path=root/'a.csv';csv_path.write_text(self.LEM_HEADER,encoding='cp932')
            txt_path=root/'a.txt';txt_path.write_text('this is not LEM metadata\n',encoding='utf-8')
            expanded,_=forest.expand_sources([lem],root/'work')
            self.assertIn(csv_path,expanded)
            self.assertNotIn(txt_path,expanded)
            records=forest.classify_sources([lem,csv_path])
            self.assertEqual([r['kind'] for r in records],['lem'])

    def test_forest_classify_sources_standalone_txt_grid_is_unaffected(self):
        # .txtは単体のXYZグリッド入力としても使われる。LEM companion扱いにならず
        # 従来どおりgridとして分類されることを確認する(回帰防止)。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            grid=root/'grid.txt';grid.write_text('X,Y,Z\n10,20,30\n11,20,31\n')
            records=forest.classify_sources([grid])
            self.assertEqual([r['kind'] for r in records],['grid'])

    def test_is_lem_metadata_does_not_read_past_probe_bound_on_large_grid_txt(self):
        # 2026-09-30 ユーザー報告の再発防止テスト。検証用データでは、LEMのcompanion
        # メタデータとは無関係に、同じ命名規則の巨大な(最大約100MB)単体.txtグリッドが
        # 同居するフォルダー(「txt形式」等)が存在する。is_lem_metadata()がファイル
        # 全体を読み込んでいると、この種のファイルが多数(実例では714件)ある場合に
        # 大量のI/O・メモリ確保が積み重なり、QGISが長時間「応答なし」になっていた。
        # ここでは、プローブ上限を超えるファイルに対してファイル全体は読み込まれない
        # ことを、open()呼び出しに渡されるサイズ上限を検証することで確認する。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            huge=root/'06ke081_1g.txt'
            # 実際に大容量データを書き込まずスパースファイルで巨大サイズを再現する。
            with open(huge,'wb') as f:
                f.seek(forest.LEM_METADATA_PROBE_BYTES*8)
                f.write(b'0')
            calls=[]
            original_open=open
            def counting_open(path,*args,**kwargs):
                fh=original_open(path,*args,**kwargs)
                if str(path)==str(huge):
                    real_read=fh.read
                    def counting_read(size=-1,*a,**kw):
                        calls.append(size)
                        return real_read(size,*a,**kw)
                    fh.read=counting_read
                return fh
            with patch('builtins.open',counting_open):
                result=forest.is_lem_metadata(huge)
            self.assertFalse(result)
            self.assertTrue(calls)
            self.assertLessEqual(max(calls),forest.LEM_METADATA_PROBE_BYTES)

    def test_is_lem_metadata_accepts_real_size_companion_beyond_naive_estimate(self):
        # 実機で確認された本物のLEM対応メタデータ(.csv)は数百バイトではなく最大約35KB
        # あった。プローブ上限(256KiB)がこれを十分に上回ることを確認する回帰テスト。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            header=root/'06ne882_1g.csv'
            # ヘッダー本体の後ろに実在のデータを模した大量の行を追加し、合計サイズを
            # 実測に近い約35KBまで水増しする(内容自体はパース対象外の余分な行)。
            padding='\n'.join(f'メモ{i},{i}' for i in range(2800))
            header.write_text(self.LEM_HEADER+padding,encoding='cp932')
            self.assertGreater(header.stat().st_size,30000)
            self.assertTrue(forest.is_lem_metadata(header))

    def test_forest_classify_sources_large_standalone_txt_grid_is_not_metadata(self):
        # txt形式フォルダーのような、.lem companionを伴わない大容量.txtグリッドが
        # gridとして分類され、メタデータ判定のための全文読み込みで固まらないことを確認。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            grid=root/'06ke081_1g.txt'
            with open(grid,'wb') as f:
                f.seek(forest.LEM_METADATA_PROBE_BYTES*4)
                f.write(b'0')
            records=forest.classify_sources([grid])
            self.assertEqual([r['kind'] for r in records],['grid'])

    def test_gsi_start_order_and_nodata(self):
        a,gt,crs,meta=next(gsi.parse_dem(xml()))
        np.testing.assert_array_equal(a,[[inputs.NODATA,10,0],[inputs.NODATA,inputs.NODATA,-2]])
        np.testing.assert_allclose(gt,[139,.001,0,35.002,0,-.001])
        self.assertEqual(crs,'EPSG:6668');self.assertEqual(meta['start_point'],[1,0])

    def test_gsi_short_tail_and_multiple_dem(self):
        a,*_=next(gsi.parse_dem(xml('地表面,5','2 1')))
        self.assertEqual(a[-1,-1],5)
        self.assertEqual(np.count_nonzero(a!=inputs.NODATA),1)
        self.assertEqual(list(gsi.parse_dem(b'<metadata/>')),[])

    def test_gsi_accepts_reverse_y_linear_traversal(self):
        a,_,_,meta=next(gsi.parse_dem(xml('地表面,1\n地表面,2\n地表面,3\n地表面,4\n地表面,5\n地表面,6',
            start='0 1',order='+x-y')))
        np.testing.assert_array_equal(a,[[4,5,6],[1,2,3]])
        self.assertEqual(meta['traversal_order'],'+x-y')

    def test_gsi_unknown_crs_not_guessed(self):
        _,_,srs,_=next(gsi.parse_dem(xml(crs='EPSG:4326')))
        self.assertEqual(srs,'EPSG:4326')
        with self.assertRaises(ValueError):list(gsi.parse_dem(xml(crs='')))

    def test_gsi_jgd2024_alias_and_shiftjis(self):
        _,_,srs,meta=next(gsi.parse_dem(xml(crs='fguuid:jgd2024.bl')))
        self.assertEqual(srs,'EPSG:6668');self.assertTrue(meta['jgd2024_horizontal_alias'])
        sjis=xml().decode('utf-8').replace('encoding="UTF-8"','encoding="Shift_JIS"').encode('shift_jis')
        np.testing.assert_array_equal(next(gsi.parse_dem(sjis))[0],next(gsi.parse_dem(xml()))[0])

    def test_gsi_reject_overflow_bad_grid_and_entities(self):
        for data in (xml(start='3 0'),xml('地表面,1\n'*7),xml().replace(b'Linear',b'Boustrophedonic'),
                     b'<!DOCTYPE Dataset [<!ENTITY foo "bar">]><Dataset/>'):
            with self.assertRaises(ValueError):list(gsi.parse_dem(data))
        with self.assertRaises(ValueError):list(gsi.parse_dem(xml(),max_pixels=5))

    def test_discovery_case_recursion_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sub=root/'sub';sub.mkdir()
            a=root/'a.LAZ';b=sub/'DEM[1].las';a.touch();b.touch();(root/'notes.txt').touch()
            self.assertEqual(inputs.discover([str(root),str(a)],root,config(input_type='lidar')),[str(a),str(b)])
            self.assertEqual(inputs.discover([str(root)],root,config(input_type='lidar',recursive=False)),[str(a)])
            with self.assertRaises(ValueError):inputs.discover([str(a)],root,config(input_type='gsi'))

    def test_individually_selected_companion_only_extensions_are_silently_skipped(self):
        # v0.9.3: フォルダー選択時は元々.tfw等が黙ってスキップされていたが、
        # 個別ファイル選択時だけ「Input extension does not match input_type」で
        # 強制停止していた（ユーザー報告、2026-09-30）。.tfw/.tifw/.wldは
        # そもそも単独では主入力になり得ない同梱物なので、個別選択でも
        # フォルダー選択と同じく黙ってスキップするよう統一したことを確認する。
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tif=root/'dem.tif';tif.touch();tfw=root/'dem.tfw';tfw.touch()
            self.assertEqual(inputs.discover([str(tif),str(tfw)],root,config(input_type='raster')),[str(tif)])
            # tfw/tifw/wldのみを個別選択した場合は、有効な入力が1件もないため
            # 従来どおり明確なエラーで停止する(黙って「入力0件」を通さない)。
            with self.assertRaises(ValueError):
                inputs.discover([str(tfw)],root,config(input_type='raster'))
            # 同梱物とは無関係の拡張子不一致は、引き続き個別選択時にエラーとする。
            bad=root/'notes.txt';bad.touch()
            with self.assertRaises(ValueError):
                inputs.discover([str(bad)],root,config(input_type='raster'))

    def test_text_columns_axes_nodata_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'測量.csv';p.write_text('番号,X,Y,Z\n1,100,200,0\n2,101,200,-9999\n3,102,200,-3\n',encoding='cp932')
            c=config(text_columns=[2,3,4],text_axis_order='north_east',text_encoding='cp932',source_nodata=-9999)
            self.assertEqual(list(inputs.text_rows(p,c)),[(200.,100.,0.),(200.,102.,-3.)])
            p.write_text('100  200  3\n',encoding='utf-8')
            self.assertEqual(list(inputs.text_rows(p,config(text_skip_rows=0,text_delimiter='space'))),[(100.,200.,3.)])

    def test_text_bad_rows_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.csv';p.write_text('X,Y,Z\n1,nan,3\n')
            with self.assertRaises(ValueError):list(inputs.text_rows(p,config()))
            p.write_text('X,Y,Z\n1,2\n')
            with self.assertRaises(ValueError):list(inputs.text_rows(p,config()))

    def test_regular_grid_pixel_centers_and_holes(self):
        class SRS:
            def IsProjected(self):return True
            def GetLinearUnits(self):return 1
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'grid.csv';p.write_text('X,Y,Z\n10,20,100\n11,20,101\n10,21,110\n')
            with patch.object(inputs,'crs_of',return_value=SRS()),patch.object(inputs,'raster_write') as write:
                inputs.text_grid(p,Path(tmp)/'grid.tif',config(input_crs='EPSG:6677'),None,None)
                a=write.call_args.args[1];gt=write.call_args.args[2]
                np.testing.assert_array_equal(a,[[110,inputs.NODATA],[100,101]])
                self.assertEqual(gt,(9.5,1.,0,21.5,0,-1.))
                p.write_text('X,Y,Z\n10,20,100\n10.3,20,101\n')
                with self.assertRaises(ValueError):inputs.text_grid(p,Path(tmp)/'bad.tif',config(input_crs='EPSG:6677'),None,None)

    def test_settings_validation(self):
        inputs.validate_input(config())
        for extra in [dict(text_columns=[1,1,3]),dict(ground_classes=[-1]),dict(point_radius=0),
            dict(input_type='text'),dict(lidar_mode='guess'),dict(point_tile_size=9999),
            dict(forest_axis_order='guess'),dict(forest_lem_coordinate_scale='bad'),dict(forest_grid_cell='bad')]:
            with self.assertRaises(ValueError):inputs.validate_input(config(**extra))

    def test_pdal_branch_tags_and_halo(self):
        records=[dict(read_path=f'file{i}.laz',reader='readers.las',crs='EPSG:6677') for i in range(2)]
        c=config(input_type='lidar',ground_classes=[2,8],lidar_mode='classified')
        pipe,halo=points.build_pipeline(records,(0,0,512,512),c,'out.tif')
        stages=pipe['pipeline'];writer=stages[-1]
        self.assertEqual(writer['inputs'],['K0','K1']);self.assertEqual(writer['window_size'],0)
        self.assertEqual(writer['origin_x'],-halo)
        self.assertEqual(writer['width'],512+2*halo)
        self.assertIn('Classification == 8',stages[3]['expression'])
        self.assertEqual(stages[4]['type'],'readers.las')
        self.assertEqual(stages[5]['inputs'],['R1'])

    def test_auto_classification_resets_and_preserves_review_output(self):
        records=[dict(read_path='a.laz',reader='readers.las',crs='EPSG:6677')]
        pipe,halo=points.build_pipeline(records,(0,0,512,512),config(input_type='lidar',lidar_mode='auto'),'out.tif','review.laz')
        stages=pipe['pipeline']
        self.assertGreater(halo,36)
        self.assertTrue(any(s.get('value')=='Classification = 0' for s in stages))
        self.assertTrue(any(s.get('filename')=='review.laz' for s in stages))
        self.assertEqual(stages[-1]['inputs'],['GROUND'])

    def test_process_and_pre_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'log.json'
            result=points.run_process(sys.executable,['-c','import json; print(json.dumps({"ok":True}))'],log,json_output=True)
            self.assertEqual(result,{'ok':True})
            class Feedback:
                def isCanceled(self):return True
            with self.assertRaises(RuntimeError):points.run_process(sys.executable,['-c','pass'],log,Feedback())


    def test_forest_nodata_codes_excludes_band_nodata(self):
        self.assertEqual(inputs.forest_nodata_codes(-9999.,-9999.),(-1111.,))
        self.assertEqual(inputs.forest_nodata_codes(-32768.,-9999.),(-9999.,-1111.))
        self.assertEqual(inputs.forest_nodata_codes(None,None),(-9999.,-1111.))
        self.assertEqual(inputs.forest_nodata_codes(None,-5.),(-9999.,-1111.,-5.))

    def test_mask_forest_nodata_codes_skips_open_when_no_codes(self):
        class NoGDAL:
            def Open(self,path):raise AssertionError('must not open')
        self.assertEqual(inputs.mask_forest_nodata_codes('a.tif','b.tif',(),None,NoGDAL()),('a.tif',None,0))

    def test_crs_probe_raster_returns_file_unchanged(self):
        self.assertEqual(inputs.crs_probe_raster('dem.tif',True),'dem.tif')

    def test_crs_probe_raster_picks_first_raster_in_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'b.tif').touch();(root/'A.TIF').touch();(root/'a.tfw').touch()
            self.assertEqual(Path(inputs.crs_probe_raster(root,False)).name,'A.TIF')

    def test_crs_probe_raster_respects_recursive_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sub').mkdir();(root/'sub'/'dem.tif').touch()
            self.assertEqual(Path(inputs.crs_probe_raster(root,True)).name,'dem.tif')
            with self.assertRaises(ValueError):inputs.crs_probe_raster(root,False)

    def test_crs_probe_raster_rejects_folder_without_raster(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'readme.txt').touch()
            with self.assertRaises(ValueError):inputs.crs_probe_raster(root,True)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):inputs.crs_probe_raster(tmp,True)


@unittest.skipUnless(importlib.util.find_spec('osgeo'),'GDAL unavailable')
class GDALInputTests(unittest.TestCase):
    def test_zipped_xml_to_aligned_dem(self):
        import zipfile
        from osgeo import gdal,osr
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'dem.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('../../not-extracted.xml',xml('地表面,100\n'*6,start='0 0'))
                z.writestr('metadata.xml','<metadata/>')
            c=config(input_type='gsi',inputs=[str(archive)],cell_size=10.)
            result,report=inputs.prepare_inputs(c,root/'input',gdal,osr)
            self.assertEqual(report['status'],'completed')
            self.assertEqual(len(result['inputs']),1)
            ds=gdal.Open(result['inputs'][0]);self.assertIsNotNone(ds)
            self.assertEqual(ds.GetRasterBand(1).GetNoDataValue(),inputs.NODATA)
            a=ds.ReadAsArray();np.testing.assert_allclose(a[a!=inputs.NODATA],100.,atol=.001)
            ds=None
            self.assertFalse((root/'not-extracted.xml').exists())


    def _forest_tiff(self, gdal, osr, path, array, nodata):
        ds=gdal.GetDriverByName('GTiff').Create(str(path),array.shape[1],array.shape[0],1,gdal.GDT_Float32)
        ds.SetGeoTransform((0.,1.,0.,10.,0.,-1.))
        srs=osr.SpatialReference();srs.ImportFromEPSG(6677);ds.SetProjection(srs.ExportToWkt())
        if nodata is not None:ds.GetRasterBand(1).SetNoDataValue(nodata)
        ds.GetRasterBand(1).WriteArray(array);ds=None

    def _prepare_forest(self, gdal, osr, root, array, nodata, **kwargs):
        tif=root/'dem.tif';self._forest_tiff(gdal,osr,tif,array,nodata)
        c=config(input_type='forest',inputs=[str(tif)],**kwargs)
        result,report=inputs.prepare_inputs(c,root/'work',gdal,osr)
        ds=gdal.Open(result['inputs'][0]);a=ds.ReadAsArray();ds=None
        return a,report

    def test_forest_tiff_masks_codes_that_differ_from_nodata_tag(self):
        from osgeo import gdal,osr
        array=np.full((10,10),100.,dtype='float32')
        array[2,2]=-9999.;array[5,5]=-1111.;array[8,8]=-32768.
        with tempfile.TemporaryDirectory() as tmp:
            a,report=self._prepare_forest(gdal,osr,Path(tmp),array,-32768.)
            self.assertEqual(report['detected'][0]['extra_nodata_cells'],2)
            valid=a[a!=inputs.NODATA]
            self.assertTrue(valid.size>0)
            np.testing.assert_allclose(valid,100.,atol=.001)

    def test_forest_tiff_without_nodata_tag_masks_both_codes(self):
        from osgeo import gdal,osr
        array=np.full((10,10),100.,dtype='float32');array[2,2]=-9999.;array[5,5]=-1111.
        with tempfile.TemporaryDirectory() as tmp:
            a,report=self._prepare_forest(gdal,osr,Path(tmp),array,None)
            self.assertEqual(report['detected'][0]['extra_nodata_cells'],2)
            np.testing.assert_allclose(a[a!=inputs.NODATA],100.,atol=.001)

    def test_forest_tiff_without_extra_codes_is_not_copied(self):
        from osgeo import gdal,osr
        array=np.full((10,10),100.,dtype='float32');array[2,2]=-9999.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a,report=self._prepare_forest(gdal,osr,root,array,-9999.)
            self.assertEqual(report['detected'][0]['extra_nodata_cells'],0)
            self.assertEqual(list((root/'work').glob('forest_masked_*')),[])
            np.testing.assert_allclose(a[a!=inputs.NODATA],100.,atol=.001)


@unittest.skipUnless(importlib.util.find_spec('osgeo') and shutil.which('pdal'),'GDAL/PDAL unavailable')
class PDALInputTests(unittest.TestCase):
    def test_classified_las_and_laz_match_and_ignore_canopy(self):
        from osgeo import gdal,osr
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);text=root/'cloud.csv'
            with text.open('w') as f:
                f.write('X,Y,Z,Classification\n')
                for x in range(30,98):
                    for y in range(30,98):
                        f.write(f'{x+.5},{y+.5},100,2\n{x+.5},{y+.5},150,5\n')
            arrays=[]
            for ext in ('las','laz'):
                src=root/f'cloud.{ext}'
                pipeline={'pipeline':[{'type':'readers.text','filename':str(text),'override_srs':'EPSG:6677'},
                    {'type':'writers.las','filename':str(src),'minor_version':4,'dataformat_id':6}]}
                spec=root/f'create_{ext}.json';spec.write_text(json.dumps(pipeline))
                points.run_process(shutil.which('pdal'),['pipeline',str(spec)],root/f'create_{ext}.log')
                c=config(input_type='lidar',inputs=[str(src)],point_tile_size=64,point_radius=1.)
                prepared,report=inputs.prepare_inputs(c,root/f'work_{ext}',gdal,osr)
                for path in prepared['inputs']:
                    ds=gdal.Open(path);a=ds.ReadAsArray();ds=None
                    np.testing.assert_allclose(a[a!=inputs.NODATA],100,atol=.001)
                arrays.append([gdal.Open(p).ReadAsArray() for p in prepared['inputs']])
            self.assertEqual(len(arrays[0]),len(arrays[1]))
            for a,b in zip(*arrays):np.testing.assert_array_equal(a,b)

if __name__=='__main__':unittest.main(verbosity=2)
