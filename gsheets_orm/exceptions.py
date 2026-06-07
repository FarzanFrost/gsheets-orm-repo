import sys
import json
from typing import Any, Dict, Optional

class ORMError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
        # Serialize to stderr as JSON as required by STANDARDS_interface.md
        err_payload = {
            "status": "error",
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }
        sys.stderr.write(json.dumps(err_payload) + "\n")
        sys.stderr.flush()

class ValidationError(ORMError):
    pass

class SessionError(ORMError):
    pass

class DialectError(ORMError):
    pass
