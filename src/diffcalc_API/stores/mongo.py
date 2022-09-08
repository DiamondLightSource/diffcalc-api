"""Defines interactions with mongo persistence layer."""

from typing import Any, Dict, List, Optional

import numpy as np
from diffcalc.hkl.calc import HklCalculation
from diffcalc.hkl.constraints import Constraints
from diffcalc.ub.calc import UBCalculation
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo.results import DeleteResult

from diffcalc_API.database import database
from diffcalc_API.errors.definitions import (
    ALL_RESPONSES,
    DiffcalcAPIException,
    ErrorCodesBase,
)
from diffcalc_API.useful_types import HklType


class ErrorCodes(ErrorCodesBase):
    """Persistence error codes.

    This class defines all error codes which can be raised in the retrieval or storage
    of HklCalculation objects.
    """

    OVERWRITE_ERROR = 405
    DOCUMENT_NOT_FOUND_ERROR = 404


class OverwriteError(DiffcalcAPIException):
    """Thrown if a HklCalculation object is created with a non-unique name."""

    def __init__(self, name: str) -> None:
        """Set detail and status code of the error."""
        self.detail = (
            f"Document already exists for crystal {name}!"
            f"\nEither delete via DELETE request to this URL "
            f"or change the existing properties. "
        )
        self.status_code = ErrorCodes.OVERWRITE_ERROR


class DocumentNotFoundError(DiffcalcAPIException):
    """Thrown if the store cannot retrieve a HklCalculation object."""

    def __init__(self, name: str, action: str) -> None:
        """Set detail and status code of the error."""
        self.detail = f"Document for crystal {name} not found! Cannot {action}."
        self.status_code = ErrorCodes.DOCUMENT_NOT_FOUND_ERROR


class MongoHklCalcStore:
    """Class to use mongo db as a persistence layer for the API."""

    def __init__(
        self,
    ) -> None:
        """Set error codes that could be thrown during method excecution.

        Purely for documentation purposes.
        """
        self.responses = {
            code: ALL_RESPONSES[code] for code in np.unique(ErrorCodes.all_codes())
        }

    async def get_all(self) -> Dict[str, List[HklType]]:
        """Get all HklCalculation objects that are persisted."""
        all_collections = await database.list_collection_names()
        result: Dict[str, List[HklType]] = {}
        for collection_name in all_collections:
            documents = await self.get_all_within_collection(collection_name)

            result[collection_name] = documents

        return result

    async def get_all_within_collection(self, collection: str) -> List[HklType]:
        """Get all HklCalculation objects persisted within a given collection."""
        coll = database[collection]
        documents = await coll.find({}).to_list(1000)

        modified_documents: List[HklType] = []

        for idx in range(len(documents)):
            modified_documents.append(
                HklType(
                    id=str(documents[idx]["_id"]),
                    **{k: documents[idx][k] for k in documents[idx].keys() - {"_id"}},
                )
            )

        return modified_documents

    async def create(self, name: str, collection: Optional[str]) -> None:
        """Create a HklCalculation object.

        Args:
            name: the unique name to attribute to the object
            collection: the collection to store it inside.
        """
        coll: Collection = database[collection if collection else "default"]

        if await coll.find_one({"ubcalc.name": name}):
            raise OverwriteError(name)

        ubcalc = UBCalculation(name=name)
        constraints = Constraints()
        hkl = HklCalculation(ubcalc, constraints)

        await coll.insert_one(hkl.asdict)

    async def delete(self, name: str, collection: Optional[str]) -> None:
        """Delete a HklCalculation object.

        Args:
            name: the name by which to retrieve the object
            collection: the collection inside which it is stored.
        """
        coll: Collection = database[collection if collection else "default"]
        result: DeleteResult = await coll.delete_one({"ubcalc.name": name})
        if result.deleted_count == 0:
            raise DocumentNotFoundError(name, "delete")

    async def save(
        self, name: str, hkl: HklCalculation, collection: Optional[str]
    ) -> None:
        """Update a HklCalculation object.

        Args:
            name: the name by which to retrieve the object
            collection: the collection inside which it is stored.
        """
        coll: Collection = database[collection if collection else "default"]
        await coll.find_one_and_update({"ubcalc.name": name}, {"$set": hkl.asdict})

    async def load(self, name: str, collection: Optional[str]) -> HklCalculation:
        """Load a HklCalculation object.

        Args:
            name: the name by which to retrieve the object
            collection: the collection inside which it is stored.

        Returns:
            The HklCalculation object.
        """
        coll: Collection = database[collection if collection else "default"]
        hkl_json: Optional[Dict[str, Any]] = await coll.find_one({"ubcalc.name": name})
        if not hkl_json:
            raise DocumentNotFoundError(name, "load")

        return HklCalculation.fromdict(hkl_json)
