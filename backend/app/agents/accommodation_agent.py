"""
Accommodation Agent for hotel and lodging recommendations.
"""

from datetime import datetime, date
from typing import Any, Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.prompts.base_prompts import get_accommodation_system_prompt
from app.ai_providers import AIMessage
from app.integrations.booking_api import search_hotels, HotelSearchResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class AccommodationAgent(BaseAgent):
    """Agent for hotel and accommodation recommendations."""

    def __init__(self):
        super().__init__(
            name="accommodation",
            description="Tư vấn và gợi ý khách sạn, resort, homestay phù hợp"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt with context information."""
        context_info = ""

        if context.trip_data:
            context_info = f"""
Thông tin chuyến đi hiện tại:
- Điểm đến: {context.trip_data.get('destination', 'Chưa xác định')}
- Ngày đi: {context.trip_data.get('start_date', 'Chưa xác định')}
- Ngày về: {context.trip_data.get('end_date', 'Chưa xác định')}
- Số người: {context.trip_data.get('travelers_count', 1)}
- Ngân sách: {context.trip_data.get('budget', 'Chưa xác định')} VND
"""

        return get_accommodation_system_prompt(context_info)

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process accommodation request."""
        start_time = datetime.utcnow()

        try:
            # Extract entities from user message
            entities = self.extract_entities(context.message)

            # Check if we have enough information for hotel search
            can_search = self._can_perform_search(context, entities)

            if can_search:
                # Perform hotel search
                hotels = await self._search_hotels(context, entities)

                if hotels:
                    # Generate response with hotel recommendations
                    response = await self._generate_hotel_response(
                        context, hotels, entities
                    )
                else:
                    # No results, ask for more info
                    response = await self._generate_clarification_response(context)
            else:
                # Need more information
                response = await self._generate_info_gathering_response(
                    context, entities
                )

            # Log interaction
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                "accommodation_agent_processed",
                user_id=context.user_id,
                trip_id=context.trip_id,
                has_results=can_search and bool(response.data),
                duration_ms=duration
            )

            return response

        except Exception as e:
            self.logger.error(
                "accommodation_agent_error",
                error=str(e),
                user_id=context.user_id
            )
            return AgentResponse(
                message="Xin lỗi, tôi gặp sự cố khi tìm kiếm khách sạn. Bạn có thể thử lại được không?",
                agent_type=self.name,
                suggestions=["Thử tìm kiếm lại", "Thay đổi điều kiện tìm kiếm"]
            )

    def _can_perform_search(
        self,
        context: AgentContext,
        entities: dict
    ) -> bool:
        """Check if we have enough info for hotel search."""
        # Need at least location
        has_location = bool(entities.get("locations"))
        if not has_location and context.trip_data:
            has_location = bool(context.trip_data.get("destination"))

        return has_location

    async def _search_hotels(
        self,
        context: AgentContext,
        entities: dict
    ) -> list[HotelSearchResult]:
        """Search for hotels based on context."""
        # Get search parameters
        location = (
            entities.get("locations", [""])[0] or
            context.trip_data.get("destination", "") if context.trip_data else ""
        )

        # Default dates if not provided
        if context.trip_data:
            check_in = context.trip_data.get("start_date", date.today())
            check_out = context.trip_data.get("end_date", date.today())
            if isinstance(check_in, str):
                check_in = date.fromisoformat(check_in)
            if isinstance(check_out, str):
                check_out = date.fromisoformat(check_out)
        else:
            check_in = date.today()
            check_out = date.today()

        travelers = entities.get("travelers") or (
            context.trip_data.get("travelers_count", 2) if context.trip_data else 2
        )

        # Search hotels
        hotels = await search_hotels(
            location=location,
            check_in=check_in,
            check_out=check_out,
            adults=travelers,
            limit=5
        )

        return hotels

    async def _generate_hotel_response(
        self,
        context: AgentContext,
        hotels: list[HotelSearchResult],
        entities: dict
    ) -> AgentResponse:
        """Generate response with hotel recommendations."""
        # Format hotels for AI
        hotels_info = self._format_hotels_for_ai(hotels)

        # Create messages for AI
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\nKết quả tìm kiếm khách sạn:\n{hotels_info}"
        ))

        # Get AI response
        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        # Convert hotels to dict for response data
        hotels_data = [
            {
                "name": h.name,
                "type": h.type,
                "address": h.address,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "price_per_night": h.price_per_night,
                "currency": h.currency,
                "rating": h.rating,
                "review_count": h.review_count,
                "image_url": h.image_url,
                "amenities": h.amenities,
                "booking_url": h.booking_url,
            }
            for h in hotels
        ]

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"accommodations": hotels_data},
            suggestions=[
                "Xem chi tiết khách sạn này",
                "Tìm khách sạn khác",
                "Đặt phòng ngay"
            ]
        )

    async def _generate_info_gathering_response(
        self,
        context: AgentContext,
        entities: dict
    ) -> AgentResponse:
        """Generate response to gather more information."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        # Add instruction to gather info
        system_prompt = self.get_system_prompt(context)
        system_prompt += """

Người dùng chưa cung cấp đủ thông tin để tìm khách sạn.
Hãy hỏi thêm về:
- Địa điểm muốn ở
- Ngày check-in và check-out
- Số lượng người
- Ngân sách
- Loại chỗ ở ưa thích

Hỏi tự nhiên và thân thiện, không liệt kê tất cả cùng lúc."""

        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            requires_followup=True,
            suggestions=[
                "Tôi muốn ở khách sạn 4 sao",
                "Ngân sách khoảng 1 triệu/đêm",
                "Cần gần trung tâm"
            ]
        )

    async def _generate_clarification_response(
        self,
        context: AgentContext
    ) -> AgentResponse:
        """Generate response when no results found."""
        return AgentResponse(
            message="Tôi không tìm thấy khách sạn phù hợp với yêu cầu của bạn. "
                    "Bạn có thể thử:\n"
                    "- Mở rộng phạm vi giá\n"
                    "- Chọn khu vực khác\n"
                    "- Thay đổi ngày lưu trú",
            agent_type=self.name,
            suggestions=[
                "Tăng ngân sách",
                "Tìm ở khu vực khác",
                "Đổi ngày"
            ]
        )

    def _format_hotels_for_ai(self, hotels: list[HotelSearchResult]) -> str:
        """Format hotel results for AI context."""
        lines = []
        for i, hotel in enumerate(hotels, 1):
            amenities_str = ", ".join(hotel.amenities) if hotel.amenities else "N/A"
            lines.append(
                f"{i}. {hotel.name}\n"
                f"   - Loại: {hotel.type}\n"
                f"   - Giá: {hotel.price_per_night:,.0f} VND/đêm\n"
                f"   - Đánh giá: {hotel.rating}/5 ({hotel.review_count} reviews)\n"
                f"   - Địa chỉ: {hotel.address}\n"
                f"   - Tiện nghi: {amenities_str}\n"
            )
        return "\n".join(lines)
