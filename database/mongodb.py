"""
MongoDB Connection and Collection Provider for SmartMed AI.
Uses direct PyMongo integration for high performance and strict consistency.
"""
import os
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class MongoDBManager:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.environ.get("MONGODB_DB_NAME", "smartmed_ai")
        try:
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                maxPoolSize=50,
                minPoolSize=5,
            )
            # Ping database to confirm connection
            self._client.admin.command("ping")
            self._db = self._client[db_name]
            logger.info("Connected successfully to MongoDB database: %s", db_name)
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            logger.error("Failed to connect to MongoDB: %s", err)
            self._db = None

    def get_db(self):
        if self._db is None or self._client is None:
            self._initialize()
        return self._db

    def get_client(self):
        if self._client is None:
            self._initialize()
        return self._client

    def is_connected(self) -> bool:
        try:
            if self._client is not None:
                self._client.admin.command("ping")
                return True
        except Exception:
            return False
        return False

    def get_collection(self, name: str):
        db = self.get_db()
        if db is None:
            raise ConnectionError("MongoDB is not connected. Ensure MongoDB is running on localhost:27017.")
        return db[name]

    def init_indexes(self):
        """Initializes required MongoDB collections and indexes."""
        db = self.get_db()
        if db is None:
            logger.warning("Cannot initialize indexes: MongoDB connection is offline.")
            return False

        try:
            # 1. users: unique username and email
            db.users.create_index([("username", ASCENDING)], unique=True)
            db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
            db.users.create_index([("role", ASCENDING)])

            # 2. upload_sessions: session_id, token_hash, expiration
            db.upload_sessions.create_index([("session_id", ASCENDING)], unique=True)
            db.upload_sessions.create_index([("token_hash", ASCENDING)], unique=True)
            db.upload_sessions.create_index([("expires_at", ASCENDING)])
            db.upload_sessions.create_index([("status", ASCENDING)])

            # 3. image_records: image_id, session_id, modality, review_status
            db.image_records.create_index([("image_id", ASCENDING)], unique=True)
            db.image_records.create_index([("session_id", ASCENDING)])
            db.image_records.create_index([("modality", ASCENDING)])
            db.image_records.create_index([("review_status", ASCENDING)])
            db.image_records.create_index([("created_at", DESCENDING)])

            # 4. analysis_records: analysis_id, image_id, task, status
            db.analysis_records.create_index([("analysis_id", ASCENDING)], unique=True)
            db.analysis_records.create_index([("image_id", ASCENDING)])
            db.analysis_records.create_index([("task", ASCENDING)])
            db.analysis_records.create_index([("status", ASCENDING)])
            db.analysis_records.create_index([("created_at", DESCENDING)])

            # 5. colorization_records: colorization_id, image_id
            db.colorization_records.create_index([("colorization_id", ASCENDING)], unique=True)
            db.colorization_records.create_index([("image_id", ASCENDING)])

            # 6. model_registry: model_id, modality, task
            db.model_registry.create_index([("model_id", ASCENDING)], unique=True)
            db.model_registry.create_index([("modality", ASCENDING)])
            db.model_registry.create_index([("task", ASCENDING)])

            # 7. model_evaluations: evaluation_id, model_id, dataset
            db.model_evaluations.create_index([("evaluation_id", ASCENDING)], unique=True)
            db.model_evaluations.create_index([("model_id", ASCENDING)])

            # 8. report_records: report_id, analysis_id
            db.report_records.create_index([("report_id", ASCENDING)], unique=True)
            db.report_records.create_index([("analysis_id", ASCENDING)])

            # 9. device_registry: device_id, api_key_hash
            db.device_registry.create_index([("device_id", ASCENDING)], unique=True)
            db.device_registry.create_index([("api_key_hash", ASCENDING)], unique=True)
            db.device_registry.create_index([("status", ASCENDING)])

            # 10. audit_events: event_id, actor, timestamp
            db.audit_events.create_index([("event_id", ASCENDING)], unique=True)
            db.audit_events.create_index([("actor", ASCENDING)])
            db.audit_events.create_index([("action", ASCENDING)])
            db.audit_events.create_index([("created_at", DESCENDING)])

            logger.info("MongoDB indexes successfully created for SmartMed AI.")
            return True
        except Exception as e:
            logger.error("Failed creating MongoDB indexes: %s", e)
            return False


# Singleton helper functions
def get_db():
    return MongoDBManager().get_db()

def get_collection(name: str):
    return MongoDBManager().get_collection(name)

def check_connection() -> bool:
    return MongoDBManager().is_connected()

def init_db():
    return MongoDBManager().init_indexes()
