#!/usr/bin/env python3
"""
Scenario Selector

Selects files from step folders according to tags:
- optional: random inclusion chance
- terminal: stop after this step
- choose1: pick one child folder, then one file (supports hub folders whose
  children use arbitrary names, scanned by step_reader's
  scan_choose1_hub_children)
- random: pick from all sub-subfolders in random order

Part of the test data assembly pipeline.
"""

import random
import re
from pathlib import Path


# ------------------------------------------------------------
# Helper functions (duplicated from step_reader for standalone)
# ------------------------------------------------------------

def parse_optional_chance(folder_name: str) -> float:
    match = re.search(r'optional[^-\d]*?(\d+(?:\.\d+)?)', folder_name, re.IGNORECASE)
    if match:
        centre = float(match.group(1))
        lo = max(1.0, centre - 2.0)
        hi = min(99.0, centre + 2.0)
        return random.uniform(lo, hi) / 100.0
    return random.uniform(0.24, 0.33)


def parse_max_files(folder_name: str):
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


# ------------------------------------------------------------
# Signature helper for nested combos
# ------------------------------------------------------------

def _combo_fp_sig(fp, i=0):
    """Generate a signature fragment for a file or nested combo."""
    if hasattr(fp, 'name'):
        return fp.name
    if isinstance(fp, dict) and fp.get('_nested'):
        parts = []
        for _ifn, _ifl in fp.get('combo', []):
            for _ifp in (_ifl if isinstance(_ifl, list) else [_ifl]):
                parts.append(_combo_fp_sig(_ifp, i))
        return 'N(' + '+'.join(parts) + ')' if parts else f'nested_{i}'
    return f'nested_{i}'


# ------------------------------------------------------------
# Combinatorial pool-size estimation
# ------------------------------------------------------------

def _pool_size(folder_data):
    """
    Estimate the number of distinct file choices a folder/hub can produce.

    Without this, files living behind a (choose1)/(random) hub are
    invisible to the top-level combo count -- a folder's own `files` list
    is empty once its content moves into `nested_subfolder_files`, so the
    naive `len(files)` count treats the whole hub as contributing nothing,
    and the combination-history dedup window resets almost immediately.
    """
    files = folder_data.get('files') or []
    nsf = folder_data.get('nested_subfolder_files')

    if not nsf:
        return len(files)

    child_sizes = [max(1, _pool_size(child)) for child in nsf.values()]

    if folder_data.get('is_choose1'):
        # Pick exactly one child, then one file from it -> combos add up
        # across children (picking child A's file 1, or child A's file 2,
        # or child B's file 1, ... are each a distinct combo).
        return sum(child_sizes)

    if folder_data.get('is_random'):
        rmax = folder_data.get('random_max')
        if rmax and rmax < len(child_sizes):
            # Approximation: this ignores *which* subset of children gets
            # sampled and just bounds the product using the largest pools.
            # Good enough in practice -- exact accounting would need
            # combinatorial (n choose rmax) bookkeeping for little benefit.
            child_sizes = sorted(child_sizes, reverse=True)[:rmax]
        total = 1
        for s in child_sizes:
            total *= s
        return total

    # Plain nested steps compose sequentially -> combos multiply.
    total = 1
    for s in child_sizes:
        total *= s
    return total


# ------------------------------------------------------------
# Main selector class
# ------------------------------------------------------------

