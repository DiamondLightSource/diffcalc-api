from typing import Optional, Tuple, Union

from diffcalc.hkl.geometry import Position

from diffcalc_API.errors.ub import ReferenceRetrievalError
from diffcalc_API.models.ub import (
    AddOrientationParams,
    AddReflectionParams,
    EditOrientationParams,
    EditReflectionParams,
    SetLatticeParams,
)
from diffcalc_API.stores.protocol import HklCalcStore


async def get_ub(name: str, store: HklCalcStore, collection: Optional[str]) -> str:
    hklcalc = await store.load(name, collection)

    return str(hklcalc.ubcalc)


async def add_reflection(
    name: str,
    params: AddReflectionParams,
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    hklcalc.ubcalc.add_reflection(
        params.hkl,
        Position(*params.position),
        params.energy,
        params.tag,
    )

    await store.save(name, hklcalc, collection)


async def edit_reflection(
    name: str,
    params: EditReflectionParams,
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    try:
        reflection = hklcalc.ubcalc.get_reflection(params.tag_or_idx)
    except (IndexError, ValueError):
        raise ReferenceRetrievalError(params.tag_or_idx, "reflection")

    hklcalc.ubcalc.edit_reflection(
        params.tag_or_idx,
        params.hkl if params.hkl else (reflection.h, reflection.k, reflection.l),
        Position(params.position) if params.position else reflection.pos,
        params.energy if params.energy else reflection.energy,
        params.tag_or_idx if isinstance(params.tag_or_idx, str) else None,
    )

    await store.save(name, hklcalc, collection)


async def delete_reflection(
    name: str,
    tag_or_idx: Union[str, int],
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    try:
        hklcalc.ubcalc.get_reflection(tag_or_idx)
    except (IndexError, ValueError):
        raise ReferenceRetrievalError(tag_or_idx, "reflection")

    hklcalc.ubcalc.del_reflection(tag_or_idx)

    await store.save(name, hklcalc, collection)


async def add_orientation(
    name: str,
    params: AddOrientationParams,
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    position = Position(*params.position) if params.position else None
    hklcalc.ubcalc.add_orientation(
        params.hkl,
        params.xyz,
        position,
        params.tag,
    )

    await store.save(name, hklcalc, collection)


async def edit_orientation(
    name: str,
    params: EditOrientationParams,
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    try:
        orientation = hklcalc.ubcalc.get_orientation(params.tag_or_idx)
    except (IndexError, ValueError):
        raise ReferenceRetrievalError(params.tag_or_idx, "orientation")

    hklcalc.ubcalc.edit_orientation(
        params.tag_or_idx,
        params.hkl if params.hkl else (orientation.h, orientation.k, orientation.l),
        params.xyz if params.xyz else (orientation.x, orientation.y, orientation.z),
        Position(params.position) if params.position else orientation.pos,
        params.tag_or_idx if isinstance(params.tag_or_idx, str) else None,
    )

    await store.save(name, hklcalc, collection)


async def delete_orientation(
    name: str,
    tag_or_idx: Union[str, int],
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    try:
        hklcalc.ubcalc.get_orientation(tag_or_idx)
    except (IndexError, ValueError):
        raise ReferenceRetrievalError(tag_or_idx, "orientation")

    hklcalc.ubcalc.del_orientation(tag_or_idx)

    await store.save(name, hklcalc, collection)


async def set_lattice(
    name: str, params: SetLatticeParams, store: HklCalcStore, collection: Optional[str]
) -> None:
    hklcalc = await store.load(name, collection)

    hklcalc.ubcalc.set_lattice(name=name, **params.dict())

    await store.save(name, hklcalc, collection)


async def modify_property(
    name: str,
    property: str,
    target_value: Tuple[float, float, float],
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    setattr(hklcalc.ubcalc, property, target_value)

    await store.save(name, hklcalc, collection)
