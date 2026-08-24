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

### In progress — Dedicated Earthquakes toolbar tool
- **Step 1 (done, committed `066db45`)** — scaffold `Earthquakes/` + enable in configure.
- **Step 2 (ready to review)** — Earthquakes owns event list, Vector source (`clean`/`detrend`), Display/Exaggeration, Clear (vectors + selection), site magenta + `ChartTool.previousSites` without opening Chart (`SearchTool` `skipOpenChart`).
- Next: slim Chart/Velocities; rewire map earthquake click; rename Saved→Selected.

### Still planned (later / out of scope for Earthquakes tool)
- On-map 50 mm displacement scale
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
