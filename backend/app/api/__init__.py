from app.schemas.common import ErrorOut

BAD_REQUEST = {400: {"model": ErrorOut, "description": "Bad request"}}
UNAUTHORIZED = {401: {"model": ErrorOut, "description": "Unauthorized"}}
NOT_FOUND = {404: {"model": ErrorOut, "description": "Not found"}}

COMMON_ERROR_RESPONSES = {**BAD_REQUEST, **UNAUTHORIZED, **NOT_FOUND}
