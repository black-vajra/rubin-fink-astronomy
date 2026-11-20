"""Import current LSST Avro detections into the distant-watch database."""
import json

import rw_core as core


def normalize_alert(alert):
    source = alert.get('diaSource')
    if not isinstance(source, dict):
        raise ValueError('missing diaSource')
    measurement = core.normalize({f'r:{key}': value for key, value in source.items()})
    if measurement['sid'] == '0':
        raise ValueError('zero diaSourceId')
    packet_id = alert.get('diaSourceId')
    if packet_id is not None and core.ident(packet_id) != measurement['sid']:
        raise ValueError('packet and source IDs differ')
    solar = alert.get('ssSource') or {}
    designation = str(solar.get('designation') or '').strip()
    solar_id = solar.get('ssObjectId')
    measurement['known_sso'] |= bool(designation) or solar_id not in (None, 0, '0', -1, '-1', '')
    measurement['designation'] = designation or None
    measurement['processed_mjd_tai'] = core.num(source.get('timeProcessedMjdTai'))
    return measurement


def ingest(db, inputs):
    from fastavro import reader

    files = set()
    for path in inputs:
        path = path.expanduser()
        if path.is_dir():
            files.update(file.resolve() for file in path.glob('*.avro') if file.is_file())
        elif path.is_file():
            files.add(path.resolve())
        else:
            raise FileNotFoundError(path)
    if not files:
        raise ValueError('No Avro packets found in the supplied paths')

    counts = dict(files=len(files), packets=0, known_sso=0, unassociated=0,
                  inserted=0, updated=0, unchanged=0, errors=[])
    for path in sorted(files):
        file_counts = {key: 0 for key in ('packets', 'known_sso', 'unassociated',
                                         'inserted', 'updated', 'unchanged')}
        try:
            with db, path.open('rb') as stream:
                for alert in reader(stream):
                    measurement = normalize_alert(alert)
                    file_counts['packets'] += 1
                    category = 'known_sso' if measurement['known_sso'] else 'unassociated'
                    file_counts[category] += 1
                    saved = db.execute(
                        'SELECT normalized FROM rw_measurements WHERE sid=?',
                        (measurement['sid'],)).fetchone()
                    if saved:
                        previous = json.loads(saved[0])
                        old_time = previous.get('processed_mjd_tai') or 0
                        new_time = measurement['processed_mjd_tai'] or 0
                        if new_time <= old_time:
                            file_counts['unchanged'] += 1
                            continue
                    core.save_normal(db, measurement)
                    file_counts['updated' if saved else 'inserted'] += 1
        except (ValueError, TypeError, AttributeError, OSError, EOFError) as exc:
            counts['errors'].append(f'{path.name}: {exc}')
            continue
        for key, value in file_counts.items():
            counts[key] += value
    return counts
