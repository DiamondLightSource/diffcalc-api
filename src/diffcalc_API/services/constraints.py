from typing import Dict, Optional, Union

from diffcalc.hkl.constraints import Constraints

from diffcalc_API.config import CONSTRAINTS_WITH_NO_VALUE
from diffcalc_API.errors.constraints import check_constraint_exists
from diffcalc_API.stores.protocol import HklCalcStore


async def get_constraints(
    name: str, store: HklCalcStore, collection: Optional[str]
) -> str:
    hklcalc = await store.load(name, collection)
    return str(hklcalc.constraints)


async def set_constraints(
    name: str,
    constraints: Dict[str, Union[float, bool]],
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    boolean_constraints = set(constraints.keys()).intersection(
        CONSTRAINTS_WITH_NO_VALUE
    )
    for constraint in boolean_constraints:
        constraints[constraint] = bool(constraints[constraint])

    hklcalc.constraints = Constraints(constraints)

    await store.save(name, hklcalc, collection)


async def remove_constraint(
    name: str,
    property: str,
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    check_constraint_exists(property)
    setattr(hklcalc.constraints, property, None)

    await store.save(name, hklcalc, collection)


async def set_constraint(
    name: str,
    property: str,
    value: Union[float, bool],
    store: HklCalcStore,
    collection: Optional[str],
) -> None:
    hklcalc = await store.load(name, collection)

    check_constraint_exists(property)
    if property in CONSTRAINTS_WITH_NO_VALUE:
        value = bool(value)

    setattr(hklcalc.constraints, property, value)

    await store.save(name, hklcalc, collection)
