"""Topic extraction pipeline.

Lightweight topic extraction tailored for short user reviews:

- TF-IDF (uni/bi-grams)
- MiniBatchKMeans with a small K heuristic
- Topic labels from centroid top TF-IDF terms

Notes
-----
This keeps dependencies small and runtime quick. Heavier engines
(BERTopic / KeyBERT) are out of scope for this prototype and listed
in the README roadmap.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class Topic:
    """Container for a discovered topic."""

    id: int
    label: str
    top_terms: list[str]
    size: int


def _choose_k(n_docs: int) -> int:
    """Return a small, sensible number of clusters for short reviews."""
    if n_docs < 50:
        return 3
    if n_docs < 150:
        return 5
    if n_docs < 400:
        return 7
    return 9


def extract_topics(  # pylint: disable=too-many-locals
    texts: list[str],
    language: str = "english",
    topk: int = 8,
    min_docs: int = 2,
) -> tuple[list[Topic], dict[int, list[int]]]:
    """Extract topics from short review texts.

    Parameters
    ----------
    texts : list[str]
        Review texts.
    language : str
        Language stopword hint for TF-IDF.
    topk : int
        Number of top terms per topic label.
    min_docs : int
        Minimum documents required for a topic to be kept.

    Returns
    -------
    tuple[list[Topic], dict[int, list[int]]]
        topics : list of Topic dataclasses
        buckets : dict mapping topic_id → document indices
    """
    if not texts:
        return [], {}

    # Adjust thresholds dynamically for very small corpora
    dynamic_min_df = 1 if len(texts) < 5 else 2
    dynamic_max_df = 0.9

    vectorizer = TfidfVectorizer(
        stop_words=language,
        ngram_range=(1, 2),
        min_df=dynamic_min_df,
        max_df=dynamic_max_df,
        lowercase=True,
    )
    tfidf_matrix = vectorizer.fit_transform(texts)

    if tfidf_matrix.shape[0] == 0 or tfidf_matrix.shape[1] == 0:
        return [], {}

    # Determine cluster count safely
    k = _choose_k(tfidf_matrix.shape[0])
    k = max(1, min(k, tfidf_matrix.shape[0]))

    km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = km.fit_predict(tfidf_matrix)

    # Collect documents per cluster
    buckets: dict[int, list[int]] = {}
    for i, label in enumerate(labels):
        buckets.setdefault(int(label), []).append(i)

    # Build topic labels from top centroid features
    topics: list[Topic] = []
    terms = np.array(vectorizer.get_feature_names_out())
    for label, idxs in sorted(buckets.items()):
        if len(idxs) < min_docs:
            continue
        centroid = km.cluster_centers_[label]
        top_idx = np.argsort(centroid)[::-1][:topk]
        top_terms = [str(term) for term in terms[top_idx]]
        label_text = ", ".join(top_terms[:3])
        topics.append(
            Topic(id=int(label), label=label_text, top_terms=top_terms, size=len(idxs))
        )

    return topics, buckets
