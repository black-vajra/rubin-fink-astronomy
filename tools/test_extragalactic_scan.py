"""Checks for selection mistakes that could turn artifacts into discoveries."""
import argparse,contextlib,importlib.util,io,json,sqlite3,tempfile,unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('scan',Path(__file__).with_name('extragalactic_scan.py'))
scan=importlib.util.module_from_spec(spec);spec.loader.exec_module(scan)

class ScanTest(unittest.TestCase):
    def test_full_index_and_false_leads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);db=root/'archive.sqlite3';con=sqlite3.connect(db)
            con.execute('CREATE TABLE sources(sid TEXT PRIMARY KEY,object_id TEXT,band TEXT,visit TEXT,mjd REAL,utc_night TEXT,ra REAL,dec REAL,sso TEXT,science REAL,difference REAL)')
            # IDs deliberately exceed exact IEEE-double integer range.
            variable='313862200773574669';constant='313862200773574670';science_only='313862200773574671';sso='313862200773574672';negative='313862200773574673'
            for oid in [variable,constant,science_only,sso,negative]:
                for i in range(3):
                    diff=[10000,20000,30000][i] if oid in [variable,sso] else [-10000,-20000,-30000][i] if oid==negative else 10000
                    science=100000*(i+1) if oid==science_only else 100000
                    con.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?,?)',(oid+str(i),oid,'i',str(100+i),61300+i,f'2026-09-{i+1:02}',(359.999999+i*.000001)%360,30,'999' if oid==sso else '',science,diff))
            con.commit();con.close()
            a=scan.parser().parse_args(['--database',str(db),'--output',str(root/'out'),'--min-abs-b','0'])
            with contextlib.redirect_stdout(io.StringIO()):scan.run(a)
            r=json.loads((root/'out/results.json').read_text())
            self.assertEqual(r['counts']['all_source_rows_read'],15)
            self.assertEqual({x['object_id'] for x in r['shortlist']},{variable,negative})
            self.assertEqual(r['counts']['known_sso_object_groups'],1)
            self.assertLess(max(x['max_offset_arcsec'] for x in r['shortlist']),.1)
            self.assertIn(variable,(root/'out/shortlist.csv').read_text())

    def test_same_visit_cannot_supply_three_nights(self):
        a=scan.parser().parse_args(['--output','unused','--min-abs-b','0'])
        rows=[dict(sid=str(i),object_id='123',band='i',visit='same',mjd=61300+i/100,utc_night='2026-09-01',ra=10.,dec=20.,science=100000.,difference=10000.+i*10000) for i in range(6)]
        result,reason=scan.assess(rows,a)
        self.assertIsNone(result);self.assertEqual(reason,'too_few_visits')

if __name__=='__main__':unittest.main()
