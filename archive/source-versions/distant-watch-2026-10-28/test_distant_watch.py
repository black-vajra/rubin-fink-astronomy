import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
import numpy as np
import rw_core as core

spec=importlib.util.spec_from_file_location('distant',Path(__file__).with_name('rubin-distant-watch.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def args():
    return types.SimpleNamespace(radii=[50,200,400,900],points=1000,seeds=1500,tolerance=.8)


def synthetic(radius=400,stationary=False,fast=False,one_night=False):
    t=61200+np.arange(12)*(0.005 if one_night else 2)
    e=d.earth_positions(t)
    normal,east,north=d.basis(100,-10)
    speed=.01720209895/radius**1.5
    angle=(t-t.mean())*speed
    h=radius*(np.cos(angle)[:,None]*normal+np.sin(angle)[:,None]*east)
    n=np.tile(normal,(len(t),1)) if stationary else h-e
    n=n/np.linalg.norm(n,axis=1)[:,None]
    ra=np.degrees(np.arctan2(n[:,1],n[:,0]))%360
    dec=np.degrees(np.arcsin(n[:,2]));rows=[]
    for i in range(len(t)):
        raw={'r:diaSourceId':str(1000+i),'r:diaObjectId':str(100000+i),
             'r:ra':float(ra[i]),'r:dec':float(dec[i]),'r:raErr':.03/3600,
             'r:decErr':.03/3600,'r:midpointMjdTai':float(t[i]),'r:band':'r',
             'r:psfFlux':300,'r:psfFluxErr':10,'r:scienceFlux':1000,
             'r:scienceFluxErr':10,'r:visit':str(10000+i),'r:ssObjectId':0,
             'r:forced_PsfFlux_flag':False}
        raw.update({'r:'+flag:False for flag in core.FLAGS})
        rows.append(core.normalize(raw))
    return rows


FIELD={'label':'synthetic-only','ra':100,'dec':-10,'radius':600}


class LinkTests(unittest.TestCase):
    def test_recovers_cross_id_distant_body(self):
        rows=synthetic();found,stats=d.link_band(rows,FIELD,args())
        self.assertTrue(found)
        good=[t for t in found if t['trial_radius_au']==400]
        self.assertTrue(good)
        self.assertEqual(good[0]['independent_visits'],12)
        self.assertEqual(len(good[0]['object_ids']),12)
        self.assertLess(good[0]['reduced_chi2'],1)

    def test_stationary_sky_rejected(self):
        found,_=d.link_band(synthetic(stationary=True),FIELD,args())
        self.assertEqual(found,[])

    def test_nearby_fast_body_rejected(self):
        found,_=d.link_band(synthetic(radius=10),FIELD,args())
        self.assertEqual(found,[])

    def test_one_night_insufficient(self):
        found,_=d.link_band(synthetic(one_night=True),FIELD,args())
        self.assertEqual(found,[])

    def test_same_exposure_not_independent(self):
        rows=synthetic()
        for r in rows:r['visit']='one-visit'
        found,_=d.link_band(rows,FIELD,args())
        self.assertEqual(found,[])

    def test_quality_and_known_sso(self):
        r=synthetic()[0];self.assertTrue(d.eligible(r))
        r['known_sso']=True;self.assertFalse(d.eligible(r))
        r['known_sso']=False;r['usable']=False;self.assertFalse(d.eligible(r))
        r['usable']=True;r['psfFlux']=-300;self.assertFalse(d.eligible(r))

    def test_deparallax_inverse_geometry(self):
        rows=synthetic();t=np.array([r['midpointMjdTai'] for r in rows])
        n=d.vectors([r['ra'] for r in rows],[r['dec'] for r in rows])
        xy,delta=d.deparallax(n,d.earth_positions(t),400,d.basis(100,-10))
        self.assertTrue(np.all(delta>398))
        self.assertLess(np.ptp(xy[:,1]),1e-5)

    def test_grid_duplicates_and_size_assumptions(self):
        found,_=d.link_band(synthetic(),FIELD,args());merged=d.merge_tracks(found)
        self.assertEqual(len(merged),1)
        t=merged[0];self.assertTrue(t['deep_trial_compatible'])
        self.assertGreaterEqual(len(t['compatible_trials']),1)
        self.assertIn('not a measured size',t['size_scenario']['status'])
        self.assertGreater(t['size_scenario']['diameter_km_if_albedo_004'],t['size_scenario']['diameter_km_if_albedo_060'])

    def test_budget_is_explicit(self):
        a=args();a.points=6
        _,stats=d.link_band(synthetic(),FIELD,a)
        self.assertTrue(stats['point_limit_hit'])

    def test_reflected_light_scenario_units(self):
        radius,delta,diameter,albedo=400.,399.,12742.,.60
        ratio=albedo*(diameter/(2*d.AU_KM))**2/(radius**2*delta**2)
        magnitude=-26.93-2.5*np.log10(ratio)
        flux=10**((31.4-magnitude)/2.5)
        rows=synthetic()
        for r in rows:r['scienceFlux']=float(flux);r['scienceFluxErr']=float(flux/10)
        scenario=d.size_scenario(dict(band='r',rows=rows,trial_radius_au=radius,trial_geocentric_distance_au=delta))
        self.assertAlmostEqual(scenario['diameter_km_if_albedo_060'],diameter,delta=1)

    def test_catalog_errors_never_become_no_match(self):
        bad=b'<VOTABLE><INFO name="QUERY_STATUS" value="ERROR">Unavailable</INFO></VOTABLE>'
        self.assertEqual(d.parse_skybot(bad,0,0)['status'],'unchecked')
        empty=b'<VOTABLE><INFO name="QUERY_STATUS" value="ERROR">No solar system object was found in the requested FOV</INFO></VOTABLE>'
        self.assertEqual(d.parse_skybot(empty,0,0)['status'],'no_catalog_match')

    def test_persistent_evidence_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);db=core.connect(root/'rubin-distant.sqlite3');d.schema(db)
            found,stats=d.link_band(synthetic(),FIELD,args());tracks=d.merge_tracks(found)
            d.persist(db,tracks)
            count=db.execute('SELECT count(*) FROM dw_audit').fetchone()[0]
            d.persist(db,tracks)
            self.assertEqual(db.execute('SELECT count(*) FROM dw_audit').fetchone()[0],count)
            d.report(db,types.SimpleNamespace(data_dir=root),tracks,[stats])
            self.assertTrue((root/'reports'/'latest.html').exists())
            d.persist(db,[])
            self.assertEqual(db.execute('SELECT status FROM dw_tracks').fetchone()[0],'not_reproduced')
            db.close()


if __name__=='__main__':unittest.main()
