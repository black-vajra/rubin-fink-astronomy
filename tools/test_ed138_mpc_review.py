"""Check native MPC parsing and exact source-ID comparison used in the new review."""
import unittest
from pathlib import Path
from astropy.coordinates import SkyCoord
from astropy import units as u
from ed138_mpc_benchmark import parse
from nightly_data_review import keyed

ROOT=Path(__file__).resolve().parents[1]
class ReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/'reports/2026/11/21/ed138-public-astrometry/MPEC-2026-U85.html').read_bytes()
        cls.rows=parse(cls.raw)
    def test_counts_stations_and_calendar(self):
        self.assertEqual(len(self.rows),74)
        rubin=[r for r in self.rows if r['station']=='X05']
        decam=[r for r in self.rows if r['station']=='W84']
        self.assertEqual((len(rubin),len({r['UTC'][:10] for r in rubin})),(30,20))
        self.assertEqual((len(decam),len({r['UTC'][:10] for r in decam})),(44,14))
        self.assertTrue(rubin[0]['UTC'].startswith('2026-03-04T09:33:14.716'))
        self.assertEqual(sum(r['UTC'][:10]<'2026-06-13' for r in rubin),25)
    def test_native_coordinate_conversion(self):
        first=next(r for r in self.rows if r['station']=='X05')
        independent=SkyCoord('18h19m09.751s','-42d27m15.71s')
        parsed=SkyCoord(first['ra_deg']*u.deg,first['dec_deg']*u.deg)
        self.assertLess(independent.separation(parsed).arcsec,1e-7)
    def test_non_observation_orbit_text_not_consumed(self):
        changed=self.raw+b'\n<pre>Orbit a=999999 e=0.999 target state is not input</pre>\n'
        self.assertEqual(parse(changed),self.rows)
    def test_large_integer_source_ids_and_revisions(self):
        a=171141216913588260
        rows=[{'r:diaSourceId':a,'flux':1},{'r:diaSourceId':a+1,'flux':2}]
        self.assertEqual(len(keyed(rows)),2)
        before=keyed(rows);after=keyed([dict(rows[0],flux=3),rows[1]])
        self.assertNotEqual(before[str(a)],after[str(a)])
        self.assertEqual(before[str(a+1)],after[str(a+1)])
if __name__=='__main__':unittest.main(verbosity=2)
