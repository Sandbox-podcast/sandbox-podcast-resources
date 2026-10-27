import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import monter
from monter import captions, encode, timestamp


class MontageTests(unittest.TestCase):
    def test_timestamp_handles_rounding_and_hours(self):
        self.assertEqual(timestamp(1.9996), '00:00:02,000')
        self.assertEqual(timestamp(3661.125), '01:01:01,125')

    def test_captions_clip_both_edges_and_keep_accents(self):
        rows=[{'start':8,'end':12,'text':'Le besoin précède le code.'},
              {'start':12,'end':16,'text':' Vérifier le résultat.'},
              {'start':16,'end':16,'text':'Sans durée'}]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sous-titres.srt'
            captions(rows,10,14,path)
            result=path.read_text(encoding='utf-8')
            self.assertIn('00:00:00,000 --> 00:00:02,000',result)
            self.assertIn('00:00:02,000 --> 00:00:04,000',result)
            self.assertIn('précède',result)
            self.assertNotIn('Sans durée',result)

    def test_source_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.mp4'
            path.write_bytes(b'original')
            with self.assertRaises(ValueError):
                encode(path,0,1,path)
            self.assertEqual(path.read_bytes(),b'original')

    def test_promos_keep_srt_outside_personal_kits(self):
        with tempfile.TemporaryDirectory() as folder:
            kit=Path(folder)
            production=kit/'production'
            production.mkdir()
            (production/'selection.json').write_text('{"videos": []}',encoding='utf-8')
            source=kit/'source.mp4'
            source.write_bytes(b'original')
            for name in ('lou','loic','nico'):
                (kit/name/'assets').mkdir(parents=True)
            rows=[{'start':3369.95,'end':5195.8,'text':'Une seule couche de sous-titres.'}]
            with (patch.object(monter,'KIT',kit),
                  patch.object(monter,'HERE',production),
                  patch.object(monter,'transcript',return_value=rows),
                  patch.object(monter,'encode') as encoder,
                  patch.object(monter,'verify',return_value={}),
                  patch('builtins.print'),
                  patch('sys.argv',['monter.py','--episode','2','--source',str(source),'--clips-only'])):
                monter.main()
            self.assertEqual(encoder.call_count,3)
            for call,name in zip(encoder.call_args_list,('lou','loic','nico')):
                srt=call.kwargs['srt']
                self.assertTrue(srt.is_file())
                self.assertTrue(srt.is_relative_to(production))
                self.assertIn('Une seule couche',srt.read_text(encoding='utf-8'))
                self.assertFalse(list((kit/name).rglob('*.srt')))
            self.assertEqual(source.read_bytes(),b'original')


if __name__=='__main__':
    unittest.main()
