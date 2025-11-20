"""
Hotel booking API integrations.

Integrates with booking platforms via RapidAPI for hotel search.
"""

from typing import Optional
from datetime import date
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class HotelSearchResult(BaseModel):
    """Normalized hotel search result."""

    name: str
    type: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_night: float
    currency: str = "VND"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    amenities: list[str] = []
    booking_url: Optional[str] = None
    source: str = "api"


class BookingAPIClient:
    """Client for hotel booking API integrations."""

    def __init__(self):
        self.rapidapi_key = settings.RAPIDAPI_KEY
        self.base_url = "https://booking-com.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
        }

    async def search_hotels(
        self,
        location: str,
        check_in: date,
        check_out: date,
        adults: int = 2,
        rooms: int = 1,
        currency: str = "VND",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        hotel_type: Optional[str] = None,
        limit: int = 10
    ) -> list[HotelSearchResult]:
        """
        Search for hotels using booking API.

        Args:
            location: City or location name
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            rooms: Number of rooms
            currency: Currency code
            min_price: Minimum price filter
            max_price: Maximum price filter
            hotel_type: Type of accommodation
            limit: Maximum results to return

        Returns:
            List of normalized hotel results
        """
        # If no API key, return mock data for development
        if not self.rapidapi_key:
            logger.warning("No RapidAPI key configured, returning mock data")
            return self._get_mock_hotels(location, check_in, check_out)

        try:
            # First, get destination ID
            dest_id = await self._get_destination_id(location)
            if not dest_id:
                logger.error(f"Could not find destination: {location}")
                return self._get_mock_hotels(location, check_in, check_out)

            # Search hotels
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/hotels/search",
                    headers=self.headers,
                    params={
                        "dest_id": dest_id,
                        "dest_type": "city",
                        "checkin_date": check_in.isoformat(),
                        "checkout_date": check_out.isoformat(),
                        "adults_number": adults,
                        "room_number": rooms,
                        "order_by": "popularity",
                        "units": "metric",
                        "filter_by_currency": currency,
                        "locale": "vi",
                        "page_number": 0,
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Hotel search API error: {response.status_code}")
                    return self._get_mock_hotels(location, check_in, check_out)

                data = response.json()
                results = []

                for hotel in data.get("result", [])[:limit]:
                    result = HotelSearchResult(
                        name=hotel.get("hotel_name", "Unknown"),
                        type=hotel.get("accommodation_type_name", "Hotel"),
                        address=hotel.get("address", ""),
                        latitude=hotel.get("latitude"),
                        longitude=hotel.get("longitude"),
                        price_per_night=hotel.get("min_total_price", 0),
                        currency=currency,
                        rating=hotel.get("review_score", 0) / 2,  # Convert to 5-star
                        review_count=hotel.get("review_nr"),
                        image_url=hotel.get("main_photo_url"),
                        amenities=self._extract_amenities(hotel),
                        booking_url=hotel.get("url"),
                        source="booking.com"
                    )
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Hotel search error: {e}")
            return self._get_mock_hotels(location, check_in, check_out)

    async def _get_destination_id(self, location: str) -> Optional[str]:
        """Get destination ID for a location."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/hotels/locations",
                    headers=self.headers,
                    params={"name": location, "locale": "vi"}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return data[0].get("dest_id")

        except Exception as e:
            logger.error(f"Destination lookup error: {e}")

        return None

    def _extract_amenities(self, hotel: dict) -> list[str]:
        """Extract amenities from hotel data."""
        amenities = []
        if hotel.get("has_free_parking"):
            amenities.append("Bãi đỗ xe miễn phí")
        if hotel.get("has_swimming_pool"):
            amenities.append("Hồ bơi")
        if hotel.get("is_free_cancellable"):
            amenities.append("Hủy miễn phí")
        return amenities

    def _get_mock_hotels(
        self,
        location: str,
        check_in: date,
        check_out: date
    ) -> list[HotelSearchResult]:
        """Return mock hotel data for development."""
        nights = (check_out - check_in).days

        mock_hotels = [
            HotelSearchResult(
                name=f"Khách sạn Mường Thanh {location}",
                type="Khách sạn 4 sao",
                address=f"123 Đường chính, {location}",
                latitude=21.0285,
                longitude=105.8542,
                price_per_night=1200000,
                rating=4.2,
                review_count=1250,
                image_url="https://example.com/hotel1.jpg",
                amenities=["Wifi miễn phí", "Hồ bơi", "Nhà hàng", "Phòng gym"],
                booking_url="https://booking.com/hotel/muongthanh",
                source="mock"
            ),
            HotelSearchResult(
                name=f"Vinpearl Resort {location}",
                type="Resort 5 sao",
                address=f"Bãi biển đẹp, {location}",
                latitude=21.0295,
                longitude=105.8552,
                price_per_night=3500000,
                rating=4.8,
                review_count=3200,
                image_url="https://example.com/hotel2.jpg",
                amenities=["Wifi miễn phí", "Hồ bơi vô cực", "Spa", "Sân golf"],
                booking_url="https://booking.com/hotel/vinpearl",
                source="mock"
            ),
            HotelSearchResult(
                name=f"Little {location} Homestay",
                type="Homestay",
                address=f"45 Phố cổ, {location}",
                latitude=21.0275,
                longitude=105.8532,
                price_per_night=450000,
                rating=4.5,
                review_count=890,
                image_url="https://example.com/hotel3.jpg",
                amenities=["Wifi miễn phí", "Bếp chung", "Sân thượng"],
                booking_url="https://booking.com/hotel/littlehomestay",
                source="mock"
            ),
        ]

        return mock_hotels


# Global client instance
booking_client = BookingAPIClient()


async def search_hotels(
    location: str,
    check_in: date,
    check_out: date,
    **kwargs
) -> list[HotelSearchResult]:
    """Convenience function for hotel search."""
    return await booking_client.search_hotels(
        location, check_in, check_out, **kwargs
    )
