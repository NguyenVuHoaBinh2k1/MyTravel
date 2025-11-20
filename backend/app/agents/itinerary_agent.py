"""
Itinerary Agent for trip planning and scheduling.
"""

from datetime import datetime, date, timedelta
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.prompts.base_prompts import get_itinerary_system_prompt
from app.ai_providers import AIMessage
from app.integrations.google_maps import search_attractions
from app.core.logging import get_logger

logger = get_logger(__name__)


class ItineraryAgent(BaseAgent):
    """Agent for itinerary planning and optimization."""

    def __init__(self):
        super().__init__(
            name="itinerary",
            description="Lập lịch trình du lịch tối ưu theo ngày"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt with context."""
        context_info = ""
        if context.trip_data:
            start = context.trip_data.get('start_date', '')
            end = context.trip_data.get('end_date', '')

            if start and end:
                try:
                    if isinstance(start, str):
                        start_date = date.fromisoformat(start)
                    else:
                        start_date = start
                    if isinstance(end, str):
                        end_date = date.fromisoformat(end)
                    else:
                        end_date = end
                    days = (end_date - start_date).days + 1
                except:
                    days = "N/A"
            else:
                days = "N/A"

            context_info = f"""
Thông tin chuyến đi:
- Điểm đến: {context.trip_data.get('destination', 'Chưa xác định')}
- Thời gian: {start} đến {end} ({days} ngày)
- Số người: {context.trip_data.get('travelers_count', 1)}
- Ngân sách: {context.trip_data.get('budget', 'Chưa xác định')} VND
"""
        return get_itinerary_system_prompt(context_info)

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process itinerary request."""
        start_time = datetime.utcnow()

        try:
            entities = self.extract_entities(context.message)
            intent = self._determine_intent(context.message)

            if intent == "create_itinerary":
                response = await self._create_itinerary(context, entities)
            elif intent == "modify_itinerary":
                response = await self._modify_itinerary(context, entities)
            elif intent == "find_attractions":
                response = await self._find_attractions(context, entities)
            else:
                response = await self._handle_general_query(context, entities)

            end_time = datetime.utcnow()
            self.logger.info(
                "itinerary_agent_processed",
                user_id=context.user_id,
                intent=intent,
                duration_ms=(end_time - start_time).total_seconds() * 1000
            )

            return response

        except Exception as e:
            self.logger.error("itinerary_agent_error", error=str(e))
            return AgentResponse(
                message="Xin lỗi, tôi gặp sự cố khi lập lịch trình. Bạn có thể thử lại?",
                agent_type=self.name,
                suggestions=["Tạo lịch trình mới", "Tìm điểm tham quan"]
            )

    def _determine_intent(self, message: str) -> str:
        """Determine user intent."""
        message_lower = message.lower()

        create_keywords = ["lập lịch", "tạo lịch", "kế hoạch", "schedule", "itinerary", "plan"]
        modify_keywords = ["thay đổi", "sửa", "đổi", "thêm", "bớt", "modify"]
        attraction_keywords = ["điểm tham quan", "đi đâu", "xem gì", "attraction", "visit"]

        for kw in create_keywords:
            if kw in message_lower:
                return "create_itinerary"

        for kw in modify_keywords:
            if kw in message_lower:
                return "modify_itinerary"

        for kw in attraction_keywords:
            if kw in message_lower:
                return "find_attractions"

        return "general"

    async def _create_itinerary(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Create a new itinerary."""
        destination = (
            entities.get("locations", [""])[0] or
            context.trip_data.get("destination", "") if context.trip_data else ""
        )

        # Search for attractions
        attractions = []
        if destination:
            attractions = await search_attractions(destination, limit=10)

        # Format attractions for AI
        attractions_info = ""
        if attractions:
            attractions_info = "\n\nĐiểm tham quan tìm được:\n"
            for i, attr in enumerate(attractions, 1):
                attractions_info += f"{i}. {attr.name} - {attr.address} (Rating: {attr.rating})\n"

        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}{attractions_info}"
        ))

        system_prompt = self.get_system_prompt(context)
        system_prompt += """

Khi tạo lịch trình, hãy:
1. Chia theo từng ngày
2. Sắp xếp các điểm gần nhau
3. Dành thời gian cho ăn uống và nghỉ ngơi
4. Ghi rõ giờ bắt đầu và kết thúc mỗi hoạt động
5. Tính thời gian di chuyển giữa các điểm
"""

        ai_response = await self.call_ai(messages, system_prompt)

        # Format activities data
        activities_data = []
        if attractions:
            for i, attr in enumerate(attractions[:5]):
                activities_data.append({
                    "name": attr.name,
                    "location": attr.address,
                    "latitude": attr.latitude,
                    "longitude": attr.longitude,
                    "rating": attr.rating,
                    "category": "sightseeing",
                    "suggested_duration": 90,
                })

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"activities": activities_data} if activities_data else None,
            suggestions=["Thêm hoạt động", "Điều chỉnh thời gian", "Xem bản đồ"]
        )

    async def _modify_itinerary(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Modify existing itinerary."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=["Xem lịch trình mới", "Thay đổi tiếp", "Hoàn tất"]
        )

    async def _find_attractions(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Find attractions for the destination."""
        destination = (
            entities.get("locations", [""])[0] or
            context.trip_data.get("destination", "") if context.trip_data else ""
        )

        attractions = []
        if destination:
            attractions = await search_attractions(destination, limit=8)

        if attractions:
            attractions_info = "Điểm tham quan tại " + destination + ":\n"
            for i, attr in enumerate(attractions, 1):
                attractions_info += f"{i}. {attr.name}\n   - {attr.address}\n   - Đánh giá: {attr.rating}/5\n\n"

            messages = self.format_conversation_history(context.conversation_history)
            messages.append(AIMessage(
                role="user",
                content=f"{context.message}\n\n{attractions_info}"
            ))

            system_prompt = self.get_system_prompt(context)
            ai_response = await self.call_ai(messages, system_prompt)

            return AgentResponse(
                message=ai_response.content,
                agent_type=self.name,
                data={"attractions": [{"name": a.name, "address": a.address, "rating": a.rating} for a in attractions]},
                suggestions=["Thêm vào lịch trình", "Tìm thêm", "Tạo lịch trình"]
            )
        else:
            return await self._handle_general_query(context, entities)

    async def _handle_general_query(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Handle general itinerary queries."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=["Tạo lịch trình", "Tìm điểm tham quan", "Gợi ý hoạt động"]
        )
