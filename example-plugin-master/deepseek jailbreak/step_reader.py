#!/usr/bin/env python3
"""
Step Reader

Reads JSON fixtures from numbered step folders (step1/, step2/, ...)
with support for:
- Nested subfolders
- Folder merging (same step number)
- Optional/conditional tags
- Terminal stops
- Random/choose1 selection
- (choose1) hub folders whose children use ARBITRARY names (e.g.
  workflow_01/, workflow_02/, ...) instead of step-number names

Output: dict of step folders with file lists and metadata.
"""

import re
import random
from pathlib import Path


def parse_optional_chance(folder_name: str) -> float:
    """Parse optional inclusion probability from folder name."""
    match = re.search(r'optional[^-\d]*?(\d+(?:\.\d+)?)', folder_name, re.IGNORECASE)
    if match:
        centre = float(match.group(1))
        lo = max(1.0, centre - 2.0)
        hi = min(99.0, centre + 2.0)
        return random.uniform(lo, hi) / 100.0
    return random.uniform(0.24, 0.33)


def parse_max_files(folder_name: str):
    """Parse max-files count from folder name. Returns None if no explicit count is present."""
    name = folder_name.strip('/').strip()
    name = re.sub(r'^[Ff]?\d+(?:\.\d+)?\s*', '', name)
    name = re.sub(r'optional\s*\d+(?:\.\d+)?', 'optional', name, flags=re.IGNORECASE)
    matches = re.findall(r'-(\d+)-', name)
    if matches:
        try:
            return max(1, int(matches[-1]))
        except ValueError:
            pass
    return None


