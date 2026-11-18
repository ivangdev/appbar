"""Schemas del reporte diario (corte de caja)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


class ReportByTable(BaseModel):
    """Total vendido (pagado) por mesa."""

    table_number: int
    total: int


class ReportByProduct(BaseModel):
    """Unidades y recaudo por producto."""

    name: str
    qty: int
    revenue: int


class DailyReport(BaseModel):
    """Corte del dia (TZ America/Bogota). Solo ordenes pagadas."""

    date: dt.date
    total: int
    by_table: list[ReportByTable] = Field(default_factory=list)
    by_product: list[ReportByProduct] = Field(default_factory=list)
