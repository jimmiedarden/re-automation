import pytest

from re_automation.analysis import analyze, mao


def test_mao_uses_65_percent_by_default():
    assert mao(200_000, 30_000) == 100_000


def test_mao_custom_percent():
    assert mao(200_000, 30_000, pct=0.70) == 110_000


def test_mao_never_negative():
    assert mao(50_000, 60_000) == 0


@pytest.mark.parametrize("arv,rehab,pct", [(-1, 0, 0.65), (1, -1, 0.65), (1, 1, 0), (1, 1, 1.5)])
def test_mao_rejects_bad_input(arv, rehab, pct):
    with pytest.raises(ValueError):
        mao(arv, rehab, pct)


@pytest.mark.parametrize(
    "asking,verdict,spread",
    [(90_000, "offer", 10_000), (100_000, "offer", 0), (108_000, "negotiate", -8_000),
     (120_000, "pass", -20_000), (None, "no-asking", None)],
)
def test_verdicts(asking, verdict, spread):
    r = analyze(200_000, 30_000, asking)
    assert r.verdict == verdict
    assert r.spread == spread


def test_zero_mao_is_pass():
    assert analyze(50_000, 60_000, 1_000).verdict == "pass"
