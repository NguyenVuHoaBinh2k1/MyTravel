"""
Export API endpoints for trip data.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime
from io import BytesIO

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services import trip_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/trips/{trip_id}/export/json")
async def export_trip_json(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export trip data as JSON."""
    trip = await trip_service.get_trip(db, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this trip"
        )

    # Build export data
    export_data = {
        "trip": {
            "id": trip.id,
            "title": trip.title,
            "destination": trip.destination,
            "start_date": str(trip.start_date) if trip.start_date else None,
            "end_date": str(trip.end_date) if trip.end_date else None,
            "travelers_count": trip.travelers_count,
            "budget": float(trip.budget) if trip.budget else None,
            "currency": trip.currency,
            "status": trip.status,
            "notes": trip.notes,
        },
        "accommodations": [
            {
                "name": acc.name,
                "type": acc.type,
                "address": acc.address,
                "check_in_date": str(acc.check_in_date),
                "check_out_date": str(acc.check_out_date),
                "price_per_night": float(acc.price_per_night),
                "total_price": float(acc.total_price),
                "currency": acc.currency,
                "booking_url": acc.booking_url,
                "status": acc.status,
                "rating": acc.rating,
                "amenities": acc.amenities,
                "notes": acc.notes,
            }
            for acc in trip.accommodations or []
        ],
        "restaurants": [
            {
                "name": rest.name,
                "cuisine_type": rest.cuisine_type,
                "address": rest.address,
                "price_range": rest.price_range,
                "rating": rest.rating,
                "specialty_dishes": rest.specialty_dishes,
                "opening_hours": rest.opening_hours,
                "phone": rest.phone,
                "status": rest.status,
                "notes": rest.notes,
            }
            for rest in trip.restaurants or []
        ],
        "transportations": [
            {
                "type": trans.type,
                "from_location": trans.from_location,
                "to_location": trans.to_location,
                "departure_time": str(trans.departure_time),
                "arrival_time": str(trans.arrival_time),
                "provider": trans.provider,
                "booking_reference": trans.booking_reference,
                "price": float(trans.price),
                "currency": trans.currency,
                "status": trans.status,
                "notes": trans.notes,
            }
            for trans in trip.transportations or []
        ],
        "activities": [
            {
                "name": act.name,
                "description": act.description,
                "location": act.location,
                "day_number": act.day_number,
                "start_time": act.start_time,
                "end_time": act.end_time,
                "duration_minutes": act.duration_minutes,
                "price": float(act.price) if act.price else None,
                "currency": act.currency,
                "category": act.category,
                "status": act.status,
                "rating": act.rating,
                "notes": act.notes,
            }
            for act in trip.activities or []
        ],
        "expenses": [
            {
                "category": exp.category,
                "description": exp.description,
                "amount": float(exp.amount),
                "currency": exp.currency,
                "date": str(exp.date),
                "is_planned": exp.is_planned,
                "notes": exp.notes,
            }
            for exp in trip.expenses or []
        ],
        "exported_at": datetime.utcnow().isoformat(),
        "exported_by": current_user.email,
    }

    # Convert to JSON
    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

    # Create filename
    filename = f"trip_{trip.destination}_{trip.start_date or 'draft'}.json"

    logger.info(
        "trip_exported_json",
        user_id=current_user.id,
        trip_id=trip_id
    )

    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/trips/{trip_id}/export/text")
