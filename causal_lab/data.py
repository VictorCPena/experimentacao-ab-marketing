"""Unbiased Bernoulli sample over the complete Criteo v2.1 file."""

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from causal_lab.fetch import download

URL = "https://huggingface.co/datasets/criteo/criteo-uplift/resolve/main/criteo-research-uplift-v2.1.csv.gz"


def sample(path: Path, output: Path, fraction=0.01, seed=42):
    if not 0 < fraction <= 1:
        raise ValueError("Sampling fraction must be in (0,1]")
    rng = np.random.default_rng(seed)
    selected, seen = [], 0
    for chunk in pd.read_csv(path, chunksize=200_000):
        keep = rng.random(len(chunk)) < fraction
        chunk["unit_id"] = np.arange(seen, seen + len(chunk))
        selected.append(chunk.loc[keep])
        seen += len(chunk)
    result = pd.concat(selected, ignore_index=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    manifest = {
        "url": URL,
        "source_rows": seen,
        "sample_rows": len(result),
        "fraction": fraction,
        "seed": seed,
        "sampling": "Bernoulli over all rows, no outcome filtering",
        "source_sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest(),
        "sample_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "license": "CC-BY-NC-SA-4.0",
        "version": "Criteo unbiased v2.1",
    }
    output.with_suffix(".json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path)
    p.add_argument("--output", type=Path, default=Path("data/criteo_sample.parquet"))
    a = p.parse_args()
    raw = a.input or Path("data/raw/criteo.csv.gz")
    if not raw.exists():
        download(URL, raw)
    print(json.dumps(sample(raw, a.output), indent=2))
