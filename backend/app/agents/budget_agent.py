"""
Budget Agent for cost tracking and budget optimization.
"""

from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.prompts.base_prompts import get_budget_system_prompt
from app.ai_providers import AIMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


# Vietnamese travel cost reference
COST_REFERENCE = {
    "accommodation": {
        "hostel": {"min": 150000, "max": 300000, "unit": "đêm"},
        "hotel_3star": {"min": 500000, "max": 1000000, "unit": "đêm"},
        "hotel_4star": {"min": 1000000, "max": 2000000, "unit": "đêm"},
        "hotel_5star": {"min": 2000000, "max": 5000000, "unit": "đêm"},
        "resort": {"min": 3000000, "max": 10000000, "unit": "đêm"},
    },
    "food": {
        "street_food": {"min": 20000, "max": 50000, "unit": "bữa"},
        "local_restaurant": {"min": 50000, "max": 150000, "unit": "bữa"},
        "mid_range": {"min": 150000, "max": 400000, "unit": "bữa"},
        "fine_dining": {"min": 500000, "max": 2000000, "unit": "bữa"},
    },
    "transport": {
        "grab_short": {"min": 20000, "max": 50000, "unit": "chuyến"},
        "grab_long": {"min": 100000, "max": 300000, "unit": "chuyến"},
        "domestic_flight": {"min": 800000, "max": 3000000, "unit": "vé"},
        "bus_ticket": {"min": 150000, "max": 500000, "unit": "vé"},
    },
    "activities": {
        "museum": {"min": 30000, "max": 100000, "unit": "vé"},
        "attraction": {"min": 100000, "max": 500000, "unit": "vé"},
        "tour": {"min": 500000, "max": 2000000, "unit": "người"},
    }
}


