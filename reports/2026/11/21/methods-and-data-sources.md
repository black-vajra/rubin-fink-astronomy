# Methods and data-source follow-up

ED138's discovery paper describes linking direct-image detections, then extending the arc through predicted-position recovery. Its orbit fits use ASSIST/REBOUND and station-specific light time; these are useful references for our planned planetary-force upgrade. Catalog candidates require image checks, static-source comparison and refitting rather than automatic acceptance. The paper lists pointdexter as work in preparation; no installable public implementation was verified here.

ADAM Precovery searches archived detections near an orbit's predicted uncertainty region and checks exposure coverage. Its documented datasets include NSC DR2/DECam, ATLAS, ZTF, SkyMapper, Rubin alerts and published MPC observations. Custom searches require sign-in. Its open-source software does not by itself provide the hosted archive. No authenticated ADAM search was submitted in this session.

Our next application stays within QY297, ED138, WV203 and CR7: compare external-orbit precovery results with the existing published-observation inventory, preserve candidate provenance, and validate useful image cutouts before adding points to independent fits. Use named-target server-side searches and cutouts; no whole-survey download is planned.

Sources:
- https://arxiv.org/html/2610.38693v1
- https://b612.ai/adam-platform/precovery/
- https://github.com/B612-Asteroid-Institute/precovery
- https://prompt-products.lsst.io/products/2026-ED138/index.html
