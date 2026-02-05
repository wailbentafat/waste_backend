from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

# Generic type for models
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by ID {id}: {e}")
            return None

    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with optional filtering."""
        try:
            query = select(self.model).offset(skip).limit(limit)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)

            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get multiple {self.model.__name__}: {e}")
            return []

    async def update(self, id: Any, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record by ID."""
        try:
            query = (
                update(self.model)
                .where(self.model.id == id)
                .values(**obj_data)
                .returning(self.model)
            )
            result = await self.session.execute(query)
            await self.session.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model.__name__} ID {id}: {e}")
            return None

    async def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__} ID {id}: {e}")
            return False


class MongoDBBaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base MongoDB repository with common CRUD operations."""

    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new document."""
        try:
            result = await self.collection.insert_one(obj_data)
            obj_data["_id"] = result.inserted_id
            return obj_data
        except Exception as e:
            logger.error(f"Failed to create document in {self.collection.name}: {e}")
            raise

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get a document by ID."""
        try:
            document = await self.collection.find_one({"_id": id})
            return document
        except Exception as e:
            logger.error(f"Failed to get document by ID {id}: {e}")
            return None

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
    ) -> List[ModelType]:
        """Get multiple documents with optional filtering and sorting."""
        try:
            query = {}
            if filters:
                query.update(filters)

            cursor = self.collection.find(query).skip(skip).limit(limit)

            if sort:
                cursor = cursor.sort(sort)

            documents = await cursor.to_list(length=limit)
            return documents
        except Exception as e:
            logger.error(f"Failed to get multiple documents: {e}")
            return []

    async def update(self, id: str, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a document by ID."""
        try:
            document = await self.collection.find_one_and_update(
                {"_id": id}, {"$set": obj_data}, return_document=ReturnDocument.AFTER
            )
            return document
        except Exception as e:
            logger.error(f"Failed to update document ID {id}: {e}")
            return None

    async def delete(self, id: str) -> bool:
        """Delete a document by ID."""
        try:
            result = await self.collection.delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete document ID {id}: {e}")
            return False

    async def find_one(self, query: Dict[str, Any]) -> Optional[ModelType]:
        """Find a document by custom query."""
        try:
            document = await self.collection.find_one(query)
            return document
        except Exception as e:
            logger.error(f"Failed to find document with query {query}: {e}")
            return None

    async def find_many(
        self,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None,
    ) -> List[ModelType]:
        """Find multiple documents by custom query."""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)

            if sort:
                cursor = cursor.sort(sort)

            documents = await cursor.to_list(length=limit)
            return documents
        except Exception as e:
            logger.error(f"Failed to find documents with query {query}: {e}")
            return []

    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute MongoDB aggregation pipeline."""
        try:
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            return results
        except Exception as e:
            logger.error(f"Failed to execute aggregation pipeline: {e}")
            return []

    async def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching query."""
        try:
            if query is None:
                query = {}
            count = await self.collection.count_documents(query)
            return count
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