class BudgetAgent(BaseAgent):
    """Agent for budget planning and expense tracking."""

    def __init__(self):
        super().__init__(
            name="budget",
            description="Tư vấn ngân sách và theo dõi chi tiêu du lịch"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt with context."""
        context_info = ""
        if context.trip_data:
            context_info = f"""
Thông tin chuyến đi:
- Điểm đến: {context.trip_data.get('destination', 'Chưa xác định')}
- Số ngày: {self._calculate_days(context.trip_data)}
- Số người: {context.trip_data.get('travelers_count', 1)}
- Ngân sách tổng: {context.trip_data.get('budget', 0):,.0f} VND
"""
        return get_budget_system_prompt(context_info)

    def _calculate_days(self, trip_data: dict) -> int:
        """Calculate trip duration."""
        try:
            from datetime import date
            start = trip_data.get('start_date', '')
            end = trip_data.get('end_date', '')
            if isinstance(start, str):
                start = date.fromisoformat(start)
            if isinstance(end, str):
                end = date.fromisoformat(end)
            return (end - start).days + 1
        except:
            return 1

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process budget request."""
        start_time = datetime.utcnow()

        try:
            entities = self.extract_entities(context.message)
            intent = self._determine_intent(context.message)

            if intent == "estimate":
                response = await self._estimate_budget(context, entities)
            elif intent == "optimize":
                response = await self._optimize_budget(context, entities)
            elif intent == "breakdown":
                response = await self._budget_breakdown(context, entities)
            else:
                response = await self._handle_general_query(context, entities)

            end_time = datetime.utcnow()
            self.logger.info(
                "budget_agent_processed",
                user_id=context.user_id,
                intent=intent,
                duration_ms=(end_time - start_time).total_seconds() * 1000
            )

            return response

        except Exception as e:
            self.logger.error("budget_agent_error", error=str(e))
            return AgentResponse(
                message="Xin lỗi, tôi gặp sự cố khi tính toán ngân sách. Bạn có thể thử lại?",
                agent_type=self.name,
                suggestions=["Ước tính chi phí", "Phân bổ ngân sách"]
            )

    def _determine_intent(self, message: str) -> str:
        """Determine budget intent."""
        message_lower = message.lower()

        estimate_keywords = ["ước tính", "bao nhiêu", "chi phí", "tốn", "cost", "estimate"]
        optimize_keywords = ["tiết kiệm", "giảm", "tối ưu", "rẻ hơn", "save", "optimize"]
        breakdown_keywords = ["phân bổ", "chia", "breakdown", "chi tiết", "hạng mục"]

        for kw in estimate_keywords:
            if kw in message_lower:
                return "estimate"

        for kw in optimize_keywords:
            if kw in message_lower:
                return "optimize"

        for kw in breakdown_keywords:
            if kw in message_lower:
                return "breakdown"

        return "general"

    async def _estimate_budget(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Estimate budget for the trip."""
        # Calculate estimated costs
        days = self._calculate_days(context.trip_data) if context.trip_data else 3
        travelers = context.trip_data.get('travelers_count', 1) if context.trip_data else 1

        estimates = self._calculate_estimates(days, travelers)
        estimates_info = self._format_estimates(estimates)

        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\nƯớc tính chi phí:\n{estimates_info}"
        ))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"budget_estimate": estimates},
            suggestions=["Chi tiết từng hạng mục", "Cách tiết kiệm", "Phân bổ ngân sách"]
        )

    async def _optimize_budget(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Provide budget optimization tips."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        system_prompt += """

Khi tư vấn tiết kiệm, gợi ý:
1. Đặt phòng sớm để có giá tốt
2. Ăn ở quán địa phương thay vì nhà hàng du lịch
3. Dùng xe bus/grab pool thay vì taxi riêng
4. Mua vé combo cho nhiều điểm tham quan
5. Tránh mùa cao điểm nếu có thể
"""

        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=["Áp dụng gợi ý", "Xem chi phí mới", "Tìm deal khách sạn"]
        )

    async def _budget_breakdown(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Provide detailed budget breakdown."""
        days = self._calculate_days(context.trip_data) if context.trip_data else 3
        travelers = context.trip_data.get('travelers_count', 1) if context.trip_data else 1
        total_budget = context.trip_data.get('budget', 5000000) if context.trip_data else 5000000

        # Calculate recommended allocation
        breakdown = {
            "accommodation": int(total_budget * 0.35),
            "food": int(total_budget * 0.25),
            "transport": int(total_budget * 0.20),
            "activities": int(total_budget * 0.15),
            "misc": int(total_budget * 0.05),
        }

        breakdown_info = f"""
Phân bổ ngân sách {total_budget:,.0f} VND:
- Chỗ ở: {breakdown['accommodation']:,.0f} VND (35%)
- Ăn uống: {breakdown['food']:,.0f} VND (25%)
- Di chuyển: {breakdown['transport']:,.0f} VND (20%)
- Tham quan: {breakdown['activities']:,.0f} VND (15%)
- Dự phòng: {breakdown['misc']:,.0f} VND (5%)
"""

        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\n{breakdown_info}"
        ))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"budget_breakdown": breakdown},
            suggestions=["Điều chỉnh tỷ lệ", "Xem chi tiết", "Ước tính thực tế"]
        )

    async def _handle_general_query(self, context: AgentContext, entities: dict) -> AgentResponse:
        """Handle general budget queries."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=["Ước tính chi phí", "Phân bổ ngân sách", "Mẹo tiết kiệm"]
        )

    def _calculate_estimates(self, days: int, travelers: int) -> dict:
        """Calculate budget estimates."""
        return {
            "accommodation": {
                "budget": {"total": days * 400000, "per_night": 400000},
                "mid_range": {"total": days * 1000000, "per_night": 1000000},
                "luxury": {"total": days * 3000000, "per_night": 3000000},
            },
            "food": {
                "budget": {"total": days * travelers * 200000, "per_day": 200000},
                "mid_range": {"total": days * travelers * 500000, "per_day": 500000},
                "luxury": {"total": days * travelers * 1000000, "per_day": 1000000},
            },
            "transport": {
                "local": {"total": days * 150000},
                "inter_city": {"estimated": 500000},
            },
            "activities": {
                "per_day": 300000,
                "total": days * 300000,
            }
        }

    def _format_estimates(self, estimates: dict) -> str:
        """Format estimates for display."""
        lines = []

        # Accommodation
        acc = estimates["accommodation"]["mid_range"]
        lines.append(f"Chỗ ở (trung bình): {acc['total']:,.0f} VND ({acc['per_night']:,.0f}/đêm)")

        # Food
        food = estimates["food"]["mid_range"]
        lines.append(f"Ăn uống: {food['total']:,.0f} VND ({food['per_day']:,.0f}/ngày/người)")

        # Transport
        lines.append(f"Di chuyển: {estimates['transport']['local']['total']:,.0f} VND")

        # Activities
        lines.append(f"Tham quan: {estimates['activities']['total']:,.0f} VND")

        return "\n".join(lines)
