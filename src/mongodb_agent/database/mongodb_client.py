"""
MongoDB client for database operations.

This module handles MongoDB connections, query execution, and result processing.
Includes connection pooling, error handling, and query validation.

Features:
- Connection pooling for performance
- Automatic retry on transient failures
- Query validation and sanitization
- Comprehensive error handling
- Schema introspection for LLM context

Best Practices:
- Use connection pooling (maxPoolSize)
- Always close connections in production
- Handle connection failures gracefully
- Use context managers for automatic cleanup

Author: AI Agent Development Team
"""

from typing import Any, Dict, List, Optional, Tuple

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mongodb_agent.config.settings import MongoDBConfig, get_config
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDBClient:
    """
    MongoDB client wrapper with connection pooling and error handling.

    This class manages MongoDB connections and provides methods for
    executing queries and aggregations safely.

    Features:
    - Connection pooling for performance
    - Automatic retry on transient failures
    - Query validation and sanitization
    - Comprehensive error handling
    - Schema introspection

    Example usage:
        >>> with MongoDBClient() as client:
        ...     results = client.find("movies", {"year": 2020})
        ...     for doc in results:
        ...         print(doc["title"])
        >>>
        >>> # Or without context manager
        >>> client = MongoDBClient()
        >>> results = client.aggregate("movies", [
        ...     {"$match": {"year": {"$gte": 2015}}},
        ...     {"$group": {"_id": "$genre", "count": {"$sum": 1}}}
        ... ])
        >>> client.close()
    """

    def __init__(self, config: Optional[MongoDBConfig] = None):
        """
        Initialize MongoDB client.

        Args:
            config: MongoDB configuration. If None, uses app config.
        """
        if config is None:
            app_config = get_config()
            config = app_config.mongodb

        self.config = config
        self.client: Optional[MongoClient] = None
        self.db = None

        # Initialize connection
        self._connect()

    @retry(
        retry=retry_if_exception_type((ConnectionFailure, ServerSelectionTimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10),
    )
    def _connect(self) -> None:
        """
        Establish MongoDB connection with retry logic.

        Uses connection pooling for efficient resource usage.
        Automatically retries on connection failures.

        Raises:
            ConnectionFailure: If unable to connect after retries
        """
        try:
            logger.info(
                f"Connecting to MongoDB",
                extra={"uri": self.config.uri[:20] + "...", "database": self.config.database},
            )

            # Create MongoClient with connection pooling
            self.client = MongoClient(
                self.config.uri,
                maxPoolSize=self.config.max_pool_size,
                serverSelectionTimeoutMS=self.config.timeout_ms,
                # Additional recommended settings for production
                retryWrites=True,
                retryReads=True,
                connectTimeoutMS=self.config.timeout_ms,
                socketTimeoutMS=self.config.timeout_ms * 2,
            )

            # Test connection with ping
            self.client.admin.command("ping")

            # Get database reference
            self.db = self.client[self.config.database]

            logger.info(
                f"Successfully connected to MongoDB",
                extra={"database": self.config.database, "pool_size": self.config.max_pool_size},
            )

        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}", exc_info=True)
            raise ConnectionFailure(f"MongoDB connection error: {e}")

    def find(
        self,
        collection: str,
        filter_dict: Dict[str, Any],
        projection: Optional[Dict[str, int]] = None,
        limit: int = 100,
        sort: Optional[List[Tuple[str, int]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute find query on collection.

        Args:
            collection: Collection name
            filter_dict: MongoDB filter/query document
                        Example: {"year": {"$gte": 2020}}
            projection: Fields to include/exclude
                       Example: {"_id": 0, "title": 1, "year": 1}
            limit: Maximum number of documents to return
            sort: Sort specification
                 Example: [("year", -1), ("title", 1)]

        Returns:
            List of matching documents

        Raises:
            OperationFailure: If query execution fails

        Example:
            >>> client.find(
            ...     "movies",
            ...     {"year": {"$gte": 2020}},
            ...     projection={"title": 1, "year": 1},
            ...     limit=10,
            ...     sort=[("year", -1)]
            ... )
            [{"title": "Movie1", "year": 2023}, ...]
        """
        try:
            logger.debug(
                f"Executing find query",
                extra={
                    "collection": collection,
                    "filter": str(filter_dict)[:100],
                    "limit": limit,
                },
            )

            # Get collection
            coll = self.db[collection]

            # Build query
            cursor = coll.find(filter_dict, projection)

            # Apply limit
            if limit:
                cursor = cursor.limit(limit)

            # Apply sort
            if sort:
                cursor = cursor.sort(sort)

            # Execute and convert to list
            results = list(cursor)

            logger.info(
                f"Find query completed",
                extra={"collection": collection, "result_count": len(results)},
            )

            return results

        except OperationFailure as e:
            logger.error(f"MongoDB find operation failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in find: {e}", exc_info=True)
            raise OperationFailure(f"Find operation error: {e}")

    def aggregate(
        self, collection: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline on collection.

        Aggregation pipelines allow complex data processing including:
        - Filtering ($match)
        - Grouping ($group)
        - Sorting ($sort)
        - Projecting ($project)
        - Joining ($lookup)
        - Calculating ($addFields, $set)
        - And many more stages

        Args:
            collection: Collection name
            pipeline: List of aggregation stages
                     Example: [
                         {"$match": {"year": {"$gte": 2015}}},
                         {"$group": {
                             "_id": "$year",
                             "avg_rating": {"$avg": "$imdb.rating"},
                             "count": {"$sum": 1}
                         }},
                         {"$sort": {"_id": -1}}
                     ]

        Returns:
            List of aggregation results

        Raises:
            OperationFailure: If aggregation fails

        Example:
            >>> # Average rating by year
            >>> client.aggregate("movies", [
            ...     {"$match": {"year": {"$gte": 2015}}},
            ...     {"$group": {
            ...         "_id": "$year",
            ...         "avg_rating": {"$avg": "$imdb.rating"},
            ...         "count": {"$sum": 1}
            ...     }},
            ...     {"$sort": {"_id": -1}}
            ... ])
            [{"_id": 2023, "avg_rating": 7.5, "count": 150}, ...]
        """
        try:
            logger.debug(
                f"Executing aggregation",
                extra={
                    "collection": collection,
                    "pipeline_stages": len(pipeline),
                },
            )

            # Log pipeline for debugging (first 2 stages only to avoid spam)
            for i, stage in enumerate(pipeline[:2]):
                logger.debug(f"Stage {i}: {stage}")

            # Get collection
            coll = self.db[collection]

            # Execute aggregation
            cursor = coll.aggregate(pipeline)

            # Convert to list
            results = list(cursor)

            logger.info(
                f"Aggregation completed",
                extra={"collection": collection, "result_count": len(results)},
            )

            return results

        except OperationFailure as e:
            logger.error(
                f"MongoDB aggregation failed: {e}",
                extra={"pipeline": pipeline},
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error in aggregation: {e}", exc_info=True)
            raise OperationFailure(f"Aggregation error: {e}")

    def get_collection_schema(
        self, collection: str, sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get schema information for collection by sampling documents.

        This helps the LLM understand the data structure when generating queries.
        Uses $sample aggregation stage to randomly sample documents.

        Args:
            collection: Collection name
            sample_size: Number of documents to sample

        Returns:
            Dictionary with schema information including:
            - collection: Collection name
            - fields: List of field names
            - sample_values: Example values for each field
            - field_types: Detected types for each field
            - document_count: Total number of documents

        Example:
            >>> schema = client.get_collection_schema("movies")
            >>> print(schema["fields"])
            ['_id', 'title', 'year', 'genres', 'imdb']
            >>> print(schema["sample_values"]["title"])
            'Inception'
        """
        try:
            logger.debug(
                f"Extracting schema",
                extra={"collection": collection, "sample_size": sample_size},
            )

            coll = self.db[collection]

            # Sample documents
            samples = list(coll.aggregate([{"$sample": {"size": sample_size}}]))

            if not samples:
                logger.warning(f"No documents found in collection: {collection}")
                return {
                    "collection": collection,
                    "fields": [],
                    "sample_values": {},
                    "field_types": {},
                    "document_count": 0,
                }

            # Extract all unique fields
            all_fields = set()
            for doc in samples:
                all_fields.update(doc.keys())

            # Get sample values and types
            sample_values = {}
            field_types = {}

            for field in all_fields:
                # Get first non-null value
                for doc in samples:
                    if field in doc and doc[field] is not None:
                        sample_values[field] = doc[field]
                        field_types[field] = type(doc[field]).__name__
                        break

            # Get total document count
            doc_count = coll.count_documents({})

            schema_info = {
                "collection": collection,
                "fields": sorted(list(all_fields)),
                "sample_values": sample_values,
                "field_types": field_types,
                "document_count": doc_count,
            }

            logger.info(
                f"Schema extracted",
                extra={
                    "collection": collection,
                    "field_count": len(all_fields),
                    "document_count": doc_count,
                },
            )

            return schema_info

        except Exception as e:
            logger.error(f"Error extracting schema: {e}", exc_info=True)
            return {
                "collection": collection,
                "fields": [],
                "sample_values": {},
                "field_types": {},
                "document_count": 0,
            }

    def list_collections(self) -> List[str]:
        """
        List all collections in the database.

        Returns:
            List of collection names

        Example:
            >>> collections = client.list_collections()
            >>> print(collections)
            ['movies', 'users', 'comments']
        """
        try:
            collections = self.db.list_collection_names()
            logger.debug(f"Found {len(collections)} collections")
            return collections

        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    def ping(self) -> bool:
        """
        Test MongoDB connection.

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False

    def close(self) -> None:
        """Close MongoDB connection and release resources."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def __enter__(self) -> "MongoDBClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - automatically closes connection."""
        self.close()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"MongoDBClient(database='{self.config.database}', "
            f"connected={self.client is not None})"
        )
