# Rubin daily journal · November 15, 2026

## Observing run

The Pavilion's 9:00 a.m. EST Fink bright extragalactic report held 354 distinct detections and 120 objects or ungrouped detections, with zero file errors. That's 42 more detections than yesterday's cumulative report. The latest observation was 05:33:18 UTC on November 15.

## PGC 766016 · nucleus brightening

**Observation.** Rubin object 171141216913588260 was around i = 16.6–16.7 through November 11, then 16.52 on November 13 and 16.23 on November 15. Lower magnitudes mean brighter. The measurements came from the science images and can include light from the host galaxy. [Fink light curve](https://lsst.fink-portal.org/171141216913588260)

**Discussion.** The source is near the center of PGC 766016, listed as LSBG F482-095 in WISeREP. It matches AT 2018fcv, classified spectroscopically as an active galactic nucleus at redshift 0.094 in 2018. The November rise covers several observations. We have yet to establish whether its speed or amplitude is unusual for this nucleus. A search on November 15 found no separate public notice about this specific rise. [2018 spectrum and classification](https://www.wiserep.org/object/17480)

**Follow-up goals.**

- Check the next Rubin i-band point to see whether the source continues rising, levels off, or fades.
- Compare with longer same-filter histories where available. Review ZTF g and r histories separately for earlier episodes and independent evidence of activity.
- If the rise continues and stands out against historical variability, consider asking Julien at Fink whether anyone is already following it and whether an independent calibrated image would help.


## Follow-up review · two more Rubin sources

### 313774266976305153 · bright in difference images since late October

**Observation.** Fink returned nine i-band detections. On November 15 at 05:30 UTC the difference-image magnitude was 18.68. Earlier points from October 30 through November 11 ranged from 18.53 to 18.65. The lone November 2025 point was fainter at 20.57. The alert has a Milliquas crossmatch at redshift approximately 0.87. [Fink light curve](https://lsst.fink-portal.org/313774266976305153)

**Discussion.** The latest difference-image point is slightly fainter than the earlier fall points. The source had a stronger difference signal by late October than it did in the lone 2025 observation. The gap leaves the onset and shape of that change unresolved.

**Follow-up goals.**

- Compare the next Rubin i-band difference-flux measurement with the late October and November range. Check whether the signal holds, fades, or rises above that range.
- Look for earlier same-filter measurements, or forced photometry at the source position, to fill in the gap and place the current activity in context.

### 313862200773574662 · brightest i-band science-image point in the retrieved history

**Observation.** On November 15 at 05:33 UTC the science-image magnitude reached i = 18.40, up in brightness from 18.52 on November 13, about 12% more measured light. The previous brightest point was 18.46 on November 5. The November 15 point was the brightest of the 117 usable i-band measurements retrieved from Fink. Its difference-image magnitude of 19.40 was close to earlier November values. [Fink light curve](https://lsst.fink-portal.org/313862200773574662)

**Discussion.** One point marks a new high in the retrieved science-image measurements. The difference-image measurements have stayed near their recent level. These two measurements describe different things: the light measured in the current image and the residual against the reference image.

**Follow-up goals.**

- Check whether the next Rubin i-band science-image measurement stays near 18.40, brightens further, or returns toward 18.5.
- If the brighter level repeats, compare the science and difference fluxes, their uncertainties, and image-quality flags across those visits before describing it as a new episode.

## Solar System follow-up · IRAS–AKARI and known-object recovery

**Status.** The IRAS–AKARI candidate watch is scheduled for Mondays. It checks public sources and alerts us when there are new position measurements, a revised search region, follow-up detections or exclusions, or newly available images that cover the relevant area.

**Discussion.** The original IRAS and AKARI positions are too sparse to pin down a single orbit. An independent observation with a reliable position and time could help narrow the possibilities. On Pots, the known asteroid 2015 XX21 gives us a way to check whether our matching method can recover an object whose path is already known.

**Follow-up goals.**

- On Pots, search the saved Rubin detections near the predicted position and time for 2015 XX21 without using its catalog label. Verify the match against the known alert afterward.
- If the recovery test passes, schedule the known-object check alongside Pots’ existing 9 a.m. Eastern report. The daily check is pending.
- If the IRAS–AKARI watch finds a promising lead, verify the observation date and sky coverage and assess whether it could help constrain the orbit. [IRAS–AKARI candidate paper](https://doi.org/10.1017/pasa.2025.10024)


---

# Rubin daily journal · November 18, 2026

## Bright extragalactic watch · report ran, data did not advance

Pavilion was wiped and reinstalled with SableLinux. The overnight Fink host for now is **Pots**, the Z890 booted into Kubuntu as `pepper`. The HTML report on Pots still says “Pavilion.” Its path, `/home/pepper/rubin-quasar/reports/latest.html`, identifies the machine that generated it.

The Pots timer launched the report at **09:00:58 EST**, and it finished a second later with **60 distinct detections, 42 objects or ungrouped detections, and zero file errors**. The latest observation was **November 15 at 04:20:49.910 UTC**. These counts describe Pots’ dataset. The November 15 journal’s 354 detections came from Pavilion’s earlier setup. A manual attempt using Pots’ `~/rubin-watch` Python failed to import `fastavro`. Pots’ working report and collector use the `~/rubin-live` environment.

The collector restarted after a reboot at **19:44 EST on November 17**. It logged Kafka session and connection timeouts and a DNS resolution failure around **06:20 EST on November 18**. DNS and a TCP probe to Fink port 24499 worked later. The newest saved Avro modification time was still **November 15 at 22:47 EST**, so the November 18 interruption alone cannot explain the older file gap. Fink’s public statistics returned no observing-night entries for November 16–18 as checked this morning. That leaves observing activity and upstream processing on those dates undetermined. [Fink statistics API](https://doc.lsst.fink-broker.org/services/api/statistics/)

We added `fink_extragalactic_lt20mag_candidate_lsst` alongside `fink_uniform_sample_lsst` on Pots and restarted the collector at **10:30:36 EST**. Both topics appeared in the local configuration and the broker returned committed offsets with **zero lag on all ten partitions per topic**. The LSST client’s topic table prints a fixed “NO” in its subscription column. The stream reads the configured topic names. No new Avro file had appeared after the restart at the time of our check. Zero lag verifies the consumer group was at the broker’s reported end at that moment. It leaves fresh delivery and topic-specific provenance unverified. The uniform topic’s roughly 1% sampling is set by Fink. [Topic-list source](https://github.com/astrolabsoftware/fink-client/blob/master/fink_client/scripts/finkctl.py#L276-L290) · [Stream source](https://github.com/astrolabsoftware/fink-client/blob/master/fink_client/scripts/finkctl_stream.py#L100-L105) · [Uniform topic description](https://fastdb.readthedocs.io/en/latest/usage.html#uniform-sample)

**Science triage.** The Pots report offered no new same-filter measurement for PGC 766016 or the two journal follow-ups. Object **170653056044630027** stood out at **r = 17.50** in the difference image on November 15 and has a Milliquas quasar match. The portal screenshot also shows a TNS association, **AT 2019hkw**, and sparse science-image measurements in multiple bands. Compare same-band measurements and review the TNS record before interpreting the bright residual. **PGC 766016** remains the first priority when fresh i-band data arrive. [Fink light curve](https://lsst.fink-portal.org/170653056044630027)

## Moving-object search · known asteroid recovered across three nights

The unfiltered November 15 `diaSource` transfer on Pots, topic `ftransfer_lsst_2026-11-18_944532`, yielded **138,867 records in 1,395 Avro files**, matching the public count. Observation times ran from **00:15:19.899 to 05:33:18.561 UTC**. Date changes in the portal kept returning that same topic. The saved timestamps establish that it was the November 15 batch. It pairs with the existing November 13 and 14 downloads of **76,350** and **59,725** records. [Fink Data Transfer](https://doc.lsst.fink-broker.org/services/data_transfer/)

Earlier controls established that a gap-tolerant within-night search could recover **14/14** near-ecliptic detections with zero unrelated detections mixed in. In the off-ecliptic field near ecliptic latitude **−44.5°**, the selected November 13 three-visit track had a **0.364″** middle residual across **272.6 minutes**. On November 14, ranking the two known visits jointly recovered the true off-ecliptic pair at **rank 1/2**, with a **0.289″** difference between their offset vectors. A nearest-alert rule would have picked the wrong alert in one of the visits.

On November 15, two visits had alerts within **1°** of the field center. Control **21163624428155461** had one detection in the full batch at **05:30:32.245 UTC**, in visit **2026111400396**, giving **3 + 2 + 1 detections** across three nights. Control **21164723755430479** had no catalog-labeled detection in the November 15 batch. For the first control, both straight-line predictions ranked the held-out alert **1st of 55** in the supplied visit. The error fell from **115.11″** using November 13 alone to **36.21″** using November 13–14, a **3.2-fold** improvement. The correct visit was supplied and the catalog ID was checked after ranking. The result validates recovery within that visit. A night-wide blind recovery, false-match rate, orbit fit, and distant-object sensitivity remain to be tested.

## Objectives in order

1. **Verify live delivery on Pots.** On the next published observing night, check that the bright topic’s offsets advance, that new Avro files appear, and that their internal observation times are current. Add the actual host name and current-night alert count or data age to the report so a successful timer run cannot be mistaken for fresh data. Topic provenance would help when both subscriptions share a directory.
2. **Resume the extragalactic follow-ups.** Start with PGC 766016 in i. Then check the two November 15 journal objects in their respective science or difference measurements and inspect the same-band history of 170653056044630027. Record dates, bands, uncertainties and quality flags as available.
3. **Test night-wide moving-object recovery.** Rank November 15 alerts across all visits for the three-night control. Test the second control across all November 14 visits and use time-shifted predictions or comparable control fields to measure accidental matches. Check a slower known object before interpreting sensitivity to distant bodies. Full-night `diaSource` transfers are the working dataset for this stage. Defer a scheduled daily recovery check until the night-wide benchmark works.
4. **Calibrate size and mass estimates after recovery tests.** Use a known body with an independent size or mass, derive a diameter range from calibrated brightness and distance across plausible albedos, then propagate density assumptions into a mass range. A dynamical mass would require measurable gravitational effects, for example a satellite orbit.
5. **Keep the IRAS–AKARI watch and flag credible Planet Nine candidates.** Retain a detection-level record, rule out cataloged movers and image artifacts, fit a plausible distant orbit with uncertainties, and predict a follow-up position before making an identification claim. No Planet Nine candidate was identified in these tests. [IRAS–AKARI candidate paper](https://doi.org/10.1017/pasa.2025.10024)

This is a reasonable list for the present. Live delivery and night-wide validation are the immediate gates. Mass estimation and distant-object inference follow the controls.

## Pots overnight operations · schedule and configuration

The **09:00 Eastern** timer generates the report. The collector is an enabled user service that ran continuously while the Kubuntu user manager was up. The current setup has no demonstrated nightly start/stop window. A 09:00 timer alone does not ensure that the Z890 is booted into Kubuntu, awake, online, or running the user manager overnight. Unattended startup before login has not been verified.

For **November 18–19**, the calculated Cerro Pachón window from sunset to sunrise is approximately **18:20–04:38 EST**. The Sun is below the nautical twilight threshold roughly **19:18–03:40 EST** and astronomical darkness roughly **19:51–03:07 EST**. These are solar planning windows, with actual observing and alert publication dependent on the observatory and broker. The November 15 batch’s observed span was **19:15–00:33 EST** across the preceding local evening and midnight. [Rubin sky almanac and site coordinates](https://obs-ops.lsst.io/Observatory-Control-System/Control-and-Monitoring/Sky-Almanac.html) · [Solar calculation method](https://www.gml.noaa.gov/grad/solcalc/solareqns.PDF)

**For now, boot Kubuntu and have the collector running by 17:00 Eastern, and keep it awake and online through the 09:00 report.** This gives margin around the November window and leaves time for delivery after dawn. Recheck the solar window seasonally. Keep the 09:00 timer. If unattended operation must start before login, verify user lingering first and enable it only if needed. If Kubuntu stays up during the day and Fink must run strictly overnight, add explicit collector start and stop timers. Neither change was applied this morning. Correct the report’s host label at the next edit. Pavilion’s rebuild is deferred while Fink work is confined to Pots.
