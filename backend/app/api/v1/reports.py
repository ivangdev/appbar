"""Endpoints de reportes.

El corte del dia usa la zona horaria America/Bogota y solo cuenta ordenes
en estado `paid`.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import READ_ONLY_RATE_LIMIT
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.order import Order
from app.models.user import User
from app.schemas.report import DailyReport, ReportByProduct, ReportByTable

router = APIRouter(prefix="/reports", tags=["reports"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

BOGOTA = ZoneInfo("America/Bogota")


@router.get("/daily", response_model=DailyReport)
@limiter.limit(READ_ONLY_RATE_LIMIT)
def daily_report(
    request: Request,
    _user: CurrentUser,
    db: DbSession,
    date: Annotated[dt.date | None, Query()] = None,
) -> DailyReport:
    """Corte del dia (admin + mesero). Solo ordenes `paid`."""
    day = date or dt.datetime.now(BOGOTA).date()
    start = dt.datetime.combine(day, dt.time.min, tzinfo=BOGOTA)
    end = start + dt.timedelta(days=1)

    orders = db.scalars(
        select(Order).where(
            Order.status == "paid",
            Order.created_at >= start,
            Order.created_at < end,
        )
    ).all()

    total = 0
    by_table: dict[int, int] = {}
    by_product: dict[str, list[int]] = {}

    for order in orders:
        total += order.total_amount
        number = order.table.table_number
        by_table[number] = by_table.get(number, 0) + order.total_amount
        for item in order.items:
            name = item.product.name
            acc = by_product.setdefault(name, [0, 0])
            acc[0] += item.quantity
            acc[1] += item.total_price

    return DailyReport(
        date=day,
        total=total,
        by_table=[
            ReportByTable(table_number=number, total=amount)
            for number, amount in sorted(by_table.items())
        ],
        by_product=[
            ReportByProduct(name=name, qty=values[0], revenue=values[1])
            for name, values in sorted(by_product.items(), key=lambda kv: -kv[1][1])
        ],
    )
