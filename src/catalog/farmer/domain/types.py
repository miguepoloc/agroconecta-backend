"""Farmer domain enumerations."""

import enum


class ComplianceStatus(str, enum.Enum):
    ACTIVE = "active"
    RENEWAL_NEEDED = "renewal_needed"
    EXPIRED = "expired"


class SustainabilityRank(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class CertificationType(str, enum.Enum):
    GLOBAL_GAP = "GlobalGAP"
    FAIR_TRADE = "FairTrade"
    ICA = "ICA"
    INVIMA = "INVIMA"
    ORGANICO = "Orgánico"
