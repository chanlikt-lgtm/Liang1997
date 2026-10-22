#!/usr/bin/env python3
"""Read-only archival-evidence validator for the Liang1997 controlled SHE trio.

Usage: python Liang1997_Readonly_Checkpoints.py --repo /path/to/Liang1997 --json audit.json

Does NOT run the 26-40 hour solver, modify the repo, or validate the 1997 paper.
It independently evaluates the saved four-REAL-iteration cross-chunk plateau
windows, comparability metadata, archival deviations, and report freshness.

Audited against the PUBLIC SOURCE SCHEMA on 2026-10-22, but not executed on the
actual GitHub NPZs (the archive could not be fetched in this environment).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

try:
    import numpy as np
except ImportError:
    sys.exit("ERROR: numpy required (python -m pip install numpy)")

NODES = ((71,58), (100,70), (141,85))
ARCH_G = (2.990e25, 2.135e25, 2.413e25)
SPREAD_MAX = 3e-4
RPHI_MAX = 1.5e-3
REFINE_RATIO = math.sqrt(2)
RATIO_TOL = 0.05
PARITY_TOL = 0.02

def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def scalar(z, key, conv=float):
    if key not in z.files:
        raise ValueError(f"required NPZ key absent: {key}")
    return conv(np.asarray(z[key]).item())

def get_commit(root):
    try:
        sha = subprocess.check_output(['git','rev-parse','HEAD'], cwd=str(root), stderr=subprocess.DEVNULL, timeout=4).decode().strip()
        dirty = bool(subprocess.check_output(['git','status','--porcelain'], cwd=str(root), stderr=subprocess.DEVNULL, timeout=4).strip())
        return sha, dirty
    except Exception:
        return None, None

def check_repo(root: pathlib.Path):
    out = dict(program='Liang1997 read-only checkpoint validator',
               inspected_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'),
               repo=str(root), nodes=[], checks=[], warnings=[],
               claim='Data/integrity diagnostics only; NOT paper validation or spatial convergence.')
    errors, warns = [], out['warnings']
    def record(name, ok, reason, critical=True):
        out['checks'].append(dict(name=name, passed=bool(ok), detail=reason))
        if not ok:
            (errors if critical else warns).append(f"{name}: {reason}")
    commit, dirty = get_commit(root)
    out['git'] = {'head':commit,'dirty':dirty}
    record('Git revision discoverable', commit is not None, 'Full Git SHA is recorded' if commit else 'git unavailable or not a clone', False)
    if dirty is True:
        record('Source tree clean', False, 'Working tree contains modifications; do not treat this as frozen comparable run', False)
    elif dirty is False:
        record('Source tree clean', True, 'Git tree clean')

    for f in ('src/plateau_gate.py', 'src/run_richardson_trio.py', 'src/gen_run_report.py',
              'src/richardson_fit.py','report/report_v6_full.tex'):
        record(f'Exists {f}', (root/f).is_file(), 'Found' if (root/f).is_file() else 'Missing file', False)

    profiles = []
    for (nx,ny), archa in zip(NODES, ARCH_G):
        node = f'{nx}x{ny}'
        nfile = root/'data'/f'she2d_richardson_{node}.npz'
        jfile = root/'data'/f'she2d_richardson_{node}.progress.json'
        entry = {'node':node,'npz':str(nfile.relative_to(root)),
                 'sidecar':str(jfile.relative_to(root))}
        out['nodes'].append(entry)
        if not nfile.is_file() or not jfile.is_file():
            record(f'{node} mandatory artifacts',False, f'npz_exists={nfile.is_file()}, sidecar_exists={jfile.is_file()}')
            continue
        entry['sha256_npz']=sha256(nfile)
        entry['sha256_sidecar']=sha256(jfile)
        try:
            with np.load(nfile, allow_pickle=False) as z:
                nxv,nyv = scalar(z,'Nx',int),scalar(z,'Ny',int)
                g,gt = scalar(z,'Gii_max'),scalar(z,'G_tot')
                dx = scalar(z,'drain_dx')
                rphi = scalar(z,'R_phi')
                hhash = scalar(z,'H_hash',str)
                sig = tuple((k,scalar(z,k)) for k in ('ratio','W','X_C','dH_eV','NH','she_tol'))
                entry.update(Gii=g,Gtot=gt,Rphi=rphi,drain_dx=dx,H_hash=hhash,
                             signature=dict(sig),abs_dev_pct=100*(g-archa)/archa)
                for opt in ('Phi_gate','surface_dy','eps_max','git_commit'):
                    if opt in z.files:
                        entry[opt]=scalar(z,opt,str if opt=='git_commit' else float)
            with jfile.open(encoding='utf-8') as fh:
                progress=json.load(fh)
            buf=progress.get('plateau_buffer',[])
            iters=[int(s['abs_iter']) for s in buf]
            good_iters = len(iters)==4 and len(set(iters))==4 and all(iters[i]+1==iters[i+1] for i in range(3))
            record(f'{node} four real consecutive samples',good_iters, f'abs_iters={iters!r}')
            if not good_iters:
                continue
            g4=np.asarray([float(s['Gii']) for s in buf])
            gt4=np.asarray([float(s['Gtot']) for s in buf])
            r4=np.asarray([float(s['Rphi']) for s in buf])
            if np.any(~np.isfinite(g4)) or np.any(~np.isfinite(gt4)) or np.any(g4<=0) or np.any(gt4<=0):
                record(f'{node} finite positive observables',False,'NaN/Inf/non-positive in certified history')
                continue
            spg=float(np.ptp(g4)/np.mean(g4))
            spt=float(np.ptp(gt4)/np.mean(gt4))
            ug=float(np.ptp(g4)/2)
            entry.update(plateau_spread_Gii=spg,plateau_spread_Gtot=spt,uncertainty_half_range=ug,
                         last_Rphi=float(r4[-1]),certified_iters=iters)
            record(f'{node} sidecar matches final NPZ',math.isclose(g4[-1],g,rel_tol=1e-6) and math.isclose(gt4[-1],gt,rel_tol=1e-6),
                   f'last_Gii={g4[-1]:.8e}, saved_Gii={g:.8e}, last_Gtot={gt4[-1]:.8e}, saved_Gtot={gt:.8e}')
            record(f'{node} sidecar integrity',bool(progress.get('passed')) and int(progress.get('cum_iters',-1))==iters[-1],
                   f'passed={progress.get("passed")}, cum_iters={progress.get("cum_iters")}, last_sample={iters[-1]}')
            record(f'{node} plateau criterion',spg<=SPREAD_MAX and spt<=SPREAD_MAX and r4[-1]<=RPHI_MAX,
                   f'spread_Gii={spg:.3e}, spread_Gtot={spt:.3e}, last_Rphi={r4[-1]:.3e}')
            record(f'{node} NPZ metrics finite', all(map(math.isfinite,[g,gt,dx,rphi])) and g>0 and gt>0 and dx>0,
                   f'Gii={g:.6e}, Gtot={gt:.6e}, dx={dx:.6g}, Rphi={rphi:.3e}')
            profiles.append(entry)
        except Exception as exc:
            record(f'{node} load and schema',False,f'{type(exc).__name__}: {exc}')
    if len(profiles)==3:
        hh=[p['H_hash'] for p in profiles]
        record('All three H grid hashes equal and mandatory',len(set(hh))==1 and all(x and x!='?' for x in hh),repr(hh))
        signatures=[p['signature'] for p in profiles]
        record('All six declared physics/grid parameters comparable',all(signatures[i]==signatures[0] for i in (1,2)),repr(signatures))
        extra_fields=set.intersection(*(set(p.keys()) for p in profiles))
        for extra in ('Phi_gate','eps_max'):
            if extra in extra_fields:
                record(f'All nodes {extra} equal',len(set(p[extra] for p in profiles))==1,repr([p[extra] for p in profiles]))
            else:
                record(f'All nodes contain {extra}',False,f'Optional schema field {extra} absent from one or more nodes; freeze from external config digest',False)
        dx=[p['drain_dx'] for p in profiles]
        ratios=[dx[0]/dx[1],dx[1]/dx[2]]
        out['refinement_ratios']=ratios
        record('Drain mesh refinement ratio',all(abs(r-REFINE_RATIO)<RATIO_TOL for r in ratios),f'ratios={ratios} target={REFINE_RATIO:.6f}')
        G=[p['Gii'] for p in profiles]
        signs=[math.copysign(1,G[0]-G[1]),math.copysign(1,G[1]-G[2])]
        nonmono=signs[0]!=signs[1]
        out['nonmonotone_Gii']=nonmono
        out['richardson_extrapolation_allowed']=False if nonmono else None
        u=[p['uncertainty_half_range'] for p in profiles]
        den=math.hypot(u[1],u[2])
        out['S_rev_certified_window']=abs(G[1]-G[2])/den if nonmono and den>0 else ('unbounded (zero numerical half-range)' if nonmono else None)
        out['archival_parity']='GREEN numerically' if all(abs(p['abs_dev_pct'])<100*PARITY_TOL for p in profiles) else 'YELLOW numerically'
        out['scientific_status']='NOT SPATIALLY CONVERGED' if nonmono else 'SPATIAL STATUS NEEDS A LARGER GRID STUDY'
        record('Archival ±2% numerical parity',all(abs(p['abs_dev_pct'])<100*PARITY_TOL for p in profiles),
               repr([(p['node'],round(p['abs_dev_pct'],4)) for p in profiles]),False)
        record('No Richardson for nonmonotone sequence',True,
               'Scientific status computed independently from certified Gii values; no continuum Gii inferred')
    report = root/'report'/'report_run_latest.pdf'
    out['run_report']={'exists':report.is_file()}
    if report.is_file():
        out['run_report'].update(sha256=sha256(report),size_bytes=report.stat().st_size)
        if len(profiles)==3:
            fresh=report.stat().st_mtime>=max((root/p['npz']).stat().st_mtime for p in profiles)
            record('Report PDF newer than NPZ inputs',fresh,'PDF mtime must postdate all inputs; source hashes still required',False)
    else:
        record('Auto-run PDF exists',False,'report/report_run_latest.pdf absent or LaTeX not installed',False)
    out['errors']=errors
    out['overall']='FAIL' if errors else ('INCOMPLETE' if len(profiles)!=3 else 'INTERNAL CHECKS PASS — PAPER VALIDATION NOT CLAIMED')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=pathlib.Path,default=pathlib.Path('.'))
    p.add_argument('--json',type=pathlib.Path,help='write audit results outside repository')
    a=p.parse_args()
    root=a.repo.expanduser().resolve()
    result=check_repo(root)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(json.dumps(result,indent=2,allow_nan=False,default=str),encoding='utf-8')
    print('Liang1997 evidence audit:',result['overall'])
    print('Source Git commit:',result['git']['head'] or 'UNKNOWN')
    for e in result['nodes']:
        print(' ',e['node'],'Gii=',e.get('Gii','missing'),'cert_window=',e.get('certified_iters','missing'))
    for c in result['checks']:
        if not c['passed']:
            print(' ', 'FAIL',c['name'],'—',c['detail'])
    print('Scientific status:',result.get('scientific_status','not assessable'))
    print('NOTE: This validates file-level evidence only, not correctness versus Liang 1997.')
    return 1 if result['errors'] else (2 if len(result['nodes'])!=3 or any('Gii' not in n for n in result['nodes']) else 0)

if __name__=='__main__':
    sys.exit(main())
