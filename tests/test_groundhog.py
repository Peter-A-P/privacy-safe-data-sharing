"""The Groundhog sanity pair: a copying synthesiser gives an outlier away, an ignoring one does not."""

from __future__ import annotations

import numpy as np
import pandas as pd

from facsimile.attacks.groundhog import attack_target, choose_targets, features, pooled
from facsimile.prep import Categorical, Domain, Numeric, encode, fit_domain

SPECS = (
    Categorical("region", values=tuple(str(i) for i in range(12))),
    Categorical("sex", values=("1", "2")),
    Numeric("age", lo=0, hi=90, bins=9),
    Numeric("income", lo=0, hi=100, bins=10),
)


def population(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "region": rng.choice(
                12, n, p=[0.3, 0.2, 0.15, 0.1, 0.1, 0.05, 0.04, 0.03, 0.02, 0.005, 0.004, 0.001]
            ),
            "sex": rng.integers(1, 3, n),
            "age": rng.normal(40, 10, n).clip(0, 89),
            "income": rng.normal(30, 8, n).clip(0, 99),
        }
    )


def world() -> tuple[pd.DataFrame, pd.DataFrame, Domain]:
    raw = population(6000, 0)
    # One planted outlier in the evaluation half: the rarest region, the oldest age, the top income.
    # The paper's features see a record through its marginals, so a copy gives this one away; a
    # record whose oddness is only in a combination of common values it may not (docs/attacks.md).
    raw.loc[5999] = {"region": 11, "sex": 1, "age": 89.0, "income": 99.0}
    raw = raw[(raw["region"] != 11) | (raw.index == 5999)]
    domain = fit_domain(SPECS, raw)
    coded = encode(raw, domain)
    return coded.iloc[:2900], coded.iloc[2900:], domain


def test_features_have_a_fixed_length_and_see_one_record() -> None:
    shadow, _, domain = world()
    a = features(shadow.iloc[:200], domain)
    b = features(pd.concat([shadow.iloc[:199], shadow.iloc[[250]]]), domain)
    assert a.shape == b.shape and not np.allclose(a, b)


def test_a_copying_synthesiser_gives_an_outlier_away_and_an_ignoring_one_does_not() -> None:
    shadow, evaluation, domain = world()
    targets = choose_targets(
        evaluation, domain, n_outliers=1, n_random=0, seed=0, sample=len(evaluation)
    )
    assert targets.index[0] == 5999, "the planted outlier is the farthest record"
    target = targets.iloc[[0]]
    pools = (shadow.drop(index=target.index, errors="ignore"), evaluation.drop(index=target.index))
    fixed = population(200, 99)
    independent = encode(fixed, domain)

    def copy(data: pd.DataFrame, seed: int) -> pd.DataFrame:
        return data

    def ignore(data: pd.DataFrame, seed: int) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        return independent.iloc[rng.integers(0, len(independent), len(data))].reset_index(drop=True)

    kw = {"n": 200, "n_shadow": 60, "n_eval": 40, "seed": 1, "kind": "outlier"}
    leaky = attack_target(target, *pools, copy, domain, **kw)  # type: ignore[arg-type]
    assert leaky.correct / leaky.trials > 0.9, leaky
    quiet = attack_target(target, *pools, ignore, domain, **kw)  # type: ignore[arg-type]
    acc = pooled([quiet])["all"]["accuracy"]
    assert acc["lo"] < 0.5 < acc["hi"], acc


def test_a_targets_plan_is_a_function_of_its_seed_alone() -> None:
    from facsimile.attacks.groundhog import plan_target

    a = plan_target(5000, 4000, n=100, n_shadow=6, n_eval=4, seed=7)
    b = plan_target(5000, 4000, n=100, n_shadow=6, n_eval=4, seed=7)
    assert [p.name for p in a] == [f"shadow{i:02d}" for i in range(6)] + [
        f"eval{i:02d}" for i in range(4)
    ]
    assert all((x.rows == y.rows).all() and x.seed == y.seed for x, y in zip(a, b, strict=True))
    assert [p.label for p in a[:4]] == [0, 1, 0, 1]
    assert max(p.rows.max() for p in a if p.phase == "eval") < 4000


def test_the_queue_skips_finished_jobs_and_runs_the_longest_first(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from facsimile import queue

    done = tmp_path / "done.txt"
    done.write_text("x")
    jobs = [
        queue.Job(["noop"], str(done), 5, "finished"),
        queue.Job(["noop"], str(tmp_path / "a"), 10, "short"),
        queue.Job(["noop"], str(tmp_path / "b"), 99, "long"),
    ]
    path = tmp_path / "q.jsonl"
    queue.write_jobs(path, jobs)
    read = queue.read_jobs(path)
    assert [j.label for j in read] == ["finished", "short", "long"]
    assert read[0].done() and not read[1].done()
    pending = sorted((j for j in read if not j.done()), key=lambda j: -j.seconds)
    assert [j.label for j in pending] == ["long", "short"]


def test_the_queue_starts_the_longest_job_that_fits_the_memory_budget() -> None:
    from facsimile.queue import Job, next_job

    big = Job(["x"], "a", 100, "big", memory_gb=8)
    small = Job(["x"], "b", 10, "small", memory_gb=2)
    assert next_job([big, small], running_gb=0, budget_gb=10) is big
    assert next_job([big, small], running_gb=6, budget_gb=10) is small, "short jobs fill in"
    assert next_job([big, small], running_gb=9, budget_gb=10) is None
    assert next_job([Job(["x"], "c", 1, "huge", memory_gb=50)], 0, 10) is not None, "runs alone"
    assert next_job([big], running_gb=99, budget_gb=None) is big
    assert next_job([small], running_gb=2, budget_gb=100, free_gb=9) is None, "machine is full"
    assert next_job([small], running_gb=2, budget_gb=100, free_gb=11) is small
