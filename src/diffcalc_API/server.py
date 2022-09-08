"""Startup script for the API server."""
import logging
import traceback
from typing import Dict, List, Optional

from diffcalc.util import DiffcalcException
from fastapi import Depends, FastAPI, Query, Request, responses

from diffcalc_API import routes
from diffcalc_API.config import Settings
from diffcalc_API.errors.constraints import responses as constraints_responses
from diffcalc_API.errors.definitions import DiffcalcAPIException
from diffcalc_API.errors.hkl import responses as hkl_responses
from diffcalc_API.errors.ub import responses as ub_responses
from diffcalc_API.models.response import (
    CollectionResponse,
    DatabaseResponse,
    InfoResponse,
)
from diffcalc_API.stores.protocol import get_store, setup_store
from diffcalc_API.useful_types import HklType

logger = logging.getLogger(__name__)
config = Settings()
setup_store("diffcalc_API.stores.mongo.MongoHklCalcStore")

app = FastAPI(
    responses=get_store().responses, title="diffcalc", version=config.api_version
)

app.include_router(routes.ub.router, responses=ub_responses)
app.include_router(routes.constraints.router, responses=constraints_responses)
app.include_router(routes.hkl.router, responses=hkl_responses)

#######################################################################################
#                              Middleware for Exceptions                              #
#######################################################################################


@app.exception_handler(DiffcalcException)
async def diffcalc_exception_handler(request: Request, exc: DiffcalcException):
    """Handle diffcalc-core exceptions, which mostly happen on bad requests."""
    tb = traceback.format_exc()
    logger.warning(f"Diffcalc Exception caught by middleware: {tb}")

    return responses.JSONResponse(
        status_code=400,
        content={"message": str(exc), "type": str(type(exc))},
    )


@app.exception_handler(DiffcalcAPIException)
async def http_exception_handler(request: Request, exc: DiffcalcAPIException):
    """Handle exceptions raised due to bad request parameters/queries and bodies."""
    tb = traceback.format_exc()
    logger.warning(f"Diffcalc API Exception caught by middleware: {tb}")

    return responses.JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "type": str(type(exc))},
    )


@app.middleware("http")
async def server_exceptions_middleware(request: Request, call_next):
    """Handle all other exceptions.

    These are undocumented, and if raised should be investigated immediately.
    """
    try:
        return await call_next(request)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"General Exception caught by middleware: {tb}")

        return responses.JSONResponse(
            status_code=500,
            content={"message": str(e), "type": str(type(e))},
        )


#######################################################################################
#                                    Global Routes                                    #
#######################################################################################


@app.get("/", response_model=DatabaseResponse)
async def get_all(store=Depends(get_store)):
    """Retrieve all HklCalculation objects in the store."""
    results: Dict[str, List[HklType]] = await store.get_all()
    return DatabaseResponse(payload=results)


@app.get("/{collection}", response_model=CollectionResponse)
async def get_all_within_collection(
    store=Depends(get_store), collection: str = Query(default="default", example="B07")
):
    """Retrieve all HklCalculation objects in a collection of the store."""
    results: List[HklType] = await store.get_all_within_collection(collection)
    return CollectionResponse(payload=results)


@app.post("/{name}", response_model=InfoResponse)
async def create_hkl_object(
    name: str,
    store=Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Create the hkl object which will be persisted."""
    await store.create(name, collection)
    return InfoResponse(message=f"crystal {name} in collection {collection} created")


@app.delete("/{name}", response_model=InfoResponse)
async def delete_hkl_object(
    name: str,
    store=Depends(get_store),
    collection: Optional[str] = Query(default=None, example="B07"),
):
    """Delete the hkl object from the store i.e. persistence layer."""
    await store.delete(name, collection)

    return InfoResponse(message=f"crystal {name} in collection {collection} deleted")
