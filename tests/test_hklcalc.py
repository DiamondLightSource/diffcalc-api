import ast

import numpy as np
import pytest
from diffcalc.hkl.calc import HklCalculation
from diffcalc.hkl.constraints import Constraints
from diffcalc.hkl.geometry import Position
from diffcalc.ub.calc import UBCalculation
from fastapi.testclient import TestClient

from diffcalc_api.errors.hkl import ErrorCodes
from diffcalc_api.server import app
from diffcalc_api.stores.protocol import HklCalcStore, get_store
from tests.conftest import FakeHklCalcStore

dummy_hkl = HklCalculation(UBCalculation(name="dummy"), Constraints())

dummy_hkl.ubcalc.set_lattice("SiO2", 4.913, 5.405)
dummy_hkl.ubcalc.n_hkl = (1, 0, 0)
dummy_hkl.ubcalc.add_reflection(
    (0, 0, 1), Position(7.31, 0, 10.62, 0, 0, 0), 12.39842, "refl1"
)
dummy_hkl.ubcalc.add_orientation((0, 1, 0), (0, 1, 0), None, "plane")
dummy_hkl.ubcalc.calc_ub("refl1", "plane")

dummy_hkl.constraints = Constraints({"qaz": 0, "alpha": 0, "eta": 0})


def dummy_get_store() -> HklCalcStore:
    return FakeHklCalcStore(dummy_hkl)


@pytest.fixture()
def client() -> TestClient:
    app.dependency_overrides[get_store] = dummy_get_store

    return TestClient(app)


def test_miller_indices_stay_the_same_after_transformation(client: TestClient):
    lab_positions = client.get(
        "/hkl/test/position/lab",
        params={"h": 0, "k": 0, "l": 1, "wavelength": 1},
    )

    assert lab_positions.status_code == 200
    possible_positions = lab_positions.json()["payload"]

    for pos in possible_positions:
        miller_positions = client.get(
            "/hkl/test/position/hkl",
            params={
                "mu": pos["mu"],
                "delta": pos["delta"],
                "nu": pos["nu"],
                "eta": pos["eta"],
                "chi": pos["chi"],
                "phi": pos["phi"],
                "wavelength": 1,
            },
        )

        assert miller_positions.status_code == 200
        results = miller_positions.json()["payload"]
        assert np.round(results["h"], 8) == 0
        assert np.round(results["k"], 8) == 0
        assert np.round(results["l"], 8) == 1


def test_hkl_positions_constrained_by_angle_bounds(client: TestClient):
    lab_positions = client.get(
        (
            "/hkl/test/position/lab?axes=mu&axes=nu&axes=phi&low_bound=0"
            + "&low_bound=0&low_bound=-90&high_bound=90&high_bound=90&high_bound=90"
        ),
        params={"h": 0, "k": 0, "l": 1, "wavelength": 1},
    )

    assert lab_positions.status_code == 200
    assert len(ast.literal_eval(lab_positions.content.decode())["payload"]) == 1


def test_scan_hkl(
    client: TestClient,
):
    lab_positions = client.get(
        "/hkl/test/scan/hkl",
        params={
            "start": [1, 0, 1],
            "stop": [2, 0, 2],
            "inc": [0.5, 0, 0.5],
            "wavelength": 1,
        },
    )
    scan_results = lab_positions.json()["payload"]

    assert lab_positions.status_code == 200
    assert len(scan_results.keys()) == 9


def test_scan_hkl_raises_invalid_solution_bounds_error_for_wrong_inputs(
    client: TestClient,
):
    lab_positions = client.get(
        "/hkl/test/scan/hkl?axes=mu&axes=nu&axes=phi&low_bound=0&high_bound=90",
        params={
            "start": [1, 0, 1],
            "stop": [2, 0, 2],
            "inc": [0.5, 0, 0.5],
            "wavelength": 1,
        },
    )

    assert lab_positions.status_code == ErrorCodes.INVALID_SOLUTION_BOUNDS
    assert (
        ast.literal_eval(lab_positions.content.decode())["type"]
        == "<class 'diffcalc_api.errors.hkl.InvalidSolutionBoundsError'>"
    )


def test_scan_hkl_correctly_constrained_by_angle_bounds(
    client: TestClient,
):
    lab_positions = client.get(
        (
            "/hkl/test/scan/hkl?axes=mu&axes=nu&axes=phi&low_bound=0&low_bound=0"
            + "&low_bound=-90&high_bound=90&high_bound=90&high_bound=90"
        ),
        params={
            "start": [1, 0, 1],
            "stop": [2, 0, 2],
            "inc": [0.5, 0, 0.5],
            "wavelength": 1,
        },
    )
    assert all(
        [
            len(val) == 1
            for val in ast.literal_eval(lab_positions.content.decode())[
                "payload"
            ].values()
        ]
    )


def test_scan_hkl_raises_invalid_miller_indices_error_for_wrong_inputs(
    client: TestClient,
):
    lab_positions = client.get(
        "/hkl/test/scan/hkl",
        params={
            "start": [1, 0, 1],
            "stop": [2, 0, 2],
            "inc": [0.5, 0],
            "wavelength": 1,
        },
    )

    assert (
        ast.literal_eval(lab_positions.content.decode())["type"]
        == "<class 'diffcalc_api.errors.hkl.InvalidMillerIndicesError'>"
    )


def test_scan_wavelength(
    client: TestClient,
):
    lab_positions = client.get(
        "/hkl/test/scan/wavelength",
        params={
            "start": 1,
            "stop": 2,
            "inc": 0.5,
            "h": 1,
            "k": 0,
            "l": 1,
        },
    )
    scan_results = lab_positions.json()["payload"]

    assert lab_positions.status_code == 200
    assert len(scan_results.keys()) == 3


def test_scan_constraint(
    client: TestClient,
):
    lab_positions = client.get(
        "/hkl/test/scan/alpha",
        params={
            "start": 1,
            "stop": 2,
            "inc": 0.5,
            "h": 1,
            "k": 0,
            "l": 1,
            "wavelength": 1.0,
        },
    )
    scan_results = lab_positions.json()["payload"]

    assert lab_positions.status_code == 200
    assert len(scan_results.keys()) == 3


def test_invalid_scans(client: TestClient):
    invalid_miller_indices = client.get(
        "/hkl/test/scan/hkl",
        params={
            "start": [0, 0, 0],
            "stop": [1, 0, 1],
            "inc": [0.5, 0, 0.5],
            "wavelength": 1,
        },
    )

    assert invalid_miller_indices.status_code == ErrorCodes.INVALID_MILLER_INDICES

    invalid_wavelength_scan = client.get(
        "/hkl/test/scan/wavelength",
        params={
            "start": 1,
            "stop": 2,
            "inc": -0.5,
            "h": 1,
            "k": 0,
            "l": 1,
        },
    )

    assert invalid_wavelength_scan.status_code == ErrorCodes.INVALID_SCAN_BOUNDS
