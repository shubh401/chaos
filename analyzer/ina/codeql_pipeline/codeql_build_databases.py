"""
codeql_build_databases.py — Phase 1 (build): constructs one CodeQL database per
extension from the signal-relevant files selected by codeql_select_files.py, in
parallel, with a hard per-extension timeout so a single pathological file cannot
stall the batch.

Separate from querying by design (per-user decision): databases are built once and
kept on disk, so the query phase (codeql_run_queries.py) can be re-run cheaply after
fixing/iterating the QL file, without rebuilding every database from scratch.

For each extension: copies its selected files into an isolated per-extension source
directory (CodeQL requires a source-root directory, not a bare file list), then runs
`codeql database create`.

Timing reference (measured on a real ~single-file content script this session):
~1.7s wall-clock per single-file database build. At 3,210 extensions with N_WORKERS=50,
expect low-single-digit minutes for the bulk of the corpus; the per-extension timeout
exists specifically to bound the LONG TAIL (large/pathological bundles), not the typical
case.

IMPORTANT — minified-file handling: CodeQL's JS extractor SILENTLY SKIPS any file it
content-heuristically detects as minified ("Skipping file X: File appears to be
minified.") — confirmed directly this session on a real corpus bundle file, and confirmed
there is NO extractor-option/env-var override in this CodeQL version
(`codeql resolve extractor --language=javascript --format=betterjson` shows the JS
extractor declares exactly one option, `skip_types`, unrelated to minification). Since
minified/bundled code is exactly the population this whole investigation (and RevB's
complaint) is about, silently letting CodeQL skip these files would systematically and
invisibly exclude the most important part of the corpus. FIX: every file is run through
`prettier` (reformats with real newlines/indentation) before being staged for database
construction — confirmed on the same real bundle file to eliminate the skip message while
still producing a database CodeQL can extract real flows from. Falls back to a raw copy
if prettier fails on a given file (some real-world JS won't parse cleanly) — a
prettier-failure is recorded per-file in the build manifest, not silently swallowed, since
a raw-copied minified file will then still be skipped by CodeQL and should be counted as
a disclosed coverage gap, not folded into the denominator silently.

Usage (run from analyzer/):
    python ina/codeql_pipeline/codeql_build_databases.py \\
        --files-json results/ina/taint/codeql_files_ina.json \\
        --db-root /datasets/codeql_dbs/ina \\
        --workers 50 --timeout 60

Optional:
    --limit N          only process the first N extensions (testing)

Requires `prettier` on PATH (npm install -g prettier) — verified working on this server
this session.
"""
import os, sys, json, shutil, subprocess, argparse, time, traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

CODEQL_BIN   = os.environ.get('CODEQL_BIN', 'codeql')
PRETTIER_BIN = os.environ.get('PRETTIER_BIN', 'prettier')
PRETTIER_TIMEOUT_S = 20  # per-file — bounds a single pathological file's beautify cost


