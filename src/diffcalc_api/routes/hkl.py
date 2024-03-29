"""Endpoints relating to calculating positions using constraints and the UB matrix."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from diffcalc_api.errors.hkl import InvalidSolutionBoundsError
from diffcalc_api.models.hkl import SolutionConstraints
from diffcalc_api.models.response import (
    DiffractorAnglesResponse,
    ReciprocalSpaceResponse,
    ScanResponse,
)
from diffcalc_api.models.ub import HklModel, PositionModel
from diffcalc_api.services import hkl as service
from diffcalc_api.stores.protocol import HklCalcStore, get_store

router = APIRouter(prefix="/hkl", tags=["hkl"])


@router.get("/{name}/position/lab", response_model=DiffractorAnglesResponse)
async def lab_position_from_miller_indices(
    name: str,
    miller_indices: HklModel = Depends(),
    wavelength: float = Query(..., example=1.0),
    axes: Optional[List[str]] = Query(default=None, example=["mu", "nu", "phi"]),
    low_bound: Optional[List[float]] = Query(default=None, example=[0.0, 0.0, -90.0]),
    high_bound: Optional[List[float]] = Query(default=None, example=[90.0, 90.0, 90.0]),
    store: HklCalcStore = Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Convert miller indices to a list of diffractometer positions.

    Args:
        name: the name of the hkl object to access within the store
        miller_indices: miller indices to be converted
        wavelength: wavelength of light used in the experiment
        axes: angles to constrain the solutions by
        low_bounds: minimum values of constrained axes
        high_bound: maximum values of constrained axes
        store: accessor to the hkl object
        collection: collection within which the hkl object resides

    Returns:
        DiffractorAnglesResponse containing a list of all possible diffractometer
        positions.
    """
    solution_constraints = SolutionConstraints(axes, low_bound, high_bound)
    if not solution_constraints.valid:
        raise InvalidSolutionBoundsError(solution_constraints.msg)

    positions = await service.lab_position_from_miller_indices(
        name,
        miller_indices,
        wavelength,
        solution_constraints,
        store,
        collection,
    )
    return DiffractorAnglesResponse(payload=positions)


