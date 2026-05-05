"""Product domain enumerations."""

import enum


class ProductCategory(str, enum.Enum):
    FRUTAS = "frutas"
    VERDURAS = "verduras"
    TUBERCULOS = "tuberculos"
    HIERBAS = "hierbas"
    GRANOS = "granos"
    LACTEOS = "lacteos"
    OTROS = "otros"


class ProductUnit(str, enum.Enum):
    KG = "kg"
    UNIDAD = "unidad"
    LIBRA = "libra"
    ARROBA = "arroba"
