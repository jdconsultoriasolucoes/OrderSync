import uuid
from typing import Optional, Any, Dict, List

class OrderSyncException(Exception):
    """Base exception for all custom OrderSync exceptions."""
    def __init__(self, message: str, code: str = "SYS_001", type_: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.type = type_
        self.status_code = status_code
        self.details = details or []
        self.trace_id = uuid.uuid4().hex[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "type": self.type,
                "message": self.message,
                "details": self.details,
                "trace_id": self.trace_id
            }
        }

class BusinessRuleException(OrderSyncException):
    """Exception raised when a business rule is violated."""
    def __init__(self, message: str, code: str = "BUS_001", details: Optional[List[str]] = None):
        super().__init__(
            message=message, 
            code=code, 
            type_="BUSINESS_RULE_VIOLATION", 
            status_code=400, 
            details=details
        )

class ValidationException(OrderSyncException):
    """Exception raised when input validation fails in services (non-Pydantic)."""
    def __init__(self, message: str, code: str = "VAL_001", details: Optional[List[str]] = None):
        super().__init__(
            message=message, 
            code=code, 
            type_="VALIDATION_ERROR", 
            status_code=400, 
            details=details
        )

class ResourceNotFoundException(OrderSyncException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str, code: str = "NOT_FOUND", details: Optional[List[str]] = None):
        super().__init__(
            message=message, 
            code=code, 
            type_="RESOURCE_NOT_FOUND", 
            status_code=404, 
            details=details
        )

class IdempotencyException(OrderSyncException):
    """Exception raised when an idempotency key conflict occurs."""
    def __init__(self, message: str, code: str = "IDEM_001", details: Optional[List[str]] = None):
        super().__init__(
            message=message, 
            code=code, 
            type_="CONFLICT", 
            status_code=409, 
            details=details
        )
