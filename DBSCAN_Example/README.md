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

## Model selection experiment

I applied DBSCAN to 179 unlabeled two-dimensional observations and compared three parameter choices. Cluster IDs are arbitrary identifiers; the visual structure and real-world context determine whether a result is useful.

| `eps` | `min_samples` | Clusters found | Noise points | Noise rate | Observation |
|---:|---:|---:|---:|---:|---|
| 0.6 | 5 | 3 | 10 | 5.6% | Baseline: one broad dense region and two smaller dense regions. |
| 0.6 | 8 | 3 | 27 | 15.1% | A stricter density threshold preserved the three regions but marked 17 more points as noise. |
| 0.4 | 5 | 5 | 35 | 19.6% | A smaller neighborhood radius split the upper-left region into smaller clusters and increased noise. |

I selected the baseline model, `eps=0.6` and `min_samples=5`, because it produced the simplest interpretable structure while retaining the most observations in clusters. This is a modeling decision rather than ground truth: if the smaller upper-left bands represent meaningful real-world groups, the five-cluster model may be more appropriate.

### Next model-building step

Test `eps=0.5` with `min_samples=5` as a middle ground. Record the cluster and noise counts, compare its plot with the three experiments above, and document the parameter choice using the real-world meaning of the two features.
