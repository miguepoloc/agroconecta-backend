"""Farmer domain enumerations."""

import enum


class ComplianceStatus(enum.StrEnum):
    ACTIVE = "active"
    RENEWAL_NEEDED = "renewal_needed"
    EXPIRED = "expired"


class SustainabilityRank(enum.StrEnum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class CertificationType(enum.StrEnum):
    GLOBAL_GAP = "GlobalGAP"
    FAIR_TRADE = "FairTrade"
    ICA = "ICA"
    INVIMA = "INVIMA"
    ORGANICO = "Orgánico"
