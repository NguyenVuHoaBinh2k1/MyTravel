"""
Transportation Agent for travel and transport recommendations.
"""

from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.prompts.base_prompts import get_transport_system_prompt
from app.ai_providers import AIMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


# Vietnamese transportation knowledge base
TRANSPORT_OPTIONS = {
    "inter_city": {
        "flight": {
            "providers": ["Vietnam Airlines", "Vietjet Air", "Bamboo Airways"],
            "typical_price": "800.000 - 3.000.000 VND",
            "booking_sites": ["vietnamairlines.com", "vietjetair.com", "bambooairways.com"]
        },
        "train": {
            "providers": ["Đường sắt Việt Nam"],
            "typical_price": "300.000 - 1.500.000 VND",
            "booking_sites": ["dsvn.vn", "vetau.com.vn"]
        },
        "bus": {
            "providers": ["Phương Trang (Futa)", "Hoàng Long", "Mai Linh", "Thành Bưởi"],
            "typical_price": "150.000 - 500.000 VND",
            "booking_sites": ["futabus.vn", "vexere.com"]
        }
    },
    "local": {
        "grab": {"typical_price": "15.000 - 50.000 VND/km"},
        "taxi": {"typical_price": "15.000 - 20.000 VND/km"},
        "motorbike_rental": {"typical_price": "100.000 - 200.000 VND/ngày"},
        "xe_om": {"typical_price": "10.000 - 30.000 VND/km"}
    }
}


class TransportAgent(BaseAgent):
    """Agent for transportation recommendations."""

    def __init__(self):
        super().__init__(
            name="transport",
            description="Tư vấn phương tiện di chuyển: máy bay, xe khách, tàu, taxi, Grab"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt with context."""
        context_info = ""
        if context.trip_data:
            context_info = f"""
Thông tin chuyến đi:
- Điểm đến: {context.trip_data.get('destination', 'Chưa xác định')}
- Ngày đi: {context.trip_data.get('start_date', 'Chưa xác định')}
- Ngày về: {context.trip_data.get('end_date', 'Chưa xác định')}
- Số người: {context.trip_data.get('travelers_count', 1)}
"""
        return get_transport_system_prompt(context_info)

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process transportation request."""
        start_time = datetime.utcnow()

        try:
            entities = self.extract_entities(context.message)
            intent = self._determine_transport_intent(context.message)

            if intent == "inter_city":
                response = await self._handle_inter_city(context, entities)
            elif intent == "local":
                response = await self._handle_local_transport(context, entities)
            else:
                response = await self._handle_general_query(context, entities)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                "transport_agent_processed",
                user_id=context.user_id,
                intent=intent,
                duration_ms=duration
            )

            return response

        except Exception as e:
            self.logger.error("transport_agent_error", error=str(e))
            return AgentResponse(
                message="Xin lỗi, tôi gặp sự cố khi tìm kiếm phương tiện. Bạn có thể thử lại?",
                agent_type=self.name,
                suggestions=["Tìm chuyến bay", "Xe khách liên tỉnh", "Di chuyển nội thành"]
            )

    def _determine_transport_intent(self, message: str) -> str:
        """Determine transport intent."""
        message_lower = message.lower()

        inter_city_keywords = ["máy bay", "chuyến bay", "flight", "tàu", "xe khách",
                               "từ", "đến", "liên tỉnh", "bus"]
        local_keywords = ["grab", "taxi", "xe máy", "thuê xe", "nội thành", "di chuyển"]

        for kw in inter_city_keywords:
            if kw in message_lower:
                return "inter_city"

        for kw in local_keywords:
            if kw in message_lower:
                return "local"

        return "general"

    async def _handle_inter_city(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Handle inter-city transport queries."""
        # Build transport info
        transport_info = self._format_transport_options("inter_city")

        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\nThông tin phương tiện:\n{transport_info}"
        ))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"transport_options": TRANSPORT_OPTIONS["inter_city"]},
            suggestions=["So sánh giá vé", "Đặt vé máy bay", "Tìm xe khách"]
        )

    async def _handle_local_transport(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Handle local transport queries."""
        transport_info = self._format_transport_options("local")

        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\nPhương tiện nội thành:\n{transport_info}"
        ))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"local_transport": TRANSPORT_OPTIONS["local"]},
            suggestions=["Thuê xe máy", "Giá Grab", "Taxi sân bay"]
        )

    async def _handle_general_query(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Handle general transport queries."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=["Di chuyển liên tỉnh", "Phương tiện nội thành", "Thuê xe"]
        )

    def _format_transport_options(self, category: str) -> str:
        """Format transport options for AI."""
        options = TRANSPORT_OPTIONS.get(category, {})
        lines = []

        for transport_type, info in options.items():
            if isinstance(info, dict):
                name = transport_type.replace("_", " ").title()
                price = info.get("typical_price", "N/A")
                lines.append(f"- {name}: {price}")

        return "\n".join(lines)
