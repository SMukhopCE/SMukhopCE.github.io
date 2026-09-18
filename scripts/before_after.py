import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

base = os.path.expanduser("~/mnt/RICON_to_geospatial")

# path computed earlier: Glen Canyon (Point.820) -> Hoover (Point.339), 592.9 km, 10 edges
path = ['Point.820', 'Point.09379910', 'Point.09380000', 'Point.09380002', 'Point.09383000',
        'Point.09383100', 'Point.09402500', 'Point.09402501', 'Point.09404120', 'Point.09404200', 'Point.339']
path_set = set(path)

# load node coords + names + type
coords = {}
names = {}
ptype = {}
for fn, key_field in ((f"{base}/nid_df.csv", "dam"), (f"{base}/sites_df.csv", "gage")):
    with open(fn) as f:
        for row in csv.DictReader(f):
            coords[row["IDS"]] = (float(row["LONGITUDE"]), float(row["LATITUDE"]))
            names[row["IDS"]] = row["NAME"]
            ptype[row["IDS"]] = row["POINTTYPE"]

# load edges along the path, in order, with their real attributes
edge_rows = []
with open(f"{base}/EdgeList.csv") as f:
    r = csv.DictReader(f)
    lookup = {}
    for row in r:
        lookup[(row["FROM_NODE"], row["TO_NODE"])] = row
        lookup[(row["TO_NODE"], row["FROM_NODE"])] = row
for a, b in zip(path[:-1], path[1:]):
    edge_rows.append(lookup[(a, b)])

BG = "#0b1220"
INK = "#e8edf5"
MUTED = "#9aa7bd"
DAM_C = "#e8a33d"
GAGE_C = "#5b8def"
PATH_C = "#e0507a"

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6), dpi=200, gridspec_kw={"width_ratios": [1.05, 1]})
fig.patch.set_facecolor(BG)

axL = axes[0]
axL.set_facecolor(BG)
axL.axis("off")
axL.set_title("EdgeList.csv  (raw output)", color=INK, fontsize=12.5, fontweight="bold",
               family="monospace", loc="left", pad=14)

headers = ["FROM_NODE", "TO_NODE", "LENGTH_KM", "TYPE"]
col_x = [0.0, 0.30, 0.58, 0.80]
row_y0 = 0.86
row_h = 0.072

for cx, h in zip(col_x, headers):
    axL.text(cx, row_y0 + row_h, h, transform=axL.transAxes, color=MUTED, fontsize=8.3,
              family="monospace", fontweight="bold")
axL.plot([0, 1], [row_y0 + row_h - 0.02]*2, transform=axL.transAxes, color=MUTED, linewidth=0.8)

for i, e in enumerate(edge_rows):
    y = row_y0 - i * row_h
    type_str = f'{e["FROM_NODETYPE"]}\u2192{e["TO_NODETYPE"]}'
    vals = [e["FROM_NODE"], e["TO_NODE"], f'{float(e["EDGE_LENGTHKM"]):.2f}', type_str]
    for cx, v in zip(col_x, vals):
        axL.text(cx, y, v, transform=axL.transAxes, color=INK, fontsize=8.1, family="monospace")

total_km = sum(float(e["EDGE_LENGTHKM"]) for e in edge_rows)
axL.text(0.0, row_y0 - len(edge_rows) * row_h - 0.06,
          f"...3,092 rows total in the full file\nsum along this path: {total_km:.1f} km over {len(edge_rows)} edges",
          transform=axL.transAxes, color=MUTED, fontsize=8.6, family="monospace", va="top")

axR = axes[1]
axR.set_facecolor(BG)

xs_path = [coords[n][0] for n in path]
ys_path = [coords[n][1] for n in path]
xpad = (max(xs_path) - min(xs_path)) * 0.22
ypad = (max(ys_path) - min(ys_path)) * 0.18
axR.set_xlim(min(xs_path) - xpad, max(xs_path) + xpad * 2.4)
axR.set_ylim(min(ys_path) - ypad, max(ys_path) + ypad * 1.6)
axR.plot(xs_path, ys_path, color=PATH_C, linewidth=2.2, zorder=3, solid_capstyle="round")

for n in path:
    lon, lat = coords[n]
    color = DAM_C if ptype[n] == "dam" else GAGE_C
    axR.scatter([lon], [lat], s=46 if ptype[n] == "dam" else 30, color=color,
                edgecolor=BG, linewidth=0.6, zorder=4)

axR.annotate("Glen Canyon Dam", coords["Point.820"], color=INK, fontsize=9, fontweight="bold",
             family="sans-serif", ha="right", xytext=(-10, 6), textcoords="offset points")
axR.annotate("Hoover Dam", coords["Point.339"], color=INK, fontsize=9, fontweight="bold",
             family="sans-serif", ha="left", xytext=(10, 10), textcoords="offset points")

axR.set_title(f"same edges, rendered  ({total_km:.1f} km, {len(edge_rows)} edges)", color=INK,
               fontsize=12.5, fontweight="bold", family="monospace", loc="left", pad=14)
axR.set_xticks([]); axR.set_yticks([])
for spine in axR.spines.values():
    spine.set_color(MUTED)
    spine.set_linewidth(0.6)

legend_elems = [
    Line2D([0], [0], marker='o', color='none', markerfacecolor=DAM_C, markersize=7, label='dam'),
    Line2D([0], [0], marker='o', color='none', markerfacecolor=GAGE_C, markersize=6, label='gauge'),
    Line2D([0], [0], color=PATH_C, linewidth=2, label='routed edge'),
]
axR.legend(handles=legend_elems, loc="lower left", frameon=False, labelcolor=INK, fontsize=8.5)

fig.suptitle("From CSV rows to a real, mappable path (Glen Canyon Dam to Hoover Dam)",
             color=INK, fontsize=14, fontweight="bold", y=1.01)

plt.tight_layout()
out = f"{base}/blog_assets/before_after.png"
plt.savefig(out, facecolor=BG, bbox_inches="tight")
print("saved", out)
