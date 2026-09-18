import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

base = os.path.expanduser("~/mnt/RICON_to_geospatial")

path = ['Point.820', 'Point.09379910', 'Point.09380000', 'Point.09380002', 'Point.09383000',
        'Point.09383100', 'Point.09402500', 'Point.09402501', 'Point.09404120', 'Point.09404200', 'Point.339']
path_edges = set(zip(path[:-1], path[1:])) | set(zip(path[1:], path[:-1]))

coords = {}
ptype = {}
for fn in (f"{base}/nid_df.csv", f"{base}/sites_df.csv"):
    with open(fn) as f:
        for row in csv.DictReader(f):
            coords[row["IDS"]] = (float(row["LONGITUDE"]), float(row["LATITUDE"]))
            ptype[row["IDS"]] = row["POINTTYPE"]

node_ids = list(coords.keys())
lons = np.array([coords[n][0] for n in node_ids])
lats = np.array([coords[n][1] for n in node_ids])
is_dam = np.array([ptype[n] == "dam" for n in node_ids])

edges_raw = []
with open(f"{base}/EdgeList.csv") as f:
    for row in csv.DictReader(f):
        a, b = row["FROM_NODE"], row["TO_NODE"]
        if a in coords and b in coords:
            on_path = (a, b) in path_edges
            edges_raw.append((coords[a], coords[b], on_path))

BG = "#0b1220"
INK = "#e8edf5"
MUTED = "#9aa7bd"
DAM_C = np.array(matplotlib.colors.to_rgb("#e8a33d"))
GAGE_C = np.array(matplotlib.colors.to_rgb("#5b8def"))
EDGE_C = np.array(matplotlib.colors.to_rgb("#6b7a99"))
PATH_C = "#e0507a"

N_NODE_FRAMES = 10
N_EDGE_FRAMES = 14
N_HOLD = 8
TOTAL = N_NODE_FRAMES + N_EDGE_FRAMES + N_HOLD

node_order = np.argsort(-lats)
node_reveal = np.empty(len(node_ids), dtype=int)
bucket_size = math.ceil(len(node_ids) / N_NODE_FRAMES)
for rank, idx in enumerate(node_order):
    node_reveal[idx] = min(rank // bucket_size, N_NODE_FRAMES - 1)

edge_mean_lat = [ (e[0][1] + e[1][1]) / 2 for e in edges_raw ]
edge_order = np.argsort(-np.array(edge_mean_lat))
edge_reveal = np.empty(len(edges_raw), dtype=int)
ebucket = math.ceil(len(edges_raw) / N_EDGE_FRAMES)
for rank, idx in enumerate(edge_order):
    edge_reveal[idx] = min(rank // ebucket, N_EDGE_FRAMES - 1)

segments = np.array([[e[0], e[1]] for e in edges_raw])
on_path_flags = np.array([e[2] for e in edges_raw])

fig, ax = plt.subplots(figsize=(8.2, 6.9), dpi=110)
fig.patch.set_facecolor(BG)
fig.subplots_adjust(top=0.85, bottom=0.13)
ax.set_facecolor(BG)
ax.set_xlim(lons.min() - 0.4, lons.max() + 0.4)
ax.set_ylim(lats.min() - 0.4, lats.max() + 0.4)
mean_lat = lats.mean()
ax.set_aspect(1.0 / math.cos(math.radians(mean_lat)))
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

fig.suptitle("Building the RICON connectivity graph — Colorado River Basin",
             color=INK, fontsize=12.5, fontweight="bold", family="sans-serif", y=0.965)
subtitle = fig.text(0.5, 0.885, "", ha="center", va="bottom",
                     color=MUTED, fontsize=9.3, family="monospace")

lc_bg = LineCollection([], linewidths=0.5, zorder=2)
ax.add_collection(lc_bg)
lc_path = LineCollection([], linewidths=2.4, zorder=4, color=PATH_C)
ax.add_collection(lc_path)

scat = ax.scatter(lons, lats, s=np.where(is_dam, 12, 7), zorder=3,
                   facecolors=np.zeros((len(lons), 4)), edgecolors="none")

legend_handles = [
    Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#e8a33d",
           markeredgecolor="none", markersize=7, label="dam"),
    Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="#5b8def",
           markeredgecolor="none", markersize=6, label="gauge"),
]
legend = ax.legend(handles=legend_handles, loc="upper left", frameon=False,
                    labelcolor=INK, fontsize=9.5, handletextpad=0.6,
                    borderaxespad=0.6)

path_mid_id = path[len(path) // 2]
anchor_xy = coords[path_mid_id]
path_ann = ax.annotate(
    "Glen Canyon Dam → Hoover Dam\n592.9 km, 10 routed edges",
    xy=anchor_xy, xycoords="data",
    xytext=(0.025, 0.635), textcoords="axes fraction",
    color=PATH_C, fontsize=9.3, fontweight="bold", family="sans-serif", ha="left",
    bbox=dict(boxstyle="round,pad=0.35", fc=BG, ec="none", alpha=0.85),
    arrowprops=dict(arrowstyle="-", color=PATH_C, linewidth=1.2, shrinkA=2, shrinkB=5,
                     connectionstyle="arc3,rad=0.12"),
    zorder=6, visible=False,
)

n_edges = len(edges_raw)

def frame_alpha_nodes(i):
    a = np.clip((i - node_reveal) / 2.0 + 1.0, 0, 1)
    return a

def frame_alpha_edges(i):
    j = i - N_NODE_FRAMES
    a = np.clip((j - edge_reveal) / 2.0 + 1.0, 0, 1)
    return a

def update(i):
    if i < N_NODE_FRAMES:
        na = frame_alpha_nodes(i)
        colors = np.where(is_dam[:, None], DAM_C, GAGE_C)
        rgba = np.concatenate([colors, na[:, None]], axis=1)
        scat.set_facecolors(rgba)
        subtitle.set_text(f"placing dams & gauges  ({int((na>0.99).sum())} / {len(lons)})")
    elif i < N_NODE_FRAMES + N_EDGE_FRAMES:
        ea = frame_alpha_edges(i)
        bg_mask = ~on_path_flags
        segs_bg = segments[bg_mask]
        rgba_bg = np.tile(np.append(EDGE_C, 1.0), (segs_bg.shape[0], 1))
        rgba_bg[:, 3] = ea[bg_mask] * 0.55
        lc_bg.set_segments(list(segs_bg))
        lc_bg.set_color(rgba_bg)
        shown = int((ea > 0.99).sum())
        subtitle.set_text(f"routing {n_edges:,} connectivity edges  ({shown:,} / {n_edges:,})")
    else:
        segs_bg = segments[~on_path_flags]
        rgba_bg = np.tile(np.append(EDGE_C, 0.35), (segs_bg.shape[0], 1))
        lc_bg.set_segments(list(segs_bg))
        lc_bg.set_color(rgba_bg)
        segs_path = segments[on_path_flags]
        lc_path.set_segments(list(segs_path))
        subtitle.set_text(f"routing {n_edges:,} connectivity edges  ({n_edges:,} / {n_edges:,})")
        k = i - (N_NODE_FRAMES + N_EDGE_FRAMES)
        if k >= 2:
            path_ann.set_visible(True)
    return scat, lc_bg, lc_path, subtitle, path_ann, legend

anim = animation.FuncAnimation(fig, update, frames=TOTAL, blit=False)
out = f"{base}/blog_assets/ricon_connectivity.gif"
anim.save(out, writer=animation.PillowWriter(fps=6))
print("saved", out)
