# MGViz local work log (no remote push)

Track in-progress work here until GitHub is available again.
Prefer **local git commits** for durable history; this file is a human summary.

Last updated: 2026-08-24

## How to save progress without push

```bash
cd /home/jpldev/MGViz
git add -p   # or git add <specific files>
git commit -m "Describe why"
# later, when GitHub works:
git push
```

Optional backup patch (does not replace commits):

```bash
git diff HEAD -- \
  .cursorignore \
  private/eseses/earthquake_vectors.py \
  src/essence/Basics/Map_/Map_.js \
  src/essence/MMGIS-Private-Tools/Velocities/VelocitiesTool.js \
  > /home/sking/mgviz-wip-$(date +%Y%m%d).patch
```

## Related to Vector tool / coseismic work

### Done
- **Step 1** — `Map_.js`: `displacementExaggeration` / `displacementFilter`; Vectors layer uses them; ≥20 mm display hide.
- **Step 2** — `VelocitiesTool.js`: Velocities | Displacements tabs; Velocities options unchanged (Source, Direction, Display, Exaggeration); Displacements has Display + Exaggeration only.
- **`earthquake_vectors.py`**: direct `.neu` Filter/Clean Detrend parse (no per-site site.py); TODO to rename `*_vel` → `*_disp` later.
- **`.cursorignore`**: allow Cursor to edit `MMGIS-Private-Tools` / Private-Backend (commented ignore lines).

### Done — Dedicated Earthquakes toolbar tool
- **Step 1** — `066db45` scaffold.
- **Step 2** — `f47af2f` event/vector load path + site select without opening Chart.
- **Step 3** — `ac70079` Chart label Saved → Selected (centered).
- **Step 4** — `24ff39b` Chart coseismic UI removed; Velocities velocity-only.
- **Step 5** — `79ced7c` Map earthquake click → Earthquakes tool.
- **Legend / scale / vertical** — Vectors legend green `#2ea043`; on-map displacement scale (20/50/100 mm) after Earthquakes load; Direction H/V with orange vertical arrows (`arrows-disp-orange`).

Still out of scope: `*_vel` → `*_disp` rename.

### Still planned (later)
- `*_vel` → `*_disp` rename

### Other modified files on branch (may be unrelated / earlier WIP)
Check with `git status` / `git diff` before committing:
- `private/eseses/db/create_coseismic.sql`
- `private/eseses/db/create_site_coseismic.sql`
- `private/eseses/sioCron.sh`
- `private/eseses/site.py`
- `private/eseses/timeseries.py`
- `scripts/server.js`

Do **not** commit untracked tarballs, `build-*`, `*.tar.gz`, or large data dumps.
