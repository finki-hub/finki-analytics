from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class Database:
    def __init__(self, dsn: str) -> None:
        """
        Initialize the database connection.
        """
        self.dsn = dsn

    def init(self) -> None:
        """
        Connect to Mongo and pick a hard-coded DB name.
        Collections are created on-the-fly by name.
        """
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(self.dsn)
        self.db = self.client["usage_data"]

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """
        Return a collection by event_type. If it doesn't exist, Mongo
        will create it on first insert.
        """
        return self.db[name]

    def disconnect(self) -> None:
        """
        Close the database connection.
        """
        self.client.close()
