#!/usr/bin/env python3
"""Numerical and information-isolation checks for the exploratory orbit fitter."""
import json
from pathlib import Path
import unittest
import numpy as np
from astropy.time import Time
import physical_orbit_review as m

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/'reports/2026/11/20/physical-orbit-watchlist/inputs'

class OrbitChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = sorted(json.loads((INPUT/'2001_QY297-sources.json').read_text()),
                      key=lambda r:r['r:midpointMjdTai'])
        jd = Time([r['r:midpointMjdTai'] for r in rows], format='mjd', scale='tai').tdb.jd
        cls.dt = jd-jd[0]
        cls.observer = -m.vectors(INPUT/'2001_QY297-sun-from-observer.json',jd,'X05@399')[:,:3]
        cls.sv = m.vectors(INPUT/'2001_QY297-sun-barycentric.json',jd,'500@0')[:,3:]
        cls.state = np.array([35.,-12.,-7., .0007,.0023,.0004])
        cls.n = m.predict(cls.state, cls.dt, cls.observer, cls.sv)
        ra = np.arctan2(cls.n[:,1],cls.n[:,0])
        cls.east = np.c_[-np.sin(ra),np.cos(ra),np.zeros(len(ra))]
        cls.north = np.cross(cls.n,cls.east)

    def test_two_body_energy_conservation(self):
        states=m.propagate(self.state,np.array([-150.,0.,200.]))
        energies=np.sum(states[:,3:]**2,axis=1)/2-m.MU/np.linalg.norm(states[:,:3],axis=1)
        self.assertLess(np.ptp(energies)/abs(energies[1]),1e-10)

    def test_light_time_has_nonzero_effect(self):
        geometric=m.propagate(self.state,self.dt)[:,:3]-self.observer
        geometric/=np.linalg.norm(geometric,axis=1)[:,None]
        errors=np.arctan2(np.linalg.norm(np.cross(geometric,self.n),axis=1),np.sum(geometric*self.n,axis=1))*m.ARC
        self.assertGreater(np.min(errors),.1)

    def test_circular_orbit_against_analytic_solution(self):
        radius=3.
        frequency=np.sqrt(m.MU/radius**3)
        dt=np.array([-150.,0.,200.])
        state=np.array([radius,0.,0.,0.,radius*frequency,0.])
        numerical=m.propagate(state,dt)[:,:3]
        analytic=np.c_[radius*np.cos(frequency*dt),radius*np.sin(frequency*dt),np.zeros(len(dt))]
        self.assertLess(np.max(np.linalg.norm(numerical-analytic,axis=1)),1e-9)

    def test_synthetic_training_only_recovery_and_holdout_isolation(self):
        old=m.SEEDS
        try:
            m.SEEDS=[5,40]
            fit,trials=m.fit_training(self.dt[:-1],self.observer[:-1],self.sv[:-1],
                                      self.n[:-1],self.east[:-1],self.north[:-1])
            self.assertIsNotNone(fit)
            pr=m.predict(fit,self.dt[-1:],self.observer[-1:],self.sv[-1:])
            miss=np.linalg.norm(np.cross(pr[0],self.n[-1]))*m.ARC
            self.assertLess(miss,.001)
            self.assertLess(np.linalg.norm(fit-self.state),1e-4)
            # Alter only the held-out observation by a large angle: training arrays are identical.
            changed=self.n.copy();changed[-1]=[1,0,0]
            again,_=m.fit_training(self.dt[:-1],self.observer[:-1],self.sv[:-1],
                                   changed[:-1],self.east[:-1],self.north[:-1])
            np.testing.assert_array_equal(fit,again)
        finally:
            m.SEEDS=old

if __name__=='__main__':
    unittest.main(verbosity=2)
