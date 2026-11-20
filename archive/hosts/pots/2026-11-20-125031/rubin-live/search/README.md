# Rubin live-alert distant-object search for Pots

Use the existing ~/rubin-live/venv, which includes Fink, fastavro, Astropy,
NumPy, and matplotlib. This release analyzes Avro files saved with finkctl.
It does not open a second Kafka consumer or reset offsets.

After extraction into ~/rubin-live/search, run:

    cd ~/rubin-live/search
    bash rubin-live-search.sh --fields pots-smoke-field.json --avro ../alerts/smoke-test ../alerts/association-test

This imports the current diaSource in each packet, deduplicates by diaSourceId,
and stores the results separately in ~/rubin-live/distant-search. Known Solar
System associations are kept in SQLite but excluded from unknown-body linking.
Existing diaObject associations are retained, and the search can link across
diaObject IDs. Embedded detection histories are excluded from this release.
Keep the original Avro files for audit and reprocessing.

Open ~/rubin-live/distant-search/reports/latest.html in a browser. The JSON
report records import counts, search budgets, and the configured footprint.

The included field is centered on the known-object control packet for a smoke
test. Supply a different JSON field list for scientific runs. Each entry uses
label, ra (degrees), dec (degrees), and radius_arcsec. The inherited linker
analyzes the field plus a half-degree buffer, with one filter at a time and
at least six distinct visits across four nights spanning at least seven days.
It tests trial heliocentric radii from 50 to 2500 AU by default. A planet-scale
size scenario depends on the assumed distance and albedo and requires usable
r-band photometry. The report lists hypotheses for review.

The 1% stream and smoke-test field establish the ingestion path. For search
validation use a denser archived sample of repeatedly observed fields and
include known-object controls.
