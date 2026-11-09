"""Real county employment panel, single 2006 cohort vs never-treated counties."""

import argparse
import json
from pathlib import Path
import numpy as np
import statsmodels.formula.api as smf
from causal_lab.fetch import download

URL = "https://raw.githubusercontent.com/bcallaway11/did/master/data/mpdta.rda"


def analyze(path):
    import pyreadr

    original = pyreadr.read_r(str(path))["mpdta"]
    frame = original[original["first.treat"].isin([0, 2006])].copy()
    frame["treated"] = (frame["first.treat"] == 2006).astype(int)
    frame["state"] = (frame.countyreal // 1000).astype(int)
    subset = frame[frame.year.isin([2005, 2006])].copy()
    subset["post"] = (subset.year == 2006).astype(int)
    # Assignment at state level. County-clustered SE would understate shared state shocks.
    model = smf.ols("lemp ~ treated * post", subset).fit(
        cov_type="cluster", cov_kwds={"groups": subset.state}
    )
    means = frame.groupby(["treated", "year"]).lemp.mean().unstack(0)
    placebo = []
    for year in (2004, 2005):
        change = means.loc[year] - means.loc[year - 1]
        placebo.append({"end_year": year, "preperiod_difference_in_changes": float(change[1] - change[0])})
    return {
        "dataset": "did::mpdta, Callaway & Sant Anna (2021)",
        "source_url": URL,
        "real_data": True,
        "rows": len(subset),
        "counties": int(subset.countyreal.nunique()),
        "states": int(subset.state.nunique()),
        "treated_states": sorted(subset.loc[subset.treated == 1, "state"].unique().tolist()),
        "estimand": "2006 cohort ATT in log teen employment, 2005 to 2006 vs never treated, unconditional parallel trends",
        "estimate_log_points": float(model.params["treated:post"]),
        "approx_percent": float(100 * np.expm1(model.params["treated:post"])),
        "conventional_state_cluster_ci95_NOT_confirmatory": model.conf_int().loc["treated:post"].tolist(),
        "preperiod_placebos": placebo,
        "interpretation": "Conditional DiD estimate, not a certified causal policy finding. Only 3 treated states; conventional cluster confidence interval is not reliable for confirmatory inference. Pre-period placebo differences can flag problems, not prove parallel trends.",
        "assumptions": [
            "No anticipation",
            "Unconditional parallel trends",
            "No interstate spillovers",
            "Stable county composition",
        ],
        "limits": [
            "State-level effective sample much smaller than county count",
            "No wild-cluster or randomization inference validated",
            "No staggered TWFE across cohorts",
            "Other time-varying policies unadjusted",
            "Package distributes data under GPL (>=2); upstream attribution retained; no data resold",
        ],
        "mean_paths": means.reset_index()
        .rename(columns={0: "control", 1: "treated"})
        .to_dict(orient="records"),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("data/raw/mpdta.rda"))
    a = p.parse_args()
    if not a.input.exists():
        download(URL, a.input, 10_000_000)
    r = analyze(a.input)
    Path("evidence/real_did.json").write_text(json.dumps(r, indent=2))
    print(json.dumps(r, indent=2))