async def export_trip_text(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export trip data as formatted text."""
    trip = await trip_service.get_trip(db, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this trip"
        )

    # Build text export
    lines = []
    lines.append("=" * 80)
    lines.append(f"{trip.title}".center(80))
    lines.append("=" * 80)
    lines.append("")

    # Trip details
    lines.append("THONG TIN CHUYEN DI")
    lines.append("-" * 80)
    lines.append(f"Diem den: {trip.destination}")
    if trip.start_date and trip.end_date:
        lines.append(f"Thoi gian: {trip.start_date} - {trip.end_date}")
    lines.append(f"So nguoi: {trip.travelers_count}")
    if trip.budget:
        lines.append(f"Ngan sach: {trip.budget:,.0f} {trip.currency}")
    lines.append(f"Trang thai: {trip.status}")
    if trip.notes:
        lines.append(f"Ghi chu: {trip.notes}")
    lines.append("")

    # Accommodations
    if trip.accommodations:
        lines.append("CHO O")
        lines.append("-" * 80)
        for acc in trip.accommodations:
            lines.append(f"• {acc.name} ({acc.type})")
            lines.append(f"  Dia chi: {acc.address}")
            lines.append(f"  Check-in: {acc.check_in_date} | Check-out: {acc.check_out_date}")
            lines.append(f"  Gia: {acc.price_per_night:,.0f} {acc.currency}/dem")
            if acc.amenities:
                lines.append(f"  Tien nghi: {', '.join(acc.amenities)}")
            lines.append("")

    # Restaurants
    if trip.restaurants:
        lines.append("NHA HANG")
        lines.append("-" * 80)
        for rest in trip.restaurants:
            lines.append(f"• {rest.name}")
            lines.append(f"  Loai hinh: {rest.cuisine_type}")
            lines.append(f"  Dia chi: {rest.address}")
            lines.append(f"  Gia: {rest.price_range}")
            if rest.specialty_dishes:
                lines.append(f"  Mon dac trung: {', '.join(rest.specialty_dishes)}")
            lines.append("")

    # Activities by day
    if trip.activities:
        lines.append("LICH TRINH")
        lines.append("-" * 80)

        # Group by day
        activities_by_day = {}
        for act in sorted(trip.activities, key=lambda a: (a.day_number, a.start_time)):
            if act.day_number not in activities_by_day:
                activities_by_day[act.day_number] = []
            activities_by_day[act.day_number].append(act)

        for day, activities in sorted(activities_by_day.items()):
            lines.append(f"\nNGAY {day}")
            for act in activities:
                lines.append(f"  {act.start_time}-{act.end_time}: {act.name}")
                if act.location:
                    lines.append(f"    Dia diem: {act.location}")
                if act.description:
                    lines.append(f"    Mo ta: {act.description}")
            lines.append("")

    # Transportation
    if trip.transportations:
        lines.append("DI CHUYEN")
        lines.append("-" * 80)
        for trans in trip.transportations:
            lines.append(f"• {trans.type.upper()}: {trans.from_location} → {trans.to_location}")
            lines.append(f"  Khoi hanh: {trans.departure_time}")
            lines.append(f"  Den noi: {trans.arrival_time}")
            if trans.provider:
                lines.append(f"  Nha cung cap: {trans.provider}")
            if trans.booking_reference:
                lines.append(f"  Ma dat cho: {trans.booking_reference}")
            lines.append(f"  Gia: {trans.price:,.0f} {trans.currency}")
            lines.append("")

    # Budget summary
    if trip.expenses:
        lines.append("TONG KET NGAN SACH")
        lines.append("-" * 80)

        total_planned = sum(exp.amount for exp in trip.expenses if exp.is_planned)
        total_actual = sum(exp.amount for exp in trip.expenses if not exp.is_planned)

        lines.append(f"Du kien: {total_planned:,.0f} {trip.currency}")
        lines.append(f"Thuc te: {total_actual:,.0f} {trip.currency}")
        if trip.budget:
            remaining = float(trip.budget) - total_actual
            lines.append(f"Con lai: {remaining:,.0f} {trip.currency}")
        lines.append("")

    lines.append("=" * 80)
    lines.append(f"Xuat du lieu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("=" * 80)

    text_data = "\n".join(lines)
    filename = f"trip_{trip.destination}_{trip.start_date or 'draft'}.txt"

    logger.info(
        "trip_exported_text",
        user_id=current_user.id,
        trip_id=trip_id
    )

    return Response(
        content=text_data.encode('utf-8'),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
