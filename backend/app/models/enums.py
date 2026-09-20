from enum import Enum


class UserRole(str, Enum):
    DONOR = "DONOR"
    REQUESTER = "REQUESTER"
    ADMIN = "ADMIN"


class BloodGroup(str, Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    O_POS = "O+"
    O_NEG = "O-"
    AB_POS = "AB+"
    AB_NEG = "AB-"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ReportReason(str, Enum):
    INCORRECT_INFORMATION = "INCORRECT_INFORMATION"
    FAKE_PROFILE = "FAKE_PROFILE"
    WRONG_BLOOD_GROUP = "WRONG_BLOOD_GROUP"
    SPAM = "SPAM"
    MISUSE = "MISUSE"
    OTHER = "OTHER"


class ReportStatus(str, Enum):
    OPEN = "OPEN"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class NotificationType(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    REPORT = "REPORT"
    SYSTEM = "SYSTEM"


class AdminActionType(str, Enum):
    ACTIVATE_DONOR = "ACTIVATE_DONOR"
    DEACTIVATE_DONOR = "DEACTIVATE_DONOR"
    DELETE_DONOR = "DELETE_DONOR"
    UPDATE_AVAILABILITY = "UPDATE_AVAILABILITY"
    RESOLVE_REPORT = "RESOLVE_REPORT"
    DISMISS_REPORT = "DISMISS_REPORT"
    PROMOTE = "PROMOTE"
    DEMOTE = "DEMOTE"
    OTHER = "OTHER"

