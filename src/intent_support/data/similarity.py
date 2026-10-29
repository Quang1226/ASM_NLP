"""Exact SequenceMatcher threshold search within each intent label."""

from __future__ import annotations

import bisect
import difflib
import math
from collections import defaultdict


class SimilarityIndex:
    def __init__(self, rows: list[dict[str, str]], threshold: float = 0.90):
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")
        self.threshold = threshold
        grouped: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            grouped[row["intent"]].append(row["instruction"].casefold())
        self.texts = {label: sorted(items, key=lambda item: (len(item), item)) for label, items in grouped.items()}
        self.lengths = {label: [len(item) for item in items] for label, items in self.texts.items()}

    def first_match(self, row: dict[str, str]) -> str | None:
        """Return a match if any same-intent source text reaches the threshold."""
        label = row["intent"]
        texts = self.texts.get(label, [])
        if not texts:
            return None
        text = row["instruction"].casefold()
        length = len(text)
        # A ratio >= t is impossible outside these length bounds. Floor/ceil
        # expand the range to avoid floating-point boundary exclusions.
        lower = math.floor(self.threshold * length / (2 - self.threshold))
        upper = math.ceil((2 - self.threshold) * length / self.threshold)
        lengths = self.lengths[label]
        start = bisect.bisect_left(lengths, lower)
        stop = bisect.bisect_right(lengths, upper)
        for other in texts[start:stop]:
            matcher = difflib.SequenceMatcher(None, text, other)
            if matcher.real_quick_ratio() < self.threshold:
                continue
            if matcher.quick_ratio() < self.threshold:
                continue
            if matcher.ratio() >= self.threshold:
                return other
        return None
