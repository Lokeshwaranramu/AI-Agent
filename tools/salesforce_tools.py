"""
Salesforce integration tools using simple-salesforce.
Provides: query, create, update, delete, describe, and metadata operations.
"""
import os
from typing import Any, Dict, List, Optional

from utils.logger import log


class SalesforceClient:
    """
    Salesforce client wrapper with authentication and CRUD operations.
    Uses environment variables for credentials.
    Gracefully degrades when credentials are not configured.
    """

    def __init__(self) -> None:
        """Initialize Salesforce client from environment variables."""
        self.sf = None
        self._connect()

    def _connect(self) -> None:
        """Establish Salesforce connection using env credentials."""
        username = os.getenv("SF_USERNAME")
        password = os.getenv("SF_PASSWORD")
        security_token = os.getenv("SF_SECURITY_TOKEN")
        domain = os.getenv("SF_DOMAIN", "login")

        placeholders = {"your.email@company.com", "YourPassword123", "YourSecurityTokenHere", ""}
        if not all([username, password, security_token]) or {username, password, security_token} & placeholders:
            log.warning(
                "Salesforce credentials not configured. "
                "Set SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN in .env"
            )
            return

        try:
            from simple_salesforce import Salesforce
            from simple_salesforce.exceptions import SalesforceError

            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain,
            )
            log.success(f"Connected to Salesforce as {username}")
        except Exception as e:
            log.error(f"Salesforce connection failed: {e}")

    def execute_soql(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SOQL query and return results.

        Args:
            query: Valid SOQL query string

        Returns:
            List of record dictionaries
        """
        if not self.sf:
            raise RuntimeError(
                "Not connected to Salesforce. Configure SF credentials in .env"
            )

        try:
            log.info(f"Executing SOQL: {query}")
            result = self.sf.query_all(query)
            records = result.get("records", [])
            log.success(f"SOQL returned {len(records)} records")
            return records
        except Exception as e:
            log.error(f"SOQL query failed: {e}")
            raise

    def create_record(self, object_name: str, data: Dict[str, Any]) -> str:
        """
        Create a new Salesforce record.

        Args:
            object_name: API name of the object (e.g., 'Account', 'Contact')
            data: Dict of field API names to values

        Returns:
            Salesforce record ID of created record
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce.")

        try:
            sf_object = getattr(self.sf, object_name)
            result = sf_object.create(data)
            record_id = result.get("id")
            log.success(f"Created {object_name} record: {record_id}")
            return record_id
        except Exception as e:
            log.error(f"Record creation failed: {e}")
            raise

    def update_record(self, object_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing Salesforce record.

        Args:
            object_name: API name of the object
            record_id: Salesforce record ID (18-char)
            data: Dict of field API names to new values

        Returns:
            True if update was successful
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce.")

        try:
            sf_object = getattr(self.sf, object_name)
            sf_object.update(record_id, data)
            log.success(f"Updated {object_name} {record_id}")
            return True
        except Exception as e:
            log.error(f"Record update failed: {e}")
            raise

    def describe_object(self, object_name: str) -> Dict[str, Any]:
        """
        Get field metadata for a Salesforce object.

        Args:
            object_name: API name of the Salesforce object

        Returns:
            Dict containing object metadata including all fields
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce.")

        try:
            sf_object = getattr(self.sf, object_name)
            result = sf_object.describe()
            log.success(f"Described {object_name}: {len(result['fields'])} fields")
            return result
        except Exception as e:
            log.error(f"Object describe failed: {e}")
            raise


# Global singleton — imported by agent/core.py
sf_client = SalesforceClient()
