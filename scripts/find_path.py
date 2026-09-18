import csv, heapq
from collections import defaultdict

import os
base = os.path.expanduser("~/mnt/RICON_to_geospatial")
edges = []
with open(f"{base}/EdgeList.csv") as f:
    r = csv.DictReader(f)
    for row in r:
        edges.append(row)

adj = defaultdict(list)
for e in edges:
    w = float(e["EDGE_LENGTHKM"])
    adj[e["FROM_NODE"]].append((e["TO_NODE"], w))
    adj[e["TO_NODE"]].append((e["FROM_NODE"], w))  # undirected fallback

def dijkstra(src, dst):
    dist = {src: 0.0}
    prev = {}
    pq = [(0.0, src)]
    seen = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen: continue
        seen.add(u)
        if u == dst: break
        for v, w in adj[u]:
            nd = d + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    if dst not in dist:
        return None, None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    path.reverse()
    return dist[dst], path

d, path = dijkstra("Point.820", "Point.339")
print("Glen Canyon (Point.820) -> Hoover (Point.339)")
print("distance km:", d)
print("num edges:", None if path is None else len(path)-1)
print("path:", path)
