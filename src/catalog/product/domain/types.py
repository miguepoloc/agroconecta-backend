"""Product domain enumerations."""

import enum


class ProductCategory(enum.StrEnum):
    FRUTAS = "frutas"
    VERDURAS = "verduras"
    TUBERCULOS = "tuberculos"
    HIERBAS = "hierbas"
    GRANOS = "granos"
    LACTEOS = "lacteos"
    OTROS = "otros"


class ProductUnit(enum.StrEnum):
    KG = "kg"
    UNIDAD = "unidad"
    LIBRA = "libra"
    ARROBA = "arroba"
