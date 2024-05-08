import functools
import inspect
import json
import logging
import os

import azure.functions as func
from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

COSMOS_ENDPOINT = os.environ['CosmosDBEndpoint']
COSMOS_KEY = os.environ['CosmosDBKey']
COSMOS_DATABASE = os.environ['CosmosDBDatabase']

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

cosmos = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
database = cosmos.get_database_client(COSMOS_DATABASE)


def _json(fun):
    @functools.wraps(fun)
    async def inner(*args, **kwargs):
        resp = fun(*args, **kwargs)
        if inspect.iscoroutinefunction(fun):
            resp = await resp
        if isinstance(resp, tuple) and len(resp) == 2:
            data, code = resp
        elif resp is None or isinstance(resp, (dict, list)):
            data = resp
            code = 200
        return func.HttpResponse(json.dumps(data), status_code=code, mimetype='application/json')

    return inner


async def get_container(id: str):
    return await database.create_container_if_not_exists(id, PartitionKey('/id'))


async def get_item(container_id: str, id: str):
    container = await get_container(container_id)
    try:
        return await container.read_item(id, id)
    except CosmosResourceNotFoundError:
        return None


@app.route('items/{id}', methods=['GET'])
@_json
async def route_get_item(req: func.HttpRequest):
    id = req.route_params['id']
    logging.info(f'GET /items/{id}')
    container = await get_container('TestContainer')
    document = await container.read_item(id, id)
    if document is not None:
        return document
    return None, 500
