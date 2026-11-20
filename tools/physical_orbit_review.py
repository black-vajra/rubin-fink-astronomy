#!/usr/bin/env python3
"""Training-only, restricted-watchlist two-body orbit fits and retrospective tests.

Offline: uses retained Sun/observer geometry, never the targets' published states.
This is an exploratory astrometric orbit fitter, not a precision ephemeris service.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html import escape
import io
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from astropy.time import Time

MU = 1.32712440041279419e20 * 86400**2 / 149597870700**3
C = 299792458 * 86400 / 149597870700
ARC = 206264.80624709636
SIGMA = .15  # Assumed per-coordinate astrometric floor, not estimated from the test.
RADIUS = 60.0  # Project radius established before the present scoring.
SEEDS = [2, 3, 5, 10, 20, 40, 80, 160]  # Topocentric trial distances in AU.
ALLOWED = ['2001 QY297', '2014 WV203', '2013 CR7', '2026 ED138']


def propagate(state, dt):
    dt = np.asarray(dt)
    calls = 0
    def rhs(t, x):
        nonlocal calls
        calls += 1
        r = x[:3]
        distance = np.linalg.norm(r)
        if calls > 4000 or distance < .05:
            raise ValueError('Integration budget/domain exceeded')
        return np.r_[x[3:], -MU * r / distance**3]
    output = np.empty((len(dt), 6))
    for sign, mask in [(1, dt >= 0), (-1, dt < 0)]:
        if not np.any(mask):
            continue
        stop = float(np.max(dt[mask]) if sign == 1 else np.min(dt[mask]))
        if stop == 0:
            output[mask] = state
            continue
        sol = solve_ivp(rhs, [0, stop], state, method='DOP853',
                        rtol=2e-12, atol=2e-14, dense_output=True)
        if not sol.success:
            raise ValueError(sol.message)
        output[mask] = sol.sol(dt[mask]).T
    return output


def predict(state, dt, observer_helio, sun_bary_velocity):
    """Astrometric ICRF unit vectors at reception, iterating down-leg light time.

    Sun displacement during light time is linearized from its DE441 barycentric
    velocity. The integrated target follows a heliocentric Sun-only orbit.
    """
    emission_dt = dt.copy()
    for _ in range(4):
        target = propagate(state, emission_dt)[:, :3]
        los = target - observer_helio + sun_bary_velocity * (emission_dt - dt)[:, None]
        emission_dt = dt - np.linalg.norm(los, axis=1) / C
    return los / np.linalg.norm(los, axis=1)[:, None]


def directions(rows):
    ra = np.radians([r['r:ra'] for r in rows])
    dec = np.radians([r['r:dec'] for r in rows])
    unit = np.c_[np.cos(ra)*np.cos(dec), np.sin(ra)*np.cos(dec), np.sin(dec)]
    east = np.c_[-np.sin(ra), np.cos(ra), np.zeros(len(ra))]
    return unit, east, np.cross(unit, east)


def offsets(predicted, observed, east, north):
    d = predicted-observed
    return np.c_[np.sum(d*east, axis=1), np.sum(d*north, axis=1)] * ARC


def vectors(path, epochs, center):
    record = json.loads(path.read_text())
    p = record['parameters']
    required = {'COMMAND': "'10'", 'CENTER': repr(center), 'TIME_TYPE': "'TDB'",
                'EPHEM_TYPE': "'VECTORS'", 'REF_PLANE': "'FRAME'",
                'REF_SYSTEM': "'ICRF'", 'VEC_CORR': "'NONE'", 'OUT_UNITS': "'AU-D'"}
    if any(p.get(k) != v for k, v in required.items()):
        raise ValueError(f'Unexpected Sun/observer geometry settings: {path}')
    body = record['response']['result'].split('$$SOE')[1].split('$$EOE')[0]
    data = np.array([[float(r[0]), *map(float, r[2:8])]
                     for r in csv.reader(io.StringIO(body)) if r and r[0].strip()])
    if len(data) != len(epochs) or np.max(np.abs(data[:, 0]-epochs))*86400 > .001:
        raise ValueError('Geometry epochs differ from source epochs')
    return data[:, 1:]


def elements(state):
    r, v = state[:3], state[3:]
    radius = np.linalg.norm(r)
    energy = np.dot(v, v)/2-MU/radius
    a = -MU/(2*energy)
    h = np.cross(r, v)
    e = np.linalg.norm(np.cross(v, h)/MU-r/radius)
    return {'heliocentric_distance_AU_at_reference': float(radius),
            'a_AU': float(a), 'e': float(e), 'bound': bool(energy < 0),
            'period_years': float(np.sqrt(a**3)) if a > 0 else None}


def fit_training(dt, observer, sunvel, observed, east, north):
    """Receives training arrays only; model selection uses training cost only."""
    trials = []
    for rho in SEEDS:
        started = time.monotonic()
        def residual(state):
            if time.monotonic()-started > 8:
                raise TimeoutError('8-second initialization budget exceeded')
            pr = predict(state, dt, observer, sunvel)
            return (offsets(pr, observed, east, north)/SIGMA).ravel()
        coefficient = np.polyfit(dt, observer+rho*observed, 1)
        v = coefficient[0]
        state0 = np.r_[coefficient[1]+v*rho/C, v]
        try:
            fit = least_squares(residual, state0, jac='3-point',
                                x_scale=np.r_[np.ones(3)*40, np.ones(3)*.005],
                                max_nfev=100, ftol=1e-10, xtol=1e-11, gtol=1e-8)
            trials.append({'seed_range_AU': rho, 'converged': bool(fit.success),
                           'training_chi2': float(2*fit.cost), 'state': fit.x.tolist(),
                           'nfev': fit.nfev, 'message': str(fit.message),
                           'bound': elements(fit.x)['bound']})
        except (ValueError, TimeoutError, FloatingPointError) as exc:
            trials.append({'seed_range_AU': rho, 'converged': False, 'error': str(exc)})
    candidates = [r for r in trials if r['converged'] and r['bound']]
    if not candidates:
        return None, trials
    chosen = min(candidates, key=lambda x: x['training_chi2'])
    return np.array(chosen['state']), trials


def tangent_jacobian(state, dt, observer, sv, observed, east, north):
    columns = []
    for i, step in enumerate([1e-6]*3+[1e-8]*3):
        delta = np.zeros(6)
        delta[i] = step
        plus = offsets(predict(state+delta, dt, observer, sv), observed, east, north)
        minus = offsets(predict(state-delta, dt, observer, sv), observed, east, north)
        columns.append((plus-minus)/(2*step))
    return np.stack(columns, axis=-1)


def review(name, inputs, cutoff="2026-11-12"):
    key = name.replace(' ', '_')
    rows = sorted(json.loads((inputs/f'{key}-sources.json').read_text()),
                  key=lambda r: r['r:midpointMjdTai'])
    if len({str(r['r:diaSourceId']) for r in rows}) != len(rows):
        raise ValueError('Duplicate source IDs')
    tai = Time([r['r:midpointMjdTai'] for r in rows], format='mjd', scale='tai')
    jd = tai.tdb.jd
    dt = jd-jd[0]
    times = tai.utc.isot
    train = np.array([i for i, s in enumerate(times) if s[:10] < cutoff])
    test = np.array([i for i, s in enumerate(times) if s[:10] >= cutoff])
    n, east, north = directions(rows)
    observer = -vectors(inputs/f'{key}-sun-from-observer.json', jd, 'X05@399')[:, :3]
    sv = vectors(inputs/f'{key}-sun-barycentric.json', jd, '500@0')[:, 3:]
    print(f'{name}: fitting {len(train)} earlier positions; withholding {len(test)}.', flush=True)
    state, trials = fit_training(dt[train], observer[train], sv[train], n[train], east[train], north[train])
    result = {'name': name, 'test_cutoff_UTC': cutoff, 'reference_TDB_JD': float(jd[0]), 'sigma_arcsec_per_coordinate': SIGMA,
              'trial_distances_AU': SEEDS, 'trials': trials,
              'training_ids': [str(rows[i]['r:diaSourceId']) for i in train],
              'withheld_ids': [str(rows[i]['r:diaSourceId']) for i in test],
              'training_dates_UTC': sorted({times[i][:10] for i in train}),
              'training_span_days': float(np.ptp(dt[train])),
              'test_used_for_optimizer_or_model_selection': False}
    if state is None:
        result['status'] = 'No converged bound solution under the stated initialization budget'
        return result
    pr = predict(state, dt, observer, sv)
    residuals = offsets(pr, n, east, north)
    misses = np.arctan2(np.linalg.norm(np.cross(pr, n), axis=1), np.sum(pr*n, axis=1))*ARC
    jac = tangent_jacobian(state, dt, observer, sv, n, east, north)
    weighted = jac[train].reshape(-1, 6)/SIGMA
    _, singular, vt = np.linalg.svd(weighted, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0]*1e-10))
    covariance = vt.T @ np.diag(singular**-2) @ vt if rank == 6 else None
    result.update(status='Exploratory bound fit; held-out evaluation below', state=state.tolist(),
                  elements=elements(state), training_chi2=float(np.sum((residuals[train]/SIGMA)**2)),
                  training_dof=int(2*len(train)-6), training_max_error_arcsec=float(misses[train].max()),
                  local_jacobian_rank=rank, covariance_state=None if covariance is None else covariance.tolist(),
                  covariance_note='Conditional local linearization for independent 0.15 arcsec coordinate errors; '
                                  'not rescaled down by small training chi-square; excludes model/photocenter '
                                  'systematics and alternative orbit branches.', withheld=[])
    for i in test:
        pc = jac[i] @ covariance @ jac[i].T if covariance is not None else None
        w = {'sid': str(rows[i]['r:diaSourceId']), 'visit': str(rows[i]['r:visit']),
             'UTC': str(times[i]), 'east_error_arcsec': float(residuals[i, 0]),
             'north_error_arcsec': float(residuals[i, 1]), 'error_arcsec': float(misses[i]),
             'fixed_radius_arcsec': RADIUS, 'inside_fixed_radius': bool(misses[i] <= RADIUS),
             'predicted_ra_deg': float(np.degrees(np.arctan2(pr[i, 1], pr[i, 0])) % 360),
             'predicted_dec_deg': float(np.degrees(np.arcsin(pr[i, 2])))}
        if pc is not None:
            eigenvalues = np.maximum(np.linalg.eigvalsh(pc), 0)
            w['formal_prediction_95pct_semiaxes_arcsec'] = np.sqrt(eigenvalues[::-1]*5.991464547).tolist()
            combined = pc+SIGMA**2*np.eye(2)
            w['formal_combined_mahalanobis_sigma'] = float(np.sqrt(residuals[i] @ np.linalg.inv(combined) @ residuals[i]))
            w['formal_position_covariance_arcsec2'] = pc.tolist()
        result['withheld'].append(w)
    if name == '2001 QY297' and covariance is not None:
        rng = np.random.default_rng(20261120)
        draws = rng.multivariate_normal(state, covariance, size=512, method='svd')
        es = [elements(s) for s in draws]
        bound = [e for e in es if e['bound']]
        result['local_Gaussian_draws'] = {'draws': 512, 'bound_draws': len(bound),
            'note': 'Illustrative 16/50/84 percentiles of local state-Gaussian draws, conditional on bound draws. '
                    'Not a global posterior, confidence interval, size estimate or mass measurement.',
            'bound_percentiles': {k: np.percentile([e[k] for e in bound], [16, 50, 84]).tolist()
                                  for k in ['a_AU', 'e', 'heliocentric_distance_AU_at_reference']}}
    print(name, 'withheld misses', [round(w['error_arcsec'], 3) for w in result['withheld']], flush=True)
    return result


def write_report(results, out, inputs):
    generated = datetime.now(timezone.utc).isoformat(timespec='seconds')
    payload = {'generated_UTC': generated, 'model': 'Newtonian heliocentric Sun-only test particle',
               'watchlist': ALLOWED, 'results': results,
               'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs.glob('*.json'))},
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(payload, indent=2)+'\n')
    lines = ['# Restricted moving-object watchlist · physical orbit benchmark', '', f'Generated {generated}.', '',
        '## Daily research scope', '',
        '| Object | Role |', '|---|---|',
        '| 2001 QY297 | Primary distant binary; orbit prediction and external binary-mass benchmark |',
        '| 2014 WV203 | Apparent-slow-motion and orbit-ambiguity control |',
        '| 2013 CR7 | Independent apparent-slow-motion comparison control |',
        '| 2026 ED138 | Priority target awaiting usable public astrometry; no fit in this run |', '',
        'No other moving objects were queried or fitted. Existing broad candidate lists remain historical evidence. '
        'Daily research means checking for new usable data; it does not require a fresh observation every night.', '',
        '## Method fixed for these fits', '',
        '- Six Cartesian heliocentric state parameters, optimized using positions strictly earlier than each stated test cutoff (November 12; also November 15 for the WV203 forward-chain control).',
        '- Newtonian solar gravity; ICRF axes; TAI source times converted to TDB for dynamics and UTC for reporting.',
        '- Rubin observer position from retained geometric DE441 Sun-from-X05 vectors; Earth/site motion therefore included.',
        '- Four iterations of light-travel time; Sun barycentric displacement during light time linearized using its retained velocity.',
        '- No target JPL/SBDB state, elements, distance, mass or target ephemeris enters initialization, objective or model selection.',
        '- Trial topocentric distances: 2, 3, 5, 10, 20, 40, 80, 160 AU. Lowest training chi-square among converged bound fits selected.',
        '- At most 100 optimizer evaluations and eight seconds per initialization. Failed/incomplete trials are retained, not counted as convergence.',
        '- Uniform assumed 0.15 arcsec errors per tangent coordinate; fixed project radius 60 arcsec. Neither tuned to held-out residuals.',
        '- Local covariance is conditional on this model/error assumption; no shrinkage by a small reduced training chi-square.', '',
        'These are **retrospective withheld-in-fit tests** of known labeled objects, whose later detections were already known. '
        'They are not a prospective blind discovery experiment. No outliers were removed and no holdout positions entered fitting.', '',
        '## Withheld results', '',
        '| Object | Training points / dates | Withheld UTC | Miss (arcsec) | Inside 60 arcsec? | Formal 95% prediction ellipse semiaxes (arcsec) |',
        '|---|---|---|---:|---|---|']
    for r in results:
        for w in r.get('withheld', []):
            axes = w.get('formal_prediction_95pct_semiaxes_arcsec')
            axes_text = 'unavailable' if axes is None else f'{axes[0]:.3f} × {axes[1]:.3f}'
            lines.append(f"| {r['name']} | {len(r['training_ids'])} / {len(r['training_dates_UTC'])} | {w['UTC']} | {w['error_arcsec']:.3f} | {w['inside_fixed_radius']} | {axes_text} |")
    lines += ['', 'Formal ellipses describe fitted position uncertainty only, under the stated 0.15 arcsec assumption. '
              'They omit systematic model errors and alternative branches; inclusion in a very large ellipse is not evidence of a useful orbit. '
              'The fixed 60 arcsec search gate is evaluated separately.', '']
    for r in results:
        good = [t for t in r['trials'] if t.get('converged') and t.get('bound')]
        lines += [f"## {r['name']} · cutoff {r['test_cutoff_UTC']}", '',
                  f"Training dates: {', '.join(r['training_dates_UTC'])}; span {r['training_span_days']:.3f} days. "
                  f"Converged bound initializations: {len(good)}/{len(SEEDS)}.", '']
        if 'state' not in r:
            lines += [r['status'], '']
            continue
        el = r['elements']
        lines += [f"Training maximum position residual: **{r['training_max_error_arcsec']:.4f} arcsec**; "
                  f"chi-square **{r['training_chi2']:.4f}** for **{r['training_dof']}** nominal degrees of freedom.", '',
                  f"Sun-only osculating fit at JD {r['reference_TDB_JD']:.9f} TDB: "
                  f"heliocentric distance **{el['heliocentric_distance_AU_at_reference']:.4f} AU**, "
                  f"semimajor axis **{el['a_AU']:.4f} AU**, eccentricity **{el['e']:.4f}**. "
                  'These are exploratory fit outputs, not catalog-grade replacement elements.', '']
        if r['name'] == '2001 QY297':
            lines += ['The November 12 prediction improves from the earlier October-30 linear diagnostic (128.766 arcsec) '
                      'to the physical-fit result above. A successful position prediction does **not** establish a precise full orbit. '
                      'The covariance and orbit-element spread show remaining distance/velocity degeneracy.', '',
                      'Illustrative 16th / 50th / 84th percentiles from 512 local Gaussian state draws, conditional on bound draws:', '',
                      '| Parameter | 16th | 50th | 84th |', '|---|---:|---:|---:|']
            for k, v in r['local_Gaussian_draws']['bound_percentiles'].items():
                lines.append(f'| {k} | {v[0]:.4f} | {v[1]:.4f} | {v[2]:.4f} |')
            lines += ['', f"Bound draws: {r['local_Gaussian_draws']['bound_draws']}/512. "
                      'These are local, assumption-dependent diagnostic spreads, not a validated global posterior.', '']
        if len(r['training_dates_UTC']) < 3:
            lines += ['**Insufficient date diversity for a trustworthy unique orbit:** a tiny training residual can coexist '
                      'with a wrong future track. Do not promote this fit to an operational prediction.', '']
        lines += ['Every initialization, including failed and non-converged trials, is retained in results.json.', '']
    lines += ['## Confirmed earlier full-night QY297 recovery', '',
        'The user supplied the completed Pots report generated 2026-11-20T16:55:37Z: external JPL predictions scored '
        '235,039 indexed November 12 alerts in 145 visits; QY297 ranked first, miss 0.0940 arcsec, with one detection '
        'inside 60 arcsec and no differently labeled/unassociated competitor inside. This corrects the previous pending status.', '',
        '**That full-night result uses the external JPL orbit.** This report scores the independently fitted physical '
        'prediction against withheld catalog detections only. A full-night all-alert ranking of this new fitted orbit '
        'has not run here. Neither result supplies usable-footprint false-match calibration.', '',
        '## Binary research and thesis potential', '',
        'QY297 is a published binary with a literature system mass (4.105 ± 0.038) × 10^18 kg from its resolved '
        'mutual orbit (Grundy et al. 2011, Table 8). The present fit concerns its motion around the Sun; it does not '
        'fit the components\' 138-day mutual orbit, recover their individual masses or improve the published system mass.', '',
        'A thesis would need a demonstrably new contribution. A bounded possible question is whether Rubin-era '
        'unresolved astrometry/photometry can constrain QY297\'s photocenter motion or binary variability, cross-validated '
        'against resolved observations and comparison objects. That is a proposed research direction, not a feasibility '
        'result. Ten sparse alert positions do not establish such a signal or a thesis-sized discovery.', '',
        'Feasibility gates: current literature/archival resolved-data audit; actual seeing/SNR/cutout and forced-photometry '
        'coverage; expected binary signal versus calibration/centroid systematics; identifiable parameters and simulated '
        'recovery; access to additional observations and appropriate academic supervision if pursued as a degree.', '',
        '## Remaining work, confined to the watchlist', '',
        '1. Add planetary perturbations and perform global orbit-ambiguity/uncertainty checks before claiming precision ephemerides.',
        '2. Expand withheld date coverage for these same targets. WV203 needs more independent training dates; ED138 needs usable public astrometry.',
        '3. Validate with an established orbit-fitting implementation and new measurements not examined during development.',
        '4. Obtain actual usable detector footprints and masks for controlled matching and sensitivity estimates.',
        '5. Assess QY297 binary-signal feasibility before extending to a mutual-orbit or physical-size/mass analysis.', '',
        '## Limitations', '',
        'The force model omits planets, solar reflex acceleration in heliocentric dynamics, relativity, resolved mutual motion, '
        'astrometric correlations and image-level biases. The linearized Sun displacement during light time is approximate. '
        'The eight initialization distances do not exhaust all orbit branches, especially for two-date arcs. '
        'Formal covariance assumes the selected branch and is not proof of uniqueness. Results do not establish an unknown-body discovery or Planet Nine.', '',
        '## Provenance', '',
        'Source IDs, input hashes, state, all trials, withheld predictions and covariances are in results.json. '
        'Original source responses and exact observer-geometry request parameters are retained in inputs/. '
        'All input times were matched against geometry epochs to within 0.001 second.', '',
        '- Fink SSO API: https://api.lsst.fink-portal.org/api/v1/sso',
        '- JPL Horizons observer/frame/time definitions: https://ssd.jpl.nasa.gov/horizons/manual.html',
        '- JPL constants: https://ssd.jpl.nasa.gov/astro_par.html',
        '- Grundy et al. 2011: https://arxiv.org/abs/1103.2751',
        '- Thirouin et al. 2012, prior QY297 variability research: https://academic.oup.com/mnras/article/424/4/3156/1062105', '']
    md = '\n'.join(lines)
    (out/'report.md').write_text(md)
    (out/'report.html').write_text('<!doctype html><meta charset=utf-8><title>Physical orbit benchmark</title>'
        '<pre style="white-space:pre-wrap;max-width:1100px;margin:2em auto;font:16px/1.5 system-ui">'+escape(md)+'</pre>')
    print(f'Report: {out / "report.html"}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = [review(name, args.data_dir/'inputs') for name in ALLOWED if name != '2026 ED138']
    result.append(review('2014 WV203', args.data_dir/'inputs', cutoff='2026-11-15'))
    write_report(result, args.output, args.data_dir/'inputs')


if __name__ == '__main__':
    main()
