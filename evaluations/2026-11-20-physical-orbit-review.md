# Physical orbit review verification · November 20, 2026

Runtime: Python 3.12; NumPy 2.3.5, SciPy 1.17.0, Astropy 8.0.3. Exact input hashes and fitter source hash are in the generated results.json.

## Numerical and information-isolation checks

`OPENBLAS_NUM_THREADS=1 python tools/test_physical_orbit_review.py` passed all four tests:

1. Circular-orbit propagation agrees with an analytic solution within 1e-9 AU over the tested -150 to +200 days.
2. Two-body specific energy is conserved to relative 1e-10 in the tested synthetic orbit.
3. Modeled light travel time produces a nonzero, measurable positional correction.
4. A separate synthetic six-parameter bound orbit is recovered from nine training positions; its withheld position is predicted within 0.001 arcsecond. Altering only the held-out observation leaves the fitted state exactly unchanged. This is a numerical fixture, not additional astronomical evidence.

The fitter receives training arrays only. Initialization, selection among converged bound branches and covariance use training data. Actual holdouts are evaluated after selecting the state. Known objects/holdouts were already inspected during project development, so the report explicitly calls these retrospective tests.

## Retained real-data results

- QY297, nine training positions/five dates: November 12 error 0.652117 arcsec; all eight initialization distances converge to the same solution. Conditional formal 95% prediction semiaxes 6.841 × 0.234 arcsec.
- CR7, five training positions/three dates: November 12 error 0.053613 arcsec.
- WV203, five training positions/two dates: November 12 errors 1022.237 and 1022.446 arcsec; November 15 error 1493.072 arcsec. This is a retained failure, not an operational orbit.
- WV203 forward-chain control, seven training positions/three dates: November 15 error 0.538803 arcsec.

The acceptance radius stays 60 arcsec. The chosen error floor stays 0.15 arcsec per coordinate; it is not calibrated by these small tests. No failed initialization was counted as convergence. All trial logs are retained.

The force model is Sun-only. The tests do not certify planetary dynamics, precision ephemerides, global uniqueness, uncertainty coverage, footprint completeness, binary-signal recovery or mass measurement. Full-night ranking of these new fitted tracks has not run in this workspace. The earlier JPL full-night success was supplied by the user and is attributed accordingly.

The benchmark figure was visually inspected for correct labels, the fixed radius and separate successful/failed fits.
