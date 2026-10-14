import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from decision_memo import memo
from experiment import analyze, generate


def test_memo_includes_guardrail_and_source_limit():
    result = analyze(generate(n_per_arm=100), observation_days=28, bootstrap_repetitions=20)
    text = memo(result)
    assert "dados sintéticos" in text
    assert "Descadastros A" in text
    assert result["decision"] in text
    assert "promover automaticamente" in text
