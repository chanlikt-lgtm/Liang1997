#!/usr/bin/env python3
"""Sample the dphi/Gmax convergence trend from a trioRphi log every 50 iters,
append the latest milestone to a CSV, and print a one-line classification.

Usage: python src/trend_snapshot.py [--log logs/trioRphi_100x70.log]
"""
import re, os, sys, csv, argparse

REF = {
    '71x58': 3.075619e25,
    '100x70': 2.136180e25,
    '141x85': 2.387429e25,
}

def parse(log):
    rows = []
    for line in open(log):
        m = re.search(r'outer (\d+)\s+dphi=([0-9.e+-]+).*?Gmax=([0-9.e+-]+)', line)
        if m:
            rows.append((int(m.group(1)), float(m.group(2)), float(m.group(3))))
    return rows

def milestones(rows, step=50):
    out, seen = [], set()
    for it, dphi, g in rows:
        if it % step == 0 and it not in seen:
            seen.add(it); out.append((it, dphi, g))
    if rows and rows[-1][0] not in [o[0] for o in out]:
        out.append(rows[-1])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', default='logs/trioRphi_100x70.log')
    ap.add_argument('--csv', default='logs/trioRphi_trend.csv')
    args = ap.parse_args()

    rows = parse(args.log)
    if not rows:
        print('NO_DATA'); return 0
    ms = milestones(rows)

    # identify node from log filename
    tag = os.path.basename(args.log).replace('trioRphi_', '').replace('.log', '')
    ref = REF.get(tag)

    # append last milestone to CSV
    new = False
    fieldnames = ['tag', 'iter', 'dphi', 'Gmax']
    existing = []
    if os.path.exists(args.csv):
        with open(args.csv) as f:
            existing = list(csv.DictReader(f))
    last_iter = -1
    if existing:
        same = [int(r['iter']) for r in existing if r.get('tag') == tag]
        if same:
            last_iter = max(same)
    with open(args.csv, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not existing:
            w.writeheader()
        for it, dphi, g in ms:
            if it > last_iter:
                w.writerow({'tag': tag, 'iter': it, 'dphi': f'{dphi:.6e}', 'Gmax': f'{g:.6e}'})
                new = True

    it, dphi, g = rows[-1]
    # classification signals
    # downward dphi trend over last 3 milestones?
    dphi_vals = [m[1] for m in ms[-3:]]
    g_vals = [m[2] for m in ms[-3:]]
    dphi_down = dphi_vals[-1] < dphi_vals[0] and len(dphi_vals) >= 2
    g_climb = g_vals[-1] > g_vals[0] and len(g_vals) >= 2

    if ref:
        rel = (g - ref) / ref * 100
        print(f'{tag} iter={it} dphi={dphi:.3e} Gmax={g:.3e} ({rel:+.2f}% vs ref {ref:.4e}) '
              f'dphi_last3={"down" if dphi_down else "flat/up"} g_last3={"up" if g_climb else "flat/down"}')
    else:
        print(f'{tag} iter={it} dphi={dphi:.3e} Gmax={g:.3e}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
