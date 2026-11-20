"""Offline regression tests. Synthetic detections are never used by the collector."""
import importlib.util
import json
import sqlite3
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('watch', Path(__file__).with_name('rubin-public-watch.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def measurement(i, flux=100., ra=None, band='r'):
    r = {'r:diaSourceId': str(1000+i), 'r:diaObjectId': '9007199254740993001',
         'r:midpointMjdTai': 61000+i, 'r:visit': str(2000+i), 'r:band': band,
         'r:psfFlux': flux, 'r:psfFluxErr': 1., 'r:ra': ra if ra is not None else 100.,
         'r:dec': 0., 'r:raErr': .000001, 'r:decErr': .000001}
    r.update({'r:'+flag: False for flag in w.FLAGS})
    return r


class RegressionTests(unittest.TestCase):
    def test_existing_pilot_database_import_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'rubin.sqlite3'
            payload = w.canonical(measurement(0))
            with sqlite3.connect(path) as pilot:
                pilot.executescript('''
                CREATE TABLE fetches(id INTEGER PRIMARY KEY,retrieved_utc TEXT NOT NULL,selection TEXT NOT NULL,url TEXT NOT NULL,returned_count INTEGER,error TEXT);
                CREATE TABLE detections(source_id TEXT PRIMARY KEY,first_seen_utc TEXT NOT NULL);
                CREATE TABLE record_versions(source_id TEXT NOT NULL,payload_hash TEXT NOT NULL,first_fetch_id INTEGER NOT NULL,payload_json TEXT NOT NULL,PRIMARY KEY(source_id,payload_hash));
                CREATE TABLE fetch_records(fetch_id INTEGER NOT NULL,source_id TEXT NOT NULL,payload_hash TEXT NOT NULL,PRIMARY KEY(fetch_id,source_id,payload_hash));
                ''')
                pilot.execute("INSERT INTO fetches VALUES(1,?,'hostless_candidate','https://example.invalid',1,NULL)", (w.now(),))
                pilot.execute('INSERT INTO detections VALUES(?,?)', ('1000', w.now()))
                pilot.execute('INSERT INTO record_versions VALUES(?,?,1,?)', ('1000', 'oldhash', payload))
                pilot.execute("INSERT INTO fetch_records VALUES(1,'1000','oldhash')")
            db = w.connect(path)
            self.assertEqual(db.execute('SELECT payload_json FROM record_versions').fetchone()[0], payload)
            self.assertEqual(db.execute('SELECT count(*) FROM rw_measurements').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT tag FROM rw_selection').fetchone()[0], 'hostless_candidate')
            self.assertEqual(len(list((Path(directory)/'backups').glob('*.sqlite3'))), 1)
            db.close()

    def test_integer_ids_not_rounded(self):
        r = measurement(0)
        self.assertEqual(w.normalize(r)['oid'], '9007199254740993001')
        r['r:diaObjectId'] = 9e18
        with self.assertRaises(ValueError): w.normalize(r)

    def test_quality_rejects_saturation_and_unknown(self):
        r = measurement(0); r['r:pixelFlags_saturatedCenter'] = True
        self.assertFalse(w.normalize(r)['usable'])
        r = measurement(0); del r['r:psfFlux_flag']
        self.assertFalse(w.normalize(r)['usable'])
        self.assertIn('psfFlux_flag', w.normalize(r)['missing'])

    def test_negative_difference_flux_is_valid(self):
        self.assertTrue(w.normalize(measurement(0, -100))['usable'])

    def test_constant_flux_and_position_do_not_flag(self):
        rows = [w.normalize(measurement(i)) for i in range(6)]
        self.assertEqual(w.screen('1', rows, set()), [])

    def test_flux_change_requires_same_filter_and_multiple_days(self):
        rows = [w.normalize(measurement(i, 100+i*50)) for i in range(6)]
        flags = dict(w.screen('1', rows, set()))
        self.assertIn('flux:r', flags)
        mixed = [w.normalize(measurement(i, 100+i*50, band='ugrizy'[i])) for i in range(6)]
        self.assertEqual(w.screen('1', mixed, set()), [])
        duplicate = rows[0].copy(); duplicate['sid'] = '9999'; duplicate['psfFlux'] = 500
        self.assertEqual(len(w.unique_visits([rows[0], duplicate])), 1)

    def test_position_fit_and_ra_wrap(self):
        rows = [w.normalize(measurement(i, ra=(359.9999+i/3600) % 360)) for i in range(6)]
        flags = dict(w.screen('1', rows, set()))
        self.assertIn('position:r', flags)
        self.assertAlmostEqual(flags['position:r']['rate_arcsec_day'], 1, places=3)
        rows[0]['known_sso'] = True
        self.assertNotIn('position:r', dict(w.screen('1', rows, set())))

    def test_sqlite_dedup_revisions_and_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            db = w.connect(Path(directory)/'rubin.sqlite3')
            collector = w.Collector(db)
            records = [measurement(i, 100+i*50) for i in range(6)]
            collector.request = lambda *args, **kwargs: (records, 'https://example.invalid/test')
            self.assertTrue(collector.fetch('hostless_candidate', 'tags', n=6))
            self.assertTrue(collector.fetch('hostless_candidate', 'tags', n=6))
            self.assertEqual(db.execute('SELECT count(*) FROM detections').fetchone()[0], 6)
            self.assertEqual(db.execute('SELECT count(*) FROM record_versions').fetchone()[0], 6)
            records[0]['r:reliability'] = .5
            collector.fetch('hostless_candidate', 'tags', n=6)
            self.assertEqual(db.execute('SELECT count(*) FROM record_versions').fetchone()[0], 7)
            groups = w.analyze(db)
            audit = db.execute('SELECT count(*) FROM rw_evidence').fetchone()[0]
            w.analyze(db)
            self.assertEqual(db.execute('SELECT count(*) FROM rw_evidence').fetchone()[0], audit)
            # Gap entries must not break daily reports.
            with db:
                db.execute('INSERT INTO rw_coverage(utc,selection,detail) VALUES (?,?,?)',
                           (w.now(), 'collector-gap', json.dumps({'hours':25,'completeness':'GAP'})))
            dest = w.report(db, Path(directory), groups)
            self.assertTrue((dest/'index.html').exists())
            self.assertIn('difference', (dest/'index.html').read_text().lower())
            for row in records: row['r:pixelFlags_bad'] = True
            collector.fetch('hostless_candidate', 'tags', n=6)
            w.analyze(db)
            self.assertEqual(db.execute("SELECT count(*) FROM rw_candidates WHERE status='review'").fetchone()[0], 0)
            db.close()

    def test_invalid_batch_rolls_back_and_logs_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            db = w.connect(Path(directory)/'rubin.sqlite3')
            collector = w.Collector(db)
            r = measurement(1); r['r:diaSourceId'] = 3.14
            collector.request = lambda *args, **kwargs: ([measurement(0), r], 'https://example.invalid/test')
            self.assertFalse(collector.fetch('test', 'tags', n=2))
            self.assertEqual(db.execute('SELECT count(*) FROM detections').fetchone()[0], 0)
            self.assertIsNotNone(db.execute('SELECT error FROM fetches').fetchone()[0])
            db.close()

    def test_time_conversion_tai_is_not_utc(self):
        self.assertNotEqual(w.utc(61000), w.Time(61000, format='mjd', scale='tai').isot+'Z')


if __name__ == '__main__':
    unittest.main()
