import numpy as np
import pytest

from backend.ai_simulate import build_spec, validate_spec
from backend.mesh import Mesh2D
from backend.solver import build_obstacle_mask


@pytest.mark.parametrize("prompt,archetype,shape", [
    ("like an simple house?", "cad", "house"),
    ("Formula 1 front wing", "f1", None),  # f1 must win over generic "wing"
    ("20m glass tower", "cad", "tower"),
    ("water in pipe", "venturi", None),
])
def test_prompt_routes_to_expected_shape(prompt, archetype, shape):
    r = build_spec(prompt)
    assert r["ok"] and r["simulation_spec"]["archetype"] == archetype
    assert r["simulation_spec"].get("obstacleSpec", {}).get("shape") == shape


def test_unknown_prompt_does_not_fall_back_to_airfoil():
    assert build_spec("tell me a joke")["ok"] is False


def test_validate_coerces_and_caps_dt():
    s = validate_spec({"gridResolution": "41x41", "reynoldsNumber": "400", "dt": 0.5})
    assert s["mesh"]["nx"] == 41 and s["fluid"]["reynolds"] == 400
    assert s["numerics"]["dt"] < 0.65 / 40 + 1e-12


@pytest.mark.parametrize("shape", ["house", "tower"])
def test_new_shapes_make_nonempty_partial_mask(shape):
    m = Mesh2D(41, 41, 1.0, 1.0)
    mask = build_obstacle_mask(m, "cad", obstacle_spec={"shape": shape, "cx": 0.4, "cy": 0.5, "size": 0.15})
    assert 0 < mask.sum() < mask.size
    if shape == "house":  # pitched roof: top row narrower than walls
        top = np.where(mask.any(axis=0))[0].max()
        assert mask[:, top].sum() < mask[:, np.where(mask.any(axis=0))[0].min()].sum()


@pytest.mark.parametrize("prompt,expected", [
    ("airflow past a cylinder at Re=900", 900),
    ("water in a pipe, reynolds number 250", 250),
    ("a simple house", None),
])
def test_user_typed_reynolds_is_read(prompt, expected):
    from backend.ai_simulate import explicit_reynolds
    assert explicit_reynolds(prompt) == expected


def test_user_reynolds_beats_the_models_guess():
    from backend.ai_simulate import normalize_rl_spec
    spec = normalize_rl_spec({"archetype": "cylinder", "reynoldsNumber": 600}, "cylinder at Re=900")["simulation_spec"]
    assert spec["fluid"]["reynolds"] == 900
    assert normalize_rl_spec({"archetype": "cylinder", "reynoldsNumber": 600}, "a cylinder")["simulation_spec"]["fluid"]["reynolds"] == 600
