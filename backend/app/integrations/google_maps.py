"""
Google Maps API integration for places and directions.
"""

from typing import Optional
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlaceResult(BaseModel):
    """Normalized place search result."""

    name: str
    address: str
    latitude: float
    longitude: float
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None  # 0-4
    types: list[str] = []
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    place_id: Optional[str] = None


class GoogleMapsClient:
    """Client for Google Maps API."""

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def search_places(
        self,
        query: str,
        location: Optional[tuple[float, float]] = None,
        radius: int = 5000,
        place_type: Optional[str] = None,
        limit: int = 10
    ) -> list[PlaceResult]:
        """
        Search for places using Google Places API.

        Args:
            query: Search query
            location: (lat, lng) tuple for location bias
            radius: Search radius in meters
            place_type: Type of place (restaurant, tourist_attraction, etc.)
            limit: Maximum results

        Returns:
            List of place results
        """
        if not self.api_key:
            logger.warning("No Google Maps API key, returning mock data")
            return self._get_mock_places(query)

        try:
            params = {
                "query": query,
                "key": self.api_key,
                "language": "vi",
            }

            if location:
                params["location"] = f"{location[0]},{location[1]}"
                params["radius"] = radius

            if place_type:
                params["type"] = place_type

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/place/textsearch/json",
                    params=params
                )

                if response.status_code != 200:
                    logger.error(f"Places API error: {response.status_code}")
                    return self._get_mock_places(query)

                data = response.json()

                if data.get("status") != "OK":
                    logger.error(f"Places API status: {data.get('status')}")
                    return self._get_mock_places(query)

                results = []
                for place in data.get("results", [])[:limit]:
                    result = PlaceResult(
                        name=place.get("name", ""),
                        address=place.get("formatted_address", ""),
                        latitude=place["geometry"]["location"]["lat"],
                        longitude=place["geometry"]["location"]["lng"],
                        rating=place.get("rating"),
                        review_count=place.get("user_ratings_total"),
                        price_level=place.get("price_level"),
                        types=place.get("types", []),
                        place_id=place.get("place_id"),
                    )

                    # Get photo URL if available
                    if place.get("photos"):
                        photo_ref = place["photos"][0].get("photo_reference")
                        result.image_url = (
                            f"{self.base_url}/place/photo"
                            f"?maxwidth=400&photo_reference={photo_ref}&key={self.api_key}"
                        )

                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Places search error: {e}")
            return self._get_mock_places(query)

    async def get_place_details(self, place_id: str) -> Optional[PlaceResult]:
        """Get detailed information about a place."""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/place/details/json",
                    params={
                        "place_id": place_id,
                        "key": self.api_key,
                        "language": "vi",
                        "fields": "name,formatted_address,geometry,rating,"
                                  "user_ratings_total,price_level,types,"
                                  "opening_hours,formatted_phone_number,website,photos"
                    }
                )

                if response.status_code != 200:
                    return None

                data = response.json()
                if data.get("status") != "OK":
                    return None

                place = data.get("result", {})
                return PlaceResult(
                    name=place.get("name", ""),
                    address=place.get("formatted_address", ""),
                    latitude=place["geometry"]["location"]["lat"],
                    longitude=place["geometry"]["location"]["lng"],
                    rating=place.get("rating"),
                    review_count=place.get("user_ratings_total"),
                    price_level=place.get("price_level"),
                    types=place.get("types", []),
                    opening_hours=self._format_opening_hours(
                        place.get("opening_hours", {})
                    ),
                    phone=place.get("formatted_phone_number"),
                    website=place.get("website"),
                    place_id=place_id,
                )

        except Exception as e:
            logger.error(f"Place details error: {e}")
            return None

    async def search_restaurants(
        self,
        location: str,
        cuisine_type: Optional[str] = None,
        limit: int = 10
    ) -> list[PlaceResult]:
        """Search for restaurants in a location."""
        query = f"nhà hàng {cuisine_type or ''} {location}".strip()
        return await self.search_places(
            query=query,
            place_type="restaurant",
            limit=limit
        )

    async def search_attractions(
        self,
        location: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> list[PlaceResult]:
        """Search for tourist attractions."""
        query = f"{category or 'điểm tham quan'} {location}".strip()
        return await self.search_places(
            query=query,
            place_type="tourist_attraction",
            limit=limit
        )

    def _format_opening_hours(self, hours_data: dict) -> Optional[str]:
        """Format opening hours from API response."""
        if not hours_data:
            return None

        weekday_text = hours_data.get("weekday_text", [])
        if weekday_text:
            return "; ".join(weekday_text[:3]) + "..."

        return "Xem chi tiết trên Google Maps"

    def _get_mock_places(self, query: str) -> list[PlaceResult]:
        """Return mock place data for development."""
        return [
            PlaceResult(
                name="Phở Thìn Bờ Hồ",
                address="13 Lò Đúc, Hai Bà Trưng, Hà Nội",
                latitude=21.0245,
                longitude=105.8512,
                rating=4.5,
                review_count=2500,
                price_level=1,
                types=["restaurant", "food"],
                opening_hours="6:00 - 20:30",
                phone="024 3821 2709",
            ),
            PlaceResult(
                name="Bún Chả Hương Liên",
                address="24 Lê Văn Hưu, Hai Bà Trưng, Hà Nội",
                latitude=21.0155,
                longitude=105.8492,
                rating=4.3,
                review_count=3800,
                price_level=1,
                types=["restaurant", "food"],
                opening_hours="8:00 - 20:00",
                phone="024 3943 4106",
            ),
            PlaceResult(
                name="Chả Cá Lã Vọng",
                address="14 Chả Cá, Hoàn Kiếm, Hà Nội",
                latitude=21.0335,
                longitude=105.8482,
                rating=4.1,
                review_count=1200,
                price_level=2,
                types=["restaurant", "food"],
                opening_hours="11:00 - 14:00, 17:00 - 21:00",
                phone="024 3825 3929",
            ),
        ]


# Global client instance
google_maps_client = GoogleMapsClient()


async def search_restaurants(
    location: str,
    cuisine_type: Optional[str] = None,
    **kwargs
) -> list[PlaceResult]:
    """Convenience function for restaurant search."""
    return await google_maps_client.search_restaurants(
        location, cuisine_type, **kwargs
    )


async def search_attractions(
    location: str,
    category: Optional[str] = None,
    **kwargs
) -> list[PlaceResult]:
    """Convenience function for attraction search."""
    return await google_maps_client.search_attractions(
        location, category, **kwargs
    )
