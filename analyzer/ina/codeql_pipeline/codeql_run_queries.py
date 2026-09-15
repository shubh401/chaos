"""
codeql_run_queries.py — Phase 2 (query): runs the validated ext_taint_locations.ql
query against every CodeQL database built by codeql_build_databases.py, in parallel,
with a hard per-database timeout.

Separate from the build phase by design (per-user decision) — this can be re-run
cheaply against the already-built databases if the query itself needs iteration,
without rebuilding anything.

Timing reference (measured on a real content script this session): ~1.7s wall-clock
per single-file database query. At 3,210 extensions with N_WORKERS=50, expect
low-single-digit minutes for the bulk; the per-database timeout bounds the long tail.

Usage (run from analyzer/):
    python ina/codeql_pipeline/codeql_run_queries.py \\
        --db-root /datasets/codeql_dbs/ina \\
        --query ina/codeql_queries/ext_taint_locations.ql \\
        --out results/ina/taint/codeql_flows_ina.json \\
        --workers 50 --timeout 60
"""
import os, sys, json, subprocess, argparse, time, traceback, tempfile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

CODEQL_BIN = os.environ.get('CODEQL_BIN', 'codeql')


def run_one(args):
    ext_id, db_path, query_path, timeout = args
    result = {'extension_id': ext_id, 'status': None, 'elapsed_s': None,
              'error': None, 'flows': []}

    t0 = time.time()
    bqrs_path = None
    try:
        if not os.path.isdir(db_path):
            result['status'] = 'db_missing'
            return result

        fd, bqrs_path = tempfile.mkstemp(suffix='.bqrs', prefix=f'{ext_id}_')
        os.close(fd)

        proc = subprocess.run(
            [CODEQL_BIN, 'query', 'run',
             f'--database={db_path}', f'--output={bqrs_path}', query_path],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            result['status'] = 'codeql_error'
            result['error'] = (proc.stderr or proc.stdout)[-2000:]
            return result

        decode = subprocess.run(
            [CODEQL_BIN, 'bqrs', 'decode', '--format=json', bqrs_path],
            capture_output=True, text=True, timeout=30,
        )
        if decode.returncode != 0:
            result['status'] = 'decode_error'
            result['error'] = (decode.stderr or decode.stdout)[-2000:]
            return result

        decoded = json.loads(decode.stdout)
        # ext_taint_locations.ql's #select columns:
        # source_file, source_line, source_text, sink_file, sink_line, sink_text
        rows = decoded.get('#select', {}).get('tuples', [])
        flows = []
        for row in rows:
            if len(row) < 6:
                continue
            flows.append({
                'source_file': row[0], 'source_line': row[1], 'source_text': row[2],
                'sink_file':   row[3], 'sink_line':   row[4], 'sink_text':   row[5],
            })
        result['flows'] = flows
        result['status'] = 'ok'
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
        result['error'] = f'exceeded {timeout}s'
    except Exception:
        result['status'] = 'exception'
        result['error'] = traceback.format_exc()[-2000:]
    finally:
        if bqrs_path and os.path.exists(bqrs_path):
            os.remove(bqrs_path)
        result['elapsed_s'] = round(time.time() - t0, 2)

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-root', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--workers', type=int, default=50)
    parser.add_argument('--timeout', type=int, default=180,
                         help='Per-database hard timeout in seconds for the query itself '
                              '(default 180s — two-tier strategy: run the bulk at this timeout, '
                              'then use --retry-manifest with a HIGHER --timeout for only the '
                              'databases that timed out)')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--retry-manifest', default=None,
                         help='Path to a prior codeql_flows_*.json output — if given, ONLY the '
                              'extensions whose status was "timeout" there are re-queried. Output '
                              'is written to --out as given (choose a distinct path yourself, '
                              'e.g. codeql_flows_ina_retry.json), so the original is never '
                              'overwritten — merge results yourself once satisfied.')
    args = parser.parse_args()

    db_root = args.db_root
    ext_ids = sorted(d for d in os.listdir(db_root) if os.path.isdir(os.path.join(db_root, d)))

    if args.retry_manifest:
        prior = json.loads(Path(args.retry_manifest).read_text())
        timed_out_ids = {r['extension_id'] for r in prior['per_extension_results']
                          if r['status'] == 'timeout'}
        ext_ids = [e for e in ext_ids if e in timed_out_ids]
        print(f"Retry mode: {len(ext_ids):,} database(s) that timed out in "
              f"{args.retry_manifest} (out of {len(timed_out_ids):,} recorded there).")

    if args.limit:
        ext_ids = ext_ids[:args.limit]

    print(f"Databases found under {db_root}: {len(ext_ids):,}")
    print(f"Query: {args.query}  |  Workers: {args.workers}  |  Per-DB timeout: {args.timeout}s\n")

    tasks = [(ext_id, os.path.join(db_root, ext_id), args.query, args.timeout)
             for ext_id in ext_ids]

    results = []
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, t): t[0] for t in tasks}
        n_done = 0
        for fut in as_completed(futures):
            ext_id = futures[fut]
            try:
                r = fut.result()
            except Exception:
                r = {'extension_id': ext_id, 'status': 'worker_exception',
                     'error': traceback.format_exc()[-2000:], 'elapsed_s': None, 'flows': []}
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
        print(f"\n{n_timeout} extension(s) exceeded the {args.timeout}s query timeout — "
              f"recorded explicitly, not silently dropped. Report as a known, disclosed "
              f"coverage gap in the denominator, same as build-phase timeouts.")

    extensions_with_flow = [r['extension_id'] for r in results
                             if r['status'] == 'ok' and r['flows']]
    total_flows_raw = sum(len(r['flows']) for r in results if r['status'] == 'ok')
    # Deduplicated by (sink_file, sink_line) per extension — CodeQL's path-sensitive
    # tracking reports one row per distinct SOURCE reaching a sink, so a single sink
    # call site fed by multiple source expressions (e.g. `el`, `el.getAttribute(...)`,
    # and a derived var, all eventually reaching the same `fetch(url)` call) inflates
    # the raw count without indicating additional distinct vulnerable locations.
    # Confirmed on real corpus data this session (e.g. one extension: same tainted
    # variable reaching 4 different fetch() call sites = 4 raw rows, which IS 4 distinct
    # sink locations and is fine; but ALSO multiple source expressions reaching the SAME
    # sink line = redundant rows for one real location). Report both — raw is an upper
    # bound on distinct-location count, deduped is the more conservative number.
    total_flows_deduped = 0
    for r in results:
        if r['status'] != 'ok':
            continue
        seen_sinks = {(f['sink_file'], f['sink_line']) for f in r['flows']}
        total_flows_deduped += len(seen_sinks)

    print(f"\nExtensions successfully queried: {status_counts.get('ok', 0):,}")
    print(f"Extensions with >=1 CodeQL-confirmed flow: {len(extensions_with_flow):,}")
    print(f"Total CodeQL-confirmed flows — raw (one row per distinct source->sink path, "
          f"NOT directly comparable to the hand-rolled extractors' counts): {total_flows_raw:,}")
    print(f"Total CodeQL-confirmed flows — deduped by (sink_file, sink_line) per "
          f"extension (comparable unit to the hand-rolled extractors): {total_flows_deduped:,}")

    out = {
        'db_root': db_root,
        'query': args.query,
        'n_databases': len(ext_ids),
        'timeout_s': args.timeout,
        'n_workers': args.workers,
        'total_elapsed_s': round(total_elapsed, 1),
        'status_counts': status_counts,
        'n_extensions_queried_ok': status_counts.get('ok', 0),
        'n_extensions_with_flow': len(extensions_with_flow),
        'total_flows_raw': total_flows_raw,
        'total_flows_deduped_by_sink_location': total_flows_deduped,
        'extensions_with_flow': sorted(extensions_with_flow),
        'per_extension_results': results,
        'note': (
            'CodeQL-based static taint confirmation — corpus-scale run. Uses '
            'ext_taint_locations.ql (validated in CODEQL_FEASIBILITY_TEST.md / '
            'TAINT_SCOPE_COLLISION_FINDINGS.md against 3 synthetic cases: correctly finds '
            'a real interprocedural flow the hand-rolled scoped extractor misses, correctly '
            'rejects a cross-scope name-collision false positive the hand-rolled original '
            'extractor wrongly flags). Databases were built ONLY from signal-relevant files '
            '(CS-only for INA, WAR-only for SNA, via codeql_select_files.py) — cross-component '
            'flows (CS->WAR via postMessage, CS->BG via chrome.runtime.sendMessage) are '
            'captured by treating those calls as SINKS in the query itself, not by including '
            'the receiving component\'s file in the same database. Any extension with a '
            '"timeout" status in the build or query phase is EXCLUDED from this count and '
            'should be reported as a disclosed coverage gap, not silently folded into a lower '
            'denominator.'
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
