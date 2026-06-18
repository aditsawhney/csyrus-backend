import enum


class UserRole(str, enum.Enum):
    REQUESTER = "REQUESTER"
    REVIEWER = "REVIEWER"


class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewActionType(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
