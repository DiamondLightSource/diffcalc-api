import ast
from pathlib import Path

import numpy as np
import pytest
from diffcalc.hkl.calc import HklCalculation
from diffcalc.hkl.constraints import Constraints
from diffcalc.hkl.geometry import Position
from diffcalc.ub.calc import UBCalculation
from fastapi.testclient import TestClient

from diffcalc_API.errors.UBCalculation import codes
from diffcalc_API.fileHandling import supplyPersist, unpickleHkl
from diffcalc_API.server import app

dummyHkl = HklCalculation(UBCalculation(name="dummy"), Constraints())


def dummy_unpickleHkl(name: str) -> HklCalculation:
    return dummyHkl


def dummy_pickleHkl(object: HklCalculation, pickleFileName: str) -> Path:
    return Path("/does/not/exist")


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[unpickleHkl] = dummy_unpickleHkl
    app.dependency_overrides[supplyPersist] = lambda: dummy_pickleHkl

    return TestClient(app)


def test_add_reflection(client: TestClient):
    response = client.put(
        "/ub/test/reflection",
        json={
            "hkl": [0, 0, 1],
            "position": [7, 0, 10, 0, 0, 0],
            "energy": 12,
            "tag": "foo",
        },
    )

    assert response.status_code == 200
    assert dummyHkl.ubcalc.get_reflection("foo")

    dummyHkl.ubcalc.del_reflection("foo")


def test_edit_reflection(client: TestClient):
    dummyHkl.ubcalc.add_reflection([0, 0, 1], Position(7, 0, 10, 0, 0, 0), 12, "foo")
    response = client.patch(
        "/ub/test/reflection",
        json={
            "energy": 13,
            "tagOrIdx": "foo",
        },
    )
    reflection = dummyHkl.ubcalc.get_reflection("foo")

    assert response.status_code == 200
    assert reflection.energy == 13

    dummyHkl.ubcalc.del_reflection("foo")


def test_delete_reflection(client: TestClient):
    dummyHkl.ubcalc.add_reflection([0, 0, 1], Position(7, 0, 10, 0, 0, 0), 12, "foo")
    response = client.delete("/ub/test/reflection", json="foo")

    assert response.status_code == 200
    with pytest.raises(Exception):
        dummyHkl.ubcalc.get_reflection("foo")


def test_edit_or_delete_reflection_fails_for_non_existing_reflection(
    client: TestClient,
):
    editResponse = client.patch(
        "/ub/test/reflection",
        json={
            "energy": 13,
            "tagOrIdx": "foo",
        },
    )
    deleteResponse = client.delete(
        "/ub/test/reflection",
        json="foo",
    )

    assert editResponse.status_code == codes.get_reflection
    assert deleteResponse.status_code == codes.get_reflection


def test_add_orientation(client: TestClient):
    response = client.put(
        "/ub/test/orientation",
        json={
            "hkl": [0, 1, 0],
            "xyz": [0, 1, 0],
            "tag": "bar",
        },
    )

    assert response.status_code == 200
    assert dummyHkl.ubcalc.get_orientation("bar")

    dummyHkl.ubcalc.del_orientation("bar")


def test_edit_orientation(client: TestClient):
    dummyHkl.ubcalc.add_orientation([0, 0, 1], [0, 0, 1], None, "bar")
    response = client.patch(
        "/ub/test/orientation",
        json={
            "xyz": [1, 1, 0],
            "tagOrIdx": "bar",
        },
    )
    orientation = dummyHkl.ubcalc.get_orientation("bar")

    assert response.status_code == 200

    assert orientation.x == 1
    assert orientation.y == 1
    assert orientation.z == 0

    dummyHkl.ubcalc.del_orientation("bar")


def test_delete_orientation(client: TestClient):
    dummyHkl.ubcalc.add_orientation([0, 0, 1], [0, 0, 1], None, "bar")
    response = client.delete(
        "/ub/test/orientation",
        json="bar",
    )

    assert response.status_code == 200
    with pytest.raises(Exception):
        dummyHkl.ubcalc.get_orientation("bar")


def test_edit_or_delete_orientation_fails_for_non_existing_orientation(
    client: TestClient,
):
    editResponse = client.patch(
        "/ub/test/orientation",
        json={
            "xyz": [1, 1, 0],
            "tagOrIdx": "bar",
        },
    )
    deleteResponse = client.delete(
        "/ub/test/orientation",
        json="bar",
    )

    assert editResponse.status_code == codes.get_orientation
    assert deleteResponse.status_code == codes.get_orientation


def test_set_lattice(client: TestClient):
    response = client.patch(
        "/ub/test/lattice",
        json={"a": 2},
    )

    assert response.status_code == 200
    assert dummyHkl.ubcalc.crystal


def test_set_lattice_fails_for_empty_data(client: TestClient):
    responseWithNoInput = client.patch(
        "/ub/test/lattice",
        json={},
    )

    responseWithWrongInput = client.patch(
        "/ub/test/lattice",
        json={"unknown": "fields"},
    )

    assert responseWithWrongInput.status_code == codes.check_params_not_empty
    assert responseWithNoInput.status_code == codes.check_params_not_empty


def test_modify_property(client: TestClient):
    response = client.patch(
        "/ub/test/n_hkl",
        json=[0, 0, 1],
    )

    assert response.status_code == 200
    assert np.all(dummyHkl.ubcalc.n_hkl == np.transpose([[0, 0, 1]]))


def test_modify_non_existent_property(client: TestClient):
    response = client.patch(
        "/ub/test/silly_property",
        json=[0, 0, 1],
    )
    assert response.status_code == codes.check_property_is_valid


def test_calculate_UB(client: TestClient):
    dummyHkl.ubcalc.add_reflection([0, 0, 1], Position(7, 0, 10, 0, 0, 0), 12, "foo")
    dummyHkl.ubcalc.add_orientation([0, 1, 0], [0, 1, 0], None, "bar")
    dummyHkl.ubcalc.set_lattice(name="test", a=2)

    response = client.get("/ub/test/UB", params={"firstTag": "foo", "secondTag": "bar"})

    expected_UB = [[3.141593, 0, 0], [0, 3.139679, 0.10964], [-0, -0.10964, 3.139679]]

    assert response.status_code == 200
    assert ast.literal_eval(response._content.decode().replace('"', "")) == expected_UB


def test_calculate_UB_fails_when_incorrect_tags(client: TestClient):
    response = client.get("/ub/test/UB", params={"firstTag": "one", "secondTag": "two"})

    assert response.status_code == codes.calculate_UB_matrix
