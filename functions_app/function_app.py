import azure.functions as func
from azure.cosmos.aio import CosmosClient
import logging
import json
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
cosmos = CosmosClient(os.environ['CosmosDBEndpoint'], os.environ['CosmosDBKey'])


async def get_item(id: str):
    container = cosmos.get_database_client('Database').get_container_client(
        'TestContainer'
    )
    try:
        return await container.read_item(id, id)
    except:
        logging.exception('Error getting item')


def json_resp(data, code=200):
    return func.HttpResponse(json.dumps(data), status_code=code)


@app.route(route='items/{id}', methods=['GET'])
async def get_item_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    item = await get_item(req.route_params['id'])

    return json_resp(item, 200 if item else 500)
