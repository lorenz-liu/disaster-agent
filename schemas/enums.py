from enum import Enum


class SimulationSessionStatusEnum(str, Enum):
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    DISCARDED = "Discarded"
    DELETED = "Deleted"


class SimulationRoleEnum(str, Enum):
    COMMANDER = "Commander"
    DISASTER_COORDINATOR = "Disaster Coordinator"
    TRAUMA_TEAM_LEADER = "Trauma Team Leader"


class IncidentTypeEnum(str, Enum):
    MASS_CASUALTY_INCIDENT = "MCI"
    MEDICAL_EVACUATION = "MEDEVAC"
    PUBLIC_HEALTH_EMERGENCY = "PHE"


class HealthcareFacilityLevelEnum(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3


class PatientSeverityEnum(str, Enum):
    """SALT Triage Categories"""
    DEAD = "Dead"  # Not breathing even after opening airway
    EXPECTANT = "Expectant"  # Unlikely to survive given resource constraints
    IMMEDIATE = "Immediate"  # Likely to survive with immediate care
    DELAYED = "Delayed"  # Serious injuries, can wait for care
    MINIMAL = "Minimal"  # Minor injuries only
    UNDEFINED = "Undefined"  # Not yet triaged


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"


class PatientInjuryMechanismEnum(str, Enum):
    BLUNT = "Blunt"
    PENETRATING = "Penetrating"
    THERMAL = "Thermal"
    BLAST = "Blast"
    DROWNING = "Drowning"
    CHEMICAL = "Chemical"
    RADIATION = "Radiation"
    ELECTRICAL = "Electrical"
    HYPOTHERMIA = "Hypothermia"
    OTHER = "Other"


class PatientInjuryLocationEnum(str, Enum):
    HEAD = "Head"
    NECK = "Neck"
    CHEST = "Chest"
    BACK = "Back"
    PELVIS = "Pelvis"
    ABDOMEN = "Abdomen"
    UPPER_LIMBS = "Limbs (Upper)"
    LOWER_LIMBS = "Limbs (Lower)"


class PatientStatusEnum(str, Enum):
    UNASSIGNED = "Unassigned"
    AWAITING_TRANSFER = "Awaiting Transfer"
    IN_TRANSFER = "In-Transfer"
    ARRIVED = "Arrived"


class SimulationNotificationTypeEnum(str, Enum):
    INFO = "Info"
    SUCCESS = "Success"
    WARNING = "Warning"
    FATAL = "Fatal"


class AIDecisionTypeEnum(str, Enum):
    TRANSFER = "Transfer"
    FORFEIT = "Forfeit"
    WAIT = "Wait"
