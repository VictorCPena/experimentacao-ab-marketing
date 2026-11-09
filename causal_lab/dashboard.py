import json
from pathlib import Path
import pandas as pd
import streamlit as st
from causal_lab.planning import required_per_arm

st.set_page_config(page_title="Causal Impact Lab", layout="wide")
st.title("Causal Impact & Experimentation Lab")
path = Path("evidence/causal_results.json")
if not path.exists():
    st.info("Run python -m causal_lab.demo first.")
    st.stop()
r = json.loads(path.read_text())
st.caption(f"Criteo v2.1 • {r['n']:,} sampled users • intention to treat")
metric = st.selectbox("Randomized outcome", list(r["ab"]))
st.caption(f"Unadjusted A/B outcome: {metric}. The selector applies only to this A/B result.")
st.json(r["ab"][metric])
primary_outcome = r.get("outcome", "visit")
st.subheader(f"Cross-fitted estimates — {primary_outcome}")
st.caption("Adjusted AIPW and the following targeting analyses use the fixed primary outcome.")
st.json(r["aipw"])
st.subheader(f"Held-out heterogeneous effects — {primary_outcome}")
st.dataframe(pd.DataFrame(r["effect_calibration"]))
st.subheader(f"Targeting comparison — {primary_outcome}")
st.json(r["comparison"])
st.subheader("Planning calculator")

baseline = st.slider("Baseline probability", 0.01, 0.5, 0.05, step=0.001, format="%.3f")
mde = st.slider("Minimum absolute effect", 0.001, 0.05, 0.005, step=0.001, format="%.3f")
st.caption(
    f"Control {baseline:.3%} → treatment {baseline + mde:.3%}; "
    f"absolute MDE {mde:.3f} = {100 * mde:.3f} percentage points. "
    "Independent observations, two-sided α=0.05, 1:1 allocation, 80% power."
)
st.write(
    "Required per arm (1:1, 80% power):",
    required_per_arm(baseline, mde),
)
st.caption("Normal-approximation planning; rounded up. This is not a certification of the Criteo allocation.")
st.warning(r["decision"])
st.json(r["business_guardrail"])
st.json(r["srm"])
st.write(r["assumptions"])
