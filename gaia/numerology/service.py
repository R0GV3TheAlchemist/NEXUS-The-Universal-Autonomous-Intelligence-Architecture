"""NumerologyService — persistence + orchestration layer.

Coordinates between NumerologyEngine (pure computation) and the
SQLAlchemy ORM models.  All database interaction lives here.

Usage example::

    async with AsyncSession(engine) as session:
        svc = NumerologyService(session)
        chart = await svc.get_or_create_chart(
            full_name="Nikola Tesla",
            birth_date=date(1856, 7, 10),
            user_id=current_user.id,
        )
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from gaia.db.models.numerology import (
    NumerologyChart,
    NumerologyNumber,
    NumerologyProfile,
)
from gaia.numerology.engine import ChartResult, NumerologyEngine


class NumerologyService:
    """Stateful service — one instance per request/session."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._engine = NumerologyEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_or_create_chart(
        self,
        full_name: str,
        birth_date: date,
        user_id: Optional[uuid.UUID] = None,
        system: str = "pythagorean",
        force_recompute: bool = False,
        cycle_years: int = 3,
    ) -> NumerologyChart:
        """Return the latest chart for this name+date, creating if absent.

        Args:
            full_name:       Birth name (will be normalised internally).
            birth_date:      Date of birth.
            user_id:         Gaian user UUID; None for anonymous charts.
            system:          Numerology system (only 'pythagorean' for now).
            force_recompute: Always create a fresh chart even if one exists.
            cycle_years:     How many future years to include in personal_year_cycle
                             (0 to omit, max 9). Stored in raw_chart JSONB.
        """
        profile = await self._get_or_create_profile(
            full_name=full_name,
            birth_date=birth_date,
            user_id=user_id,
            system=system,
        )

        if not force_recompute and profile.latest_chart is not None:
            return profile.latest_chart

        return await self._create_chart(profile, cycle_years=cycle_years)

    async def get_chart_by_id(
        self, chart_id: uuid.UUID
    ) -> Optional[NumerologyChart]:
        """Fetch a chart by primary key, eagerly loading numbers."""
        stmt = (
            select(NumerologyChart)
            .where(NumerologyChart.id == chart_id)
            .options(
                selectinload(NumerologyChart.numbers),
                selectinload(NumerologyChart.profile),
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_charts_for_user(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[NumerologyChart]:
        """Return the most recent charts for a given user across all their profiles."""
        stmt = (
            select(NumerologyChart)
            .join(NumerologyChart.profile)
            .where(
                NumerologyProfile.user_id == user_id,
                NumerologyProfile.deleted_at.is_(None),
            )
            .options(
                selectinload(NumerologyChart.numbers),
                selectinload(NumerologyChart.profile),
            )
            .order_by(NumerologyChart.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_profile(
        self, profile_id: uuid.UUID, hard: bool = False
    ) -> bool:
        """Soft-delete (default) or hard-delete a profile and its charts.

        Soft-delete sets deleted_at; hard-delete removes the row entirely
        (use only under explicit Right to Be Forgotten request per C139).
        """
        stmt = select(NumerologyProfile).where(NumerologyProfile.id == profile_id)
        result = await self._db.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            return False

        if hard:
            await self._db.delete(profile)
        else:
            profile.soft_delete()
            self._db.add(profile)

        await self._db.flush()
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_or_create_profile(
        self,
        full_name: str,
        birth_date: date,
        user_id: Optional[uuid.UUID],
        system: str,
    ) -> NumerologyProfile:
        """Return an existing active profile or create a new one."""
        normalized = self._engine.normalize_name(full_name)

        stmt = (
            select(NumerologyProfile)
            .where(
                NumerologyProfile.normalized_name == normalized,
                NumerologyProfile.birth_date == birth_date,
                NumerologyProfile.system == system,
                NumerologyProfile.deleted_at.is_(None),
            )
            .options(selectinload(NumerologyProfile.charts))
            .limit(1)
        )
        if user_id is not None:
            stmt = stmt.where(NumerologyProfile.user_id == user_id)

        result = await self._db.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile is not None:
            return profile

        profile = NumerologyProfile(
            user_id=user_id,
            full_name=full_name,
            normalized_name=normalized,
            birth_date=birth_date,
            system=system,
        )
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def _create_chart(
        self,
        profile: NumerologyProfile,
        cycle_years: int = 3,
    ) -> NumerologyChart:
        """Compute a fresh chart and persist it with all number rows.

        Args:
            profile:     The NumerologyProfile ORM row this chart belongs to.
            cycle_years: Passed through to engine.compute() to control how many
                         future years appear in personal_year_cycle inside raw_chart.
        """
        computed: ChartResult = self._engine.compute(
            full_name=profile.full_name,
            birth_date=profile.birth_date,
            system=profile.system,
            cycle_years=cycle_years,
        )

        chart = NumerologyChart(
            profile_id=profile.id,
            life_path=computed.life_path.reduced_value,
            expression=computed.expression.reduced_value,
            soul_urge=computed.soul_urge.reduced_value,
            personality=computed.personality.reduced_value,
            birthday=computed.birthday.reduced_value,
            personal_year=computed.personal_year.reduced_value,
            computed_for_year=date.today().year,
            life_path_is_master=computed.life_path.is_master_number,
            expression_is_master=computed.expression.is_master_number,
            soul_urge_is_master=computed.soul_urge.is_master_number,
            raw_chart=computed.as_dict(),
        )
        self._db.add(chart)
        await self._db.flush()

        core_results = [
            computed.life_path,
            computed.expression,
            computed.soul_urge,
            computed.personality,
            computed.birthday,
            computed.personal_year,
            *computed.challenges,
        ]
        for nr in core_results:
            num = NumerologyNumber(
                chart_id=chart.id,
                number_type=nr.number_type,
                raw_value=nr.raw_value,
                reduced_value=nr.reduced_value,
                is_master_number=nr.is_master_number,
                reduction_path=nr.reduction_path,
            )
            self._db.add(num)

        await self._db.flush()
        return chart
