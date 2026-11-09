import argparse
import json
from pathlib import Path
import pandas as pd
from causal_lab.estimators import analyze
from causal_lab.did import simulation


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("data/criteo_sample.parquet"))
    p.add_argument("--output", type=Path, default=Path("evidence"))
    a = p.parse_args()
    result = analyze(pd.read_parquet(a.input))
    result["did_separate_simulation"] = simulation()
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / "causal_results.json").write_text(json.dumps(result, indent=2))
    pd.DataFrame(result["effect_calibration"]).to_csv(a.output / "cate_calibration.csv", index=False)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c = pd.DataFrame(result["effect_calibration"])
    plt.errorbar(
        c.quintile,
        c.estimate,
        yerr=[c.estimate - c.ci95.map(lambda x: x[0]), c.ci95.map(lambda x: x[1]) - c.estimate],
        fmt="o",
        label="Held-out HT estimate (95% CI)",
    )
    plt.plot(c.quintile, c.predicted_cate, label="Predicted CATE")
    plt.axhline(0, color="gray")
    plt.xlabel("Exploratory T-learner quintile")
    plt.ylabel("Incremental visit probability")
    plt.legend()
    plt.tight_layout()
    plt.savefig(a.output / "cate_calibration.png", dpi=160)
    print(json.dumps({"n": result["n"], "ab": result["ab"], "aipw": result["aipw"]}, indent=2))


if __name__ == "__main__":
    main()
