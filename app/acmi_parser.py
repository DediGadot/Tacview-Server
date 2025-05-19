import re
from collections import defaultdict, Counter

"""Basic parser for Tacview ACMI files.

This parser extracts pilot and formation information as well as common
events such as shots, hits, kills and crashes.

It is not a complete implementation of the TACVIEW specification, but it
handles typical key/value pairs used by DCS World ACMI exports.
"""

# Regular expression to parse key=value pairs (value may be quoted)
KEY_VALUE_RE = re.compile(r"(?P<key>[^=]+)=(?P<value>.*)")


def _parse_line(line):
    """Parse a single comma separated line.

    Returns a tuple of (object id, {key: value}). Values are stripped of
    surrounding quotes.
    """

    parts = line.split(',')
    obj_id = parts[0]
    data = {}
    for part in parts[1:]:
        match = KEY_VALUE_RE.match(part)
        if match:
            key = match.group('key').strip()
            value = match.group('value').strip().strip('"')
            data[key] = value
    return obj_id, data


def _ensure_stats():
    """Return a Counter pre-populated with common event keys."""

    return Counter({
        'Shots': 0,
        'Hits': 0,
        'Kills': 0,
        'Deaths': 0,
        'Takeoffs': 0,
        'Landings': 0,
    })


def parse_acmi(content):
    """Parse an ACMI file content and compute statistics.

    Parameters
    ----------
    content : str
        Raw text of the ACMI file.

    Returns
    -------
    dict
        Dictionary with per pilot and per formation statistics.
    """

    metadata = {}
    objects = defaultdict(dict)
    pilot_stats = defaultdict(_ensure_stats)
    formation_stats = defaultdict(_ensure_stats)

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Header lines such as FileType=text/acmi/tacview
        if ',' not in line:
            if '=' in line:
                key, _, value = line.partition('=')
                metadata[key.strip()] = value.strip().strip('"')
            continue

        obj_id, data = _parse_line(line)

        if 'T' not in data:
            # Object definition or static property
            if 'Pilot' in data:
                objects[obj_id]['Pilot'] = data['Pilot']
            if 'Group' in data:
                objects[obj_id]['Group'] = data['Group']
        else:
            # Event line with time T
            pilot = objects.get(obj_id, {}).get('Pilot', 'Unknown')
            formation = objects.get(obj_id, {}).get('Group', 'Unknown')
            event = data.get('Event', '').lower()

            # Generic counters for well-known events
            if 'shot' in event:
                pilot_stats[pilot]['Shots'] += 1
                formation_stats[formation]['Shots'] += 1
            elif 'hit' in event:
                pilot_stats[pilot]['Hits'] += 1
                formation_stats[formation]['Hits'] += 1
            elif 'kill' in event:
                pilot_stats[pilot]['Kills'] += 1
                formation_stats[formation]['Kills'] += 1
                target_id = data.get('PrimaryTarget') or data.get('Target')
                if target_id and target_id in objects:
                    target_pilot = objects[target_id].get('Pilot', 'Unknown')
                    target_formation = objects[target_id].get('Group', 'Unknown')
                    pilot_stats[target_pilot]['Deaths'] += 1
                    formation_stats[target_formation]['Deaths'] += 1
            elif 'takeoff' in event:
                pilot_stats[pilot]['Takeoffs'] += 1
                formation_stats[formation]['Takeoffs'] += 1
            elif 'land' in event:
                pilot_stats[pilot]['Landings'] += 1
                formation_stats[formation]['Landings'] += 1
            elif any(x in event for x in ['eject', 'crash', 'dead']):
                pilot_stats[pilot]['Deaths'] += 1
                formation_stats[formation]['Deaths'] += 1

    return {
        'metadata': metadata,
        'pilots': pilot_stats,
        'formations': formation_stats,
    }

