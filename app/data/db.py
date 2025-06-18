from fastapi import Request

from app.data.connection import Database


def get_db(request: Request) -> Database:
    """
    Dependency to retrieve the Database instance from app.state.
    """
    return request.app.state.db