def _beautify_or_copy(src, dst):
    """Run prettier on src, writing the reformatted output to dst. Falls back to a raw
    copy if prettier fails (non-zero exit or timeout) — some real-world JS won't parse
    cleanly. Returns a status string: 'beautified', 'raw_copy_fallback' (prettier failed,
    raw copy used — CodeQL may still skip this specific file as minified), or
    'unreadable' (neither succeeded)."""
    try:
        proc = subprocess.run(
            [PRETTIER_BIN, src],
            capture_output=True, text=True, timeout=PRETTIER_TIMEOUT_S,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(proc.stdout)
            return 'beautified'
    except Exception:
        pass
    # Fallback: raw copy — CodeQL may still skip this specific file as "minified" if
    # prettier failed on genuinely malformed/non-standard JS; this is a real, disclosed
    # coverage gap (recorded per-extension in the build manifest), not something to hide.
    try:
        shutil.copy2(src, dst)
        return 'raw_copy_fallback'
    except Exception:
        return 'unreadable'


def build_one(args):
    ext_id, file_paths, staging_root, db_root, timeout = args
    staging_dir = os.path.join(staging_root, ext_id)
    db_path     = os.path.join(db_root, ext_id)
    result = {'extension_id': ext_id, 'status': None, 'elapsed_s': None, 'error': None,
              'n_beautified': 0, 'n_raw_copy_fallback': 0, 'n_unreadable': 0}

    t0 = time.time()
    try:
        # Fresh staging dir with just the selected files (flattened — filename
        # collisions across different subdirectories of the SAME extension are rare
        # but possible; disambiguate by prefixing with an index if needed).
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)
        os.makedirs(staging_dir, exist_ok=True)

        seen_names = set()
        for i, src in enumerate(file_paths):
            base = os.path.basename(src)
            if base in seen_names:
                base = f"{i}_{base}"
            seen_names.add(base)
            dst = os.path.join(staging_dir, base)
            beautify_status = _beautify_or_copy(src, dst)
            if beautify_status == 'beautified':
                result['n_beautified'] += 1
            elif beautify_status == 'raw_copy_fallback':
                result['n_raw_copy_fallback'] += 1
            else:
                result['n_unreadable'] += 1
                continue  # a single unreadable file shouldn't sink the whole extension

        if not os.listdir(staging_dir):
            result['status'] = 'no_files_copied'
            return result

        if os.path.exists(db_path):
            shutil.rmtree(db_path, ignore_errors=True)

        proc = subprocess.run(
            [CODEQL_BIN, 'database', 'create', db_path,
             '--language=javascript', f'--source-root={staging_dir}',
             '--overwrite'],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode == 0:
            result['status'] = 'ok'
        else:
            result['status'] = 'codeql_error'
            result['error'] = (proc.stderr or proc.stdout)[-2000:]
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
        result['error'] = f'exceeded {timeout}s'
    except Exception:
        result['status'] = 'exception'
        result['error'] = traceback.format_exc()[-2000:]
    finally:
        # Staging copy is disposable — always clean it up regardless of outcome to
        # bound disk usage (the DB itself is what we keep for phase 2).
        shutil.rmtree(staging_dir, ignore_errors=True)
        result['elapsed_s'] = round(time.time() - t0, 2)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files-json', required=True)
    parser.add_argument('--db-root', required=True,
                         help='Directory to hold one CodeQL database subdir per extension')
    parser.add_argument('--staging-root', default=None,
                         help='Scratch dir for per-extension flattened file copies '
                              '(default: <db-root>/../_staging)')
    parser.add_argument('--workers', type=int, default=50)
    parser.add_argument('--timeout', type=int, default=180,
                         help='Per-extension hard timeout in seconds for `codeql database create` '
                              '(default 180s — two-tier strategy: run the bulk at this timeout, '
                              'then use --retry-manifest with a HIGHER --timeout for only the '
                              'extensions that timed out, rather than paying a high timeout for '
                              'the whole corpus upfront)')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--retry-manifest', default=None,
                         help='Path to a prior codeql_build_manifest_<signal>.json — if given, '
                              'ONLY the extensions whose status was "timeout" in that manifest are '
                              'rebuilt (their existing, partial/failed database dirs are removed '
                              'first). Use with a higher --timeout than the original run. The '
                              'output manifest is written to a distinct path '
                              '(codeql_build_manifest_<signal>_retry.json) so the original manifest '
                              'is never overwritten — merge results yourself once satisfied.')
    args = parser.parse_args()

    data = json.loads(Path(args.files_json).read_text())
    files_by_ext = data['files_by_extension']
    ext_ids = sorted(files_by_ext.keys())

    if args.retry_manifest:
        prior = json.loads(Path(args.retry_manifest).read_text())
        timed_out_ids = {r['extension_id'] for r in prior['results'] if r['status'] == 'timeout'}
        ext_ids = [e for e in ext_ids if e in timed_out_ids]
        print(f"Retry mode: {len(ext_ids):,} extension(s) that timed out in "
              f"{args.retry_manifest} (out of {len(timed_out_ids):,} recorded there — some may "
              f"no longer be present in --files-json if the population changed).")

    if args.limit:
        ext_ids = ext_ids[:args.limit]

    db_root = args.db_root
    staging_root = args.staging_root or os.path.join(os.path.dirname(db_root.rstrip('/')), '_staging')
    os.makedirs(db_root, exist_ok=True)
    os.makedirs(staging_root, exist_ok=True)

    print(f"Signal: {data.get('signal')}  |  Extensions to build: {len(ext_ids):,}  |  "
          f"Workers: {args.workers}  |  Per-extension timeout: {args.timeout}s")
    print(f"DB root: {db_root}\nStaging root: {staging_root}\n")

    tasks = [(ext_id, files_by_ext[ext_id], staging_root, db_root, args.timeout)
             for ext_id in ext_ids]

    results = []
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(build_one, t): t[0] for t in tasks}
        n_done = 0
        for fut in as_completed(futures):
            ext_id = futures[fut]
            try:
                r = fut.result()
            except Exception:
                r = {'extension_id': ext_id, 'status': 'worker_exception',
                     'error': traceback.format_exc()[-2000:], 'elapsed_s': None}
            results.append(r)
            n_done += 1
            if n_done % 100 == 0 or n_done == len(tasks):
                elapsed = time.time() - t_start
                print(f"  {n_done}/{len(tasks)} done ({elapsed:.0f}s elapsed)")

    status_counts = {}
    for r in results:
        status_counts[r['status']] = status_counts.get(r['status'], 0) + 1

    total_elapsed = time.time() - t_start
    print(f"\nDone in {total_elapsed:.0f}s. Status breakdown:")
    for status, n in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {status:<20} {n:>6,}")

    n_timeout = status_counts.get('timeout', 0)
    if n_timeout:
        timed_out = [r['extension_id'] for r in results if r['status'] == 'timeout']
        print(f"\n{n_timeout} extension(s) exceeded the {args.timeout}s build timeout — "
              f"NOT SILENTLY DROPPED, recorded explicitly (see manifest 'timeout' status). "
              f"These are excluded from the query phase and should be reported as a known, "
              f"disclosed coverage gap, not folded silently into a lower denominator.")

    total_beautified = sum(r.get('n_beautified', 0) for r in results)
    total_raw_fallback = sum(r.get('n_raw_copy_fallback', 0) for r in results)
    total_unreadable = sum(r.get('n_unreadable', 0) for r in results)
    print(f"\nFile-level preprocessing (across all extensions):")
    print(f"  Beautified successfully:        {total_beautified:>6,}")
    print(f"  Prettier failed, raw-copy used: {total_raw_fallback:>6,}  "
          f"(these files may still be silently skipped by CodeQL as \"minified\" — a "
          f"disclosed, not hidden, coverage gap)")
    print(f"  Unreadable (neither worked):    {total_unreadable:>6,}")

    suffix = '_retry' if args.retry_manifest else ''
    manifest_path = os.path.join(os.path.dirname(db_root.rstrip('/')),
                                  f"codeql_build_manifest_{data.get('signal', 'unknown')}{suffix}.json")
    with open(manifest_path, 'w') as f:
        json.dump({
            'signal': data.get('signal'),
            'db_root': db_root,
            'timeout_s': args.timeout,
            'n_workers': args.workers,
            'total_elapsed_s': round(total_elapsed, 1),
            'status_counts': status_counts,
            'total_files_beautified': total_beautified,
            'total_files_raw_copy_fallback': total_raw_fallback,
            'total_files_unreadable': total_unreadable,
            'results': results,
            'note': (
                'files with n_raw_copy_fallback > 0 may still be silently skipped by '
                'CodeQL\'s content-based minified-file detection (no extractor-option '
                'override exists in this CodeQL version — confirmed via `codeql resolve '
                'extractor --language=javascript --format=betterjson`). This is a real, '
                'disclosed coverage gap, not folded into the denominator silently — cross-'
                'reference against codeql_run_queries.py\'s per-extension flow counts if '
                'a specific extension shows suspiciously zero flows AND has '
                'n_raw_copy_fallback > 0 for its only file(s).'
            ),
        }, f, indent=2)
    print(f"\nManifest saved: {manifest_path}")
    print("Next: codeql_run_queries.py against this db-root.")


if __name__ == '__main__':
    main()
