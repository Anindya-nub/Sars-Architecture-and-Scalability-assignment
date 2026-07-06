"""
Task 2.3(c)
Thread-safe Singleton implementation for a shared DatabaseConnection object.
"""

from __future__ import annotations

import threading
from typing import Dict


class DatabaseConnection:
    """Thread-safe Singleton using double-checked locking."""

    _instance = None
    _lock = threading.Lock()  # Shared lock used to protect first-time creation.

    def __new__(cls) -> "DatabaseConnection":
        # First check avoids locking after the Singleton has already been created.
        if cls._instance is None:
            # Without this lock, two threads could both observe _instance as None
            # and both create separate objects during naive lazy initialisation.
            with cls._lock:
                # Second check is required because another thread may have created
                # the instance while the current thread was waiting for the lock.
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._connection = cls._instance._create_connection()
        return cls._instance

    def _create_connection(self) -> Dict[str, str]:
        """
        Simulate creation of a shared database connection object.

        In a real application, this is where a database driver connection or
        connection pool would be created.
        """
        return {
            "host": "sars-db-primary",
            "database": "sars",
            "status": "connected",
        }

    def get_connection(self) -> Dict[str, str]:
        """Return the shared connection object."""
        return self._connection


if __name__ == "__main__":
    instances = []

    def create_instance() -> None:
        instances.append(DatabaseConnection())

    threads = [threading.Thread(target=create_instance) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    unique_instance_ids = {id(instance) for instance in instances}
    print(f"Number of unique DatabaseConnection instances: {len(unique_instance_ids)}")
    print(DatabaseConnection().get_connection())
