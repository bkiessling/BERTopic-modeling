"""Framework-independent document projection."""

import numpy as np
from umap import UMAP
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA


def project_documents(embeddings, method="umap"):
    """Compute a deterministic layout independently of topic labels."""
    n_samples, n_features = embeddings.shape
    if method not in {"umap", "tsne"}:
        raise ValueError("Unbekannte Dimensionsreduktion.")
    if n_samples == 1 or np.allclose(embeddings, embeddings[0]):
        return np.zeros((n_samples, 2))
    if n_samples <= 3 or n_features < 2:
        result = PCA(n_components=min(2, n_samples, n_features)).fit_transform(embeddings)
        return np.pad(result, ((0, 0), (0, 2 - result.shape[1])))
    if method == "umap":
        reducer = UMAP(
            n_neighbors=min(10, n_samples - 1),
            n_components=2,
            min_dist=0.0,
            metric="cosine",
            random_state=42,
            n_jobs=1,
        )
    else:
        reducer = TSNE(
            n_components=2,
            perplexity=min(30, n_samples - 1),
            metric="cosine",
            random_state=42,
            init="random",
        )
    return reducer.fit_transform(embeddings)