class ManualHistoryTracker:
    """
    Tracks used file combinations and generates new ones with respect to tags.
    """
    def __init__(self, subfolder_files, rng, folder_name, input_dir):
        self.subfolder_files = subfolder_files
        self.rng = rng
        self.folder_name = folder_name
        self.input_dir = input_dir
        self.history_dir = input_dir / "combination_history"
        self.used_combinations = self._load_all_combinations()
        self._sequence_reused = False

        # Compute total possible combos (recurses into choose1/random hubs
        # so files living behind a hub aren't invisible to the count)
        pool_sizes = [_pool_size(fd) for fd in subfolder_files.values()]
        total_possible = 1
        for ps in pool_sizes:
            total_possible *= max(1, ps)
        self._total_possible_combos = total_possible
        self._is_single_slot = (len(subfolder_files) == 1 and
                                not any(fd.get('nested_subfolder_files') for fd in subfolder_files.values()))

        if (not self._is_single_slot and len(self.used_combinations) >= total_possible and total_possible > 0):
            print(f"   [combo reset] All {total_possible} combination(s) used; resetting history.")
            self.used_combinations.clear()

        # Per-subfolder file queues
        self._file_queues = {}
        for fn, fd in self.subfolder_files.items():
            pool = list(fd.get('files', []))
            self.rng.shuffle(pool)
            self._file_queues[fn] = pool

        # Nested trackers for subfolders that contain their own sub-subfolders.
        # choose1/random hubs handle their own children directly in
        # get_next_combination() and never call into a nested tracker --
        # building one for them is wasted work (history load + print noise).
        self._nested_trackers = {}
        for fn, fd in self.subfolder_files.items():
            nsf = fd.get('nested_subfolder_files')
            if nsf and not fd.get('is_choose1') and not fd.get('is_random'):
                self._nested_trackers[fn] = ManualHistoryTracker(
                    nsf, self.rng, f"{self.folder_name}_nested_{fn}", self.input_dir
                )

        print(f"   {len(self.used_combinations)} combinations loaded from history")

    def _load_all_combinations(self):
        all_used = set()
        if not self.history_dir.exists():
            return all_used
        txt_files = list(self.history_dir.glob("*.txt"))
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('[') or line.startswith('='):
                            continue
                        if 'F' in line and '=' in line and '|' in line:
                            if line.startswith('[') and ']' in line:
                                continue
                            all_used.add(line)
            except Exception as e:
                print(f"   Warning: could not read {txt_file.name}: {e}")
        return all_used

    def _next_file(self, folder_num):
        q = self._file_queues.get(folder_num)
        if not q:
            pool = list(self.subfolder_files.get(folder_num, {}).get('files', []))
            if not pool:
                return None
            self.rng.shuffle(pool)
            last_key = f"_last_{folder_num}"
            last = getattr(self, last_key, None)
            if last is not None and len(pool) > 1 and pool[-1] == last:
                swap = self.rng.randint(0, len(pool) - 2)
                pool[-1], pool[swap] = pool[swap], pool[-1]
            self._file_queues[folder_num] = pool
            q = self._file_queues[folder_num]
        item = q.pop()
        setattr(self, f"_last_{folder_num}", item)
        return item

    def get_next_combination(self):
        """
        Generate a new combination respecting optional/terminal/choose1/random tags.
        """
        all_nested = all(fd.get('nested_subfolder_files') and not fd.get('files')
                         for fd in self.subfolder_files.values())
        max_attempts = 500 if not all_nested else 1

        for _ in range(max_attempts):
            combination = []
            for folder_num in sorted(self.subfolder_files.keys()):
                folder_data = self.subfolder_files[folder_num]

                # optional+end
                if folder_data.get('is_optional_end', False):
                    chance = folder_data.get('optional_chance', 0.50)
                    if self.rng.random() < chance:
                        f = self._next_file(folder_num)
                        if f:
                            combination.append((folder_num, [f]))
                        break
                    else:
                        continue

                # regular end
                if folder_data.get('is_end', False) and not folder_data.get('is_optional', False):
                    f = self._next_file(folder_num)
                    if f:
                        combination.append((folder_num, [f]))
                    break

                # optional skip
                if folder_data.get('is_optional', False):
                    chance = folder_data.get('optional_chance', 0.50)
                    if self.rng.random() >= chance:
                        continue

                nsf = folder_data.get('nested_subfolder_files')
                max_files = folder_data.get('max_files', 1)
                n = self.rng.randint(1, max_files) if max_files and max_files > 1 else 1

                if nsf:
                    tracker = self._nested_trackers.get(folder_num)
                    picked = []

                    # --- (choose1) logic ---
                    if folder_data.get('is_choose1'):
                        sub_nums = sorted(nsf.keys())
                        if sub_nums:
                            chosen_sn = self.rng.choice(sub_nums)
                            sf_data = nsf[chosen_sn]

                            # If chosen child is (random), run full random logic
                            if sf_data.get('is_random'):
                                child_nsf = sf_data.get('nested_subfolder_files', {})
                                if child_nsf:
                                    child_nums = sorted(child_nsf.keys())
                                    self.rng.shuffle(child_nums)
                                    rmax = sf_data.get('random_max')
                                    if rmax and rmax < len(child_nums):
                                        child_nums = child_nums[:rmax]
                                    for csn in child_nums:
                                        csf_files = child_nsf[csn].get('files', [])
                                        if csf_files:
                                            f = self.rng.choice(csf_files)
                                            picked.append({
                                                '_nested': True,
                                                '_random_single': True,
                                                '_parent_folder_num': folder_num,
                                                'combo': [(csn, [f])],
                                                'nested_sf': child_nsf,
                                                'nested_root_af': folder_data.get('nested_root_always_first'),
                                                'nested_root_al': folder_data.get('nested_root_always_last'),
                                            })
                            else:
                                # Normal child – pick one file
                                sf_files = sf_data.get('files', [])
                                if sf_files:
                                    f = self.rng.choice(sf_files)
                                    picked.append({
                                        '_nested': True,
                                        '_random_single': True,
                                        '_parent_folder_num': folder_num,
                                        'combo': [(chosen_sn, [f])],
                                        'nested_sf': nsf,
                                        'nested_root_af': folder_data.get('nested_root_always_first'),
                                        'nested_root_al': folder_data.get('nested_root_always_last'),
                                    })
                    # --- (random) logic (standalone) ---
                    elif folder_data.get('is_random'):
                        sub_nums = sorted(nsf.keys())
                        self.rng.shuffle(sub_nums)
                        rmax = folder_data.get('random_max')
                        if rmax and rmax < len(sub_nums):
                            sub_nums = sub_nums[:rmax]
                        for sn in sub_nums:
                            sf_data = nsf[sn]
                            sf_files = sf_data.get('files', [])
                            if sf_files:
                                f = self.rng.choice(sf_files)
                                picked.append({
                                    '_nested': True,
                                    '_random_single': True,
                                    '_parent_folder_num': folder_num,
                                    'combo': [(sn, [f])],
                                    'nested_sf': nsf,
                                    'nested_root_af': folder_data.get('nested_root_always_first'),
                                    'nested_root_al': folder_data.get('nested_root_always_last'),
                                })
                    else:
                        # Normal nested – pick n combos from the inner tracker
                        for _ in range(n):
                            sub_combo = tracker.get_next_combination()
                            if sub_combo:
                                picked.append({
                                    '_nested': True,
                                    'combo': sub_combo,
                                    'nested_sf': nsf,
                                    'nested_root_af': folder_data.get('nested_root_always_first'),
                                    'nested_root_al': folder_data.get('nested_root_always_last'),
                                })
                    if picked:
                        combination.append((folder_num, picked))
                else:
                    # Regular folder – pick files from queue
                    picked_files = []
                    for _ in range(n):
                        f = self._next_file(folder_num)
                        if f:
                            picked_files.append(f)
                    if picked_files:
                        combination.append((folder_num, picked_files))

            if not combination:
                continue

            if all_nested:
                return combination

            # Generate signature for deduplication
            signature = "|".join(
                f"F{int(fn) if fn == int(fn) else fn}=" +
                "+".join(_combo_fp_sig(fp, i) for i, fp in enumerate(fl if isinstance(fl, list) else [fl]))
                for fn, fl in combination
            )

            if self._is_single_slot:
                return combination

            if self._total_possible_combos > 0 and len(self.used_combinations) >= self._total_possible_combos:
                self.used_combinations.clear()

            if signature not in self.used_combinations:
                self.used_combinations.add(signature)
                return combination

        # Fallback (sequence reused)
        print(f"  [!]  Using random combination (may repeat)")
        self._sequence_reused = True
        combination = []
        for folder_num in sorted(self.subfolder_files.keys()):
            folder_data = self.subfolder_files[folder_num]
            if folder_data.get('is_optional_end', False):
                chance = folder_data.get('optional_chance', 0.50)
                if self.rng.random() < chance:
                    f = self._next_file(folder_num)
                    if f:
                        combination.append((folder_num, [f]))
                    break
                else:
                    continue
            if folder_data.get('is_end', False) and not folder_data.get('is_optional', False):
                f = self._next_file(folder_num)
                if f:
                    combination.append((folder_num, [f]))
                break
            if folder_data.get('is_optional', False):
                chance = folder_data.get('optional_chance', 0.50)
                if self.rng.random() >= chance:
                    continue
            f = self._next_file(folder_num)
            if f:
                combination.append((folder_num, [f]))
        return combination if combination else None