def scan_choose1_hub_children(hub_path):
    """
    Enumerate the children of a (choose1) hub folder, regardless of naming
    convention. Each child becomes one entry in the returned dict, keyed by
    a synthetic index (NOT parsed from the folder name) so children can be
    named anything (workflow_01, cut_long, default, ...).

    If a child is itself tagged (random), its own sub-subfolders are
    expected to follow the normal numbered-folder convention, and are
    scanned with scan_for_numbered_subfolders so the existing (random)
    selection logic in the scenario selector keeps working unchanged.

    Returns: (children_dict, non_json_files)
    """
    hub = Path(hub_path)
    children = {}
    non_json_files = []

    child_dirs = []
    for d in sorted(hub.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        d_lower = d.name.lower()
        if d_lower == 'session_end, wait, in' or d.name.startswith('@'):
            continue
        if d_lower in ("don't use features on me", "dont mess with me"):
            continue
        child_dirs.append(d)

    for idx, child in enumerate(child_dirs):
        child_lower = child.name.lower()

        json_files = sorted(child.glob("*.json"))
        always_first = []
        always_last = []
        regular_files = []
        for jf in json_files:
            name_lower = jf.name.lower()
            if 'always first' in name_lower or 'alwaysfirst' in name_lower:
                always_first.append(jf)
            elif 'always last' in name_lower or 'alwayslast' in name_lower:
                always_last.append(jf)
            else:
                regular_files.append(jf)

        random_match = re.search(r'\(random(\d*)\)', child.name, re.IGNORECASE)
        is_random = bool(random_match)
        random_max = int(random_match.group(1)) if (is_random and random_match.group(1)) else None

        is_optional = 'optional' in child_lower
        optional_chance = parse_optional_chance(child.name) if is_optional else None
        is_end = bool(re.search(r'\bend\b', child.name, re.IGNORECASE))
        is_optional_end = is_optional and is_end

        is_time_sensitive = 'time sensitive' in child_lower
        is_click_time = ('click/time sensitive' in child_lower or
                         'click+time sensitive' in child_lower or
                         'click time sensitive' in child_lower)
        is_click = 'click sensitive' in child_lower
        if is_click_time:
            is_time_sensitive = True
            is_click = True

        nested_subfolder_files = None
        if is_random:
            # Random children keep using the normal numbered convention
            # for their own sub-subfolders (the "slots" to combine).
            nf, nnj, naf, nal = scan_for_numbered_subfolders(child)
            non_json_files.extend(nnj)
            if nf:
                nested_subfolder_files = nf

        for f in child.iterdir():
            if f.is_file() and not f.name.endswith('.json'):
                non_json_files.append(f)

        children[idx] = {
            'files': regular_files,
            'is_optional': is_optional,
            'optional_chance': optional_chance,
            'is_end': is_end,
            'is_optional_end': is_optional_end,
            'is_time_sensitive': is_time_sensitive,
            'is_click_sensitive': is_click,
            'max_files': parse_max_files(child.name),
            'always_first': always_first,
            'always_last': always_last,
            'nested_subfolder_files': nested_subfolder_files,
            'nested_root_always_first': None,
            'nested_root_always_last': None,
            'is_random': is_random,
            'random_max': random_max,
            'is_choose1': False,
            'folder_name': child.name,
            'folder_path': child,
        }

    return children, non_json_files


def scan_for_numbered_subfolders(base_path):
    """
    Scan for numbered subfolders (step1/, step2/, etc.) and collect JSON files.
    """
    base = Path(base_path)
    numbered_folders = {}
    non_json_files = []

    base_lower = base.name.lower()
    main_optional = 'optional' in base_lower
    main_time_sensitive = 'time sensitive' in base_lower
    main_click_sensitive = ('click sensitive' in base_lower or
                            'click/time sensitive' in base_lower or
                            'click+time sensitive' in base_lower or
                            'click time sensitive' in base_lower)

    for item in base.iterdir():
        if not item.is_dir():
            if not item.name.endswith('.json'):
                non_json_files.append(item)
            continue

        folder_lower = item.name.lower()
        if folder_lower == 'session_end, wait, in' or item.name.startswith('@'):
            continue
        if folder_lower in ("don't use features on me", "dont mess with me"):
            continue

        f_match = re.match(r'^[Ff](\d+(?:\.\d+)?)', item.name.strip())
        if f_match:
            folder_num = float(f_match.group(1))
        else:
            n_match = re.search(r'\d+\.?\d*', item.name)
            folder_num = float(n_match.group()) if n_match else None

        if folder_num is None:
            continue

        json_files = sorted(item.glob("*.json"))
        always_first = []
        always_last = []
        regular_files = []

        for jf in json_files:
            name_lower = jf.name.lower()
            if 'always first' in name_lower or 'alwaysfirst' in name_lower:
                always_first.append(jf)
            elif 'always last' in name_lower or 'alwayslast' in name_lower:
                always_last.append(jf)
            else:
                regular_files.append(jf)

        is_optional = 'optional' in item.name.lower()
        optional_chance = parse_optional_chance(item.name) if is_optional else None
        is_end = bool(re.search(r'\bend\b', item.name, re.IGNORECASE))
        is_optional_end = is_optional and is_end

        if main_time_sensitive:
            is_time_sensitive = True
        else:
            is_time_sensitive = 'time sensitive' in item.name.lower()

        item_lower = item.name.lower()
        is_click_time = ('click/time sensitive' in item_lower or
                         'click+time sensitive' in item_lower or
                         'click time sensitive' in item_lower)
        is_click = ('click sensitive' in item_lower) and not is_click_time
        if is_click_time:
            is_time_sensitive = True
            is_click = True
        if main_click_sensitive:
            is_click = True

        random_match = re.search(r'\(random(\d*)\)', item.name, re.IGNORECASE)
        is_random = bool(random_match)
        random_max = int(random_match.group(1)) if (is_random and random_match.group(1)) else None
        if is_random:
            is_click = True

        is_choose1 = bool(re.search(r'\(choose1\)', item.name, re.IGNORECASE))

        nested_subfolder_files = None
        nested_root_af = None
        nested_root_al = None

        if is_choose1:
            # Hub folders enumerate ALL child directories regardless of
            # naming convention -- children don't need a step-number prefix.
            hub_children, hub_nnj = scan_choose1_hub_children(item)
            non_json_files.extend(hub_nnj)
            if hub_children:
                nested_subfolder_files = hub_children
        elif not regular_files:
            nested_dirs = [d for d in item.iterdir() if d.is_dir() and
                           (re.search(r'^[Ff]?\d', d.name) or re.search(r'\(\d+\)', d.name))]
            if nested_dirs:
                nf, nnj, naf, nal = scan_for_numbered_subfolders(item)
                non_json_files.extend(nnj)
                if nf:
                    nested_subfolder_files = nf
                    nested_root_af = naf
                    nested_root_al = nal

        if regular_files or nested_subfolder_files:
            entry = {
                'files': regular_files,
                'is_optional': is_optional,
                'optional_chance': optional_chance,
                'is_end': is_end,
                'is_optional_end': is_optional_end,
                'is_time_sensitive': is_time_sensitive,
                'is_click_sensitive': is_click,
                'max_files': parse_max_files(item.name),
                'always_first': always_first,
                'always_last': always_last,
                'nested_subfolder_files': nested_subfolder_files,
                'nested_root_always_first': nested_root_af,
                'nested_root_always_last': nested_root_al,
                'is_random': is_random,
                'random_max': random_max,
                'is_choose1': is_choose1,
                'folder_name': item.name,
                'folder_path': item,
            }

            if folder_num not in numbered_folders:
                numbered_folders[folder_num] = entry
            else:
                existing = numbered_folders[folder_num]
                existing['files'] += regular_files
                existing['always_first'] += always_first
                existing['always_last'] += always_last
                existing['is_optional'] = existing['is_optional'] or is_optional
                existing['is_end'] = existing['is_end'] or is_end
                existing['is_optional_end'] = existing['is_optional_end'] or is_optional_end
                existing['is_time_sensitive'] = existing['is_time_sensitive'] or is_time_sensitive
                existing['is_click_sensitive'] = existing['is_click_sensitive'] or is_click
                if existing['optional_chance'] is None and optional_chance is not None:
                    existing['optional_chance'] = optional_chance
                if existing['max_files'] is None and entry['max_files'] is not None:
                    existing['max_files'] = entry['max_files']
                if nested_subfolder_files:
                    if existing['nested_subfolder_files'] is None:
                        existing['nested_subfolder_files'] = nested_subfolder_files
                        existing['nested_root_always_first'] = nested_root_af
                        existing['nested_root_always_last'] = nested_root_al
                    else:
                        for inner_num, inner_data in nested_subfolder_files.items():
                            if inner_num not in existing['nested_subfolder_files']:
                                existing['nested_subfolder_files'][inner_num] = inner_data
                            else:
                                inn = existing['nested_subfolder_files'][inner_num]
                                inn['files'] += inner_data.get('files', [])
                                inn['always_first'] += inner_data.get('always_first', [])
                                inn['always_last'] += inner_data.get('always_last', [])
                        existing['nested_root_always_first'] = (existing.get('nested_root_always_first') or []) + (nested_root_af or [])
                        existing['nested_root_always_last'] = (existing.get('nested_root_always_last') or []) + (nested_root_al or [])

        for file in item.iterdir():
            if file.is_file() and not file.name.endswith('.json'):
                non_json_files.append(file)

    # Flat folder support
    if not numbered_folders:
        direct_json = [f for f in base.glob('*.json') if f.name.lower() not in ('session_end.json', '- session_end.json')]
        if direct_json:
            always_first = [f for f in direct_json if 'always first' in f.name.lower() or 'alwaysfirst' in f.name.lower()]
            always_last = [f for f in direct_json if 'always last' in f.name.lower() or 'alwayslast' in f.name.lower()]
            regular = [f for f in direct_json if f not in always_first and f not in always_last]
            if regular:
                numbered_folders[1.0] = {
                    'files': regular,
                    'is_optional': False,
                    'optional_chance': None,
                    'is_end': False,
                    'is_optional_end': False,
                    'is_time_sensitive': main_time_sensitive,
                    'is_click_sensitive': main_click_sensitive,
                    'max_files': 1,
                    'always_first': always_first,
                    'always_last': always_last,
                    'nested_subfolder_files': None,
                    'nested_root_always_first': None,
                    'nested_root_always_last': None,
                    'is_random': False,
                    'random_max': None,
                    'is_choose1': False,
                    'folder_name': base.name,
                    'folder_path': base,
                }

    root_always_first = []
    root_always_last = []
    is_flat_scan = (set(numbered_folders.keys()) == {1.0} and not any(
        re.match(r'(?i)^[Ff]?\d', d.name) for d in base.iterdir() if d.is_dir()
    )) if numbered_folders else False

    if numbered_folders and not is_flat_scan:
        for rf in sorted(base.glob('*.json')):
            name = rf.name.lower()
            if 'always first' in name or 'alwaysfirst' in name:
                root_always_first.append(rf)
            elif 'always last' in name or 'alwayslast' in name:
                root_always_last.append(rf)

    return numbered_folders, non_json_files, root_always_first, root_always_last


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Read step folders and print summary."
    )
    parser.add_argument("input_root", type=str, help="Root folder with step1/, step2/, etc.")
    args = parser.parse_args()

    base_path = Path(args.input_root)
    if not base_path.exists():
        print(f"[X] Input root not found: {base_path}")
        return

    folders, non_json, root_af, root_al = scan_for_numbered_subfolders(base_path)

    print(f"Found {len(folders)} step folders:")
    for num, data in sorted(folders.items()):
        print(f"  Step {int(num) if num == int(num) else num}: {len(data['files'])} files")
        if data.get('is_optional'):
            print(f"    Optional: {data.get('optional_chance', 0.0):.2f}%")
        if data.get('is_end'):
            print("    Terminal (end) folder")
        if data.get('is_choose1'):
            print(f"    Choose-one hub: {len(data.get('nested_subfolder_files') or {})} child folder(s)")
        if data.get('is_random'):
            print(f"    Random: max {data.get('random_max', 'all')} sub-folders")

    print(f"Root always_first: {len(root_af)} file(s)")
    print(f"Root always_last: {len(root_al)} file(s)")
    print(f"Non-JSON files: {len(non_json)}")


if __name__ == "__main__":
    main()