@router.get("/{name}/position/hkl", response_model=ReciprocalSpaceResponse)
async def miller_indices_from_lab_position(
    name: str,
    pos: PositionModel = Depends(),
    wavelength: float = Query(..., example=1.0),
    store: HklCalcStore = Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Convert a diffractometer position to a set of miller indices.

    Args:
        name: the name of the hkl object to access within the store
        pos: object containing diffractometer position to be converted.
        wavelength: wavelength of light used in the experiment
        store: accessor to the hkl object.
        collection: collection within which the hkl object resides.

    Returns:
        ReciprocalSpaceResponse containing the miller indices.
    """
    hkl = await service.miller_indices_from_lab_position(
        name, pos, wavelength, store, collection
    )
    return ReciprocalSpaceResponse(payload=hkl)


@router.get("/{name}/scan/hkl", response_model=ScanResponse)
async def scan_hkl(
    name: str,
    start: List[float] = Query(..., example=[1, 0, 1]),
    stop: List[float] = Query(..., example=[2, 0, 2]),
    inc: List[float] = Query(..., example=[0.1, 0, 0.1]),
    wavelength: float = Query(..., example=1),
    axes: Optional[List[str]] = Query(default=None, example=["mu", "nu", "phi"]),
    low_bound: Optional[List[float]] = Query(default=None, example=[0.0, 0.0, -90.0]),
    high_bound: Optional[List[float]] = Query(default=None, example=[90.0, 90.0, 90.0]),
    store: HklCalcStore = Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Retrieve possible diffractometer positions for a range of miller indices.

    Args:
        name: the name of the hkl object to access within the store
        start: miller indices to start at
        stop: miller indices to stop at
        inc: miller indices to increment by
        wavelength: wavelength of light used in the experiment
        axes: angles to constrain the solutions by
        low_bounds: minimum values of constrained axes
        high_bound: maximum values of constrained axes
        store: accessor to the hkl object.
        collection: collection within which the hkl object resides.

    Returns:
        ScanResponse containing a dictionary of each set of miller indices and their
        possible diffractometer positions.
    """
    solution_constraints = SolutionConstraints(axes, low_bound, high_bound)
    if not solution_constraints.valid:
        raise InvalidSolutionBoundsError(solution_constraints.msg)

    scan_results = await service.scan_hkl(
        name,
        start,
        stop,
        inc,
        wavelength,
        solution_constraints,
        store,
        collection,
    )
    return ScanResponse(payload=scan_results)


@router.get("/{name}/scan/wavelength", response_model=ScanResponse)
async def scan_wavelength(
    name: str,
    start: float = Query(..., example=1.0),
    stop: float = Query(..., example=2.0),
    inc: float = Query(..., example=0.2),
    hkl: HklModel = Depends(),
    axes: Optional[List[str]] = Query(default=None, example=["mu", "nu", "phi"]),
    low_bound: Optional[List[float]] = Query(default=None, example=[0.0, 0.0, -90.0]),
    high_bound: Optional[List[float]] = Query(default=None, example=[90.0, 90.0, 90.0]),
    store: HklCalcStore = Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Retrieve possible diffractometer positions for a range of wavelengths.

    Args:
        name: the name of the hkl object to access within the store
        start: wavelength to start at
        stop: wavelength to stop at
        inc: wavelength to increment by
        hkl: desired miller indices to use for the experiment
        axes: angles to constrain the solutions by
        low_bounds: minimum values of constrained axes
        high_bound: maximum values of constrained axes
        store: accessor to the hkl object.
        collection: collection within which the hkl object resides.

    Returns:
        ScanResponse containing a dictionary of each wavelength and the corresponding
        possible diffractometer positions.
    """
    solution_constraints = SolutionConstraints(axes, low_bound, high_bound)
    if not solution_constraints.valid:
        raise InvalidSolutionBoundsError(solution_constraints.msg)

    scan_results = await service.scan_wavelength(
        name, start, stop, inc, hkl, solution_constraints, store, collection
    )
    return ScanResponse(payload=scan_results)


@router.get("/{name}/scan/{constraint}", response_model=ScanResponse)
async def scan_constraint(
    name: str,
    constraint: str,
    start: float = Query(..., example=1),
    stop: float = Query(..., example=4),
    inc: float = Query(..., example=1),
    hkl: HklModel = Depends(),
    wavelength: float = Query(..., example=1.0),
    axes: Optional[List[str]] = Query(default=None, example=["mu", "nu", "phi"]),
    low_bound: Optional[List[float]] = Query(default=None, example=[0.0, 0.0, -90.0]),
    high_bound: Optional[List[float]] = Query(default=None, example=[90.0, 90.0, 90.0]),
    store: HklCalcStore = Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Retrieve possible diffractometer positions while scanning across a constraint.

    Args:
        name: the name of the hkl object to access within the store
        constraint: the name of the constraint to use.
        start: constraint to start at
        stop: constraint to stop at
        inc: constraint to increment by
        hkl: desired miller indices to use for the experiment
        wavelength: wavelength of light used in the experiment
        axes: angles to constrain the solutions by
        low_bounds: minimum values of constrained axes
        high_bound: maximum values of constrained axes
        store: accessor to the hkl object.
        collection: collection within which the hkl object resides.

    Returns:
        ScanResponse containing a dictionary of each constraint value and the
        corresponding possible diffractometer positions.
    """
    solution_constraints = SolutionConstraints(axes, low_bound, high_bound)
    if not solution_constraints.valid:
        raise InvalidSolutionBoundsError(solution_constraints.msg)

    scan_results = await service.scan_constraint(
        name,
        constraint,
        start,
        stop,
        inc,
        hkl,
        wavelength,
        solution_constraints,
        store,
        collection,
    )

    return ScanResponse(payload=scan_results)
