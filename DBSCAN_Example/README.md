# DBSCAN model walkthrough

A short, runnable notebook that demonstrates how to build and inspect a DBSCAN clustering model with a two-dimensional dataset.

## Run it

```bash
python3 -m pip install -r requirements.txt
jupyter notebook DBSCAN_tutorial.ipynb
```

Run every cell, then change `EPS` or `MIN_SAMPLES` and rerun cells 12–19 to see how the model changes.

## What the model does

DBSCAN groups points by local density instead of requiring a chosen number of clusters.

- `eps` is the radius of a point's neighborhood.
- `min_samples` is the minimum number of points in that neighborhood, including the point itself, required for a core point.
- A cluster grows through connected core points; reachable non-core points become border points.
- Points not assigned to a cluster are noise and have label `-1`.

The supplied baseline (`eps=0.6`, `min_samples=5`) is a starting hypothesis for this dataset, not a universally correct setting. `eps` is sensitive to feature scale, so standardize inputs when features use incompatible units.