# ------------------------------------------------------------
# Demo / test harness
# ------------------------------------------------------------

def main():
    import argparse
    from step_reader import scan_for_numbered_subfolders  # we assume step_reader is available

    parser = argparse.ArgumentParser(
        description="Demonstrate scenario selector with a given folder."
    )
    parser.add_argument("input_root", type=str, help="Root folder with step1/, step2/, etc.")
    parser.add_argument("--count", type=int, default=10, help="Number of combinations to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    base_path = Path(args.input_root)
    if not base_path.exists():
        print(f"[X] Input root not found: {base_path}")
        return

    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    # Scan folders using the step_reader
    folders, non_json, root_af, root_al = scan_for_numbered_subfolders(base_path)
    if not folders:
        print("No step folders found.")
        return

    tracker = ManualHistoryTracker(folders, rng, base_path.name, base_path.parent)

    for i in range(args.count):
        combo = tracker.get_next_combination()
        if combo is None:
            print(f"  No more unique combinations (exhausted)")
            break
        print(f"Combo {i+1}:")
        for step, files in combo:
            if isinstance(files, list):
                print(f"  Step {step}: {[f.name for f in files if hasattr(f, 'name')]}")
            else:
                print(f"  Step {step}: {files}")  # nested dict

if __name__ == "__main__":
    main()
