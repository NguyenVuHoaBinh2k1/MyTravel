"""
Master Orchestrator for coordinating travel planning agents.

Uses LangGraph for agent workflow management and routing.
"""

from datetime import datetime
from typing import Any, Optional
from enum import Enum

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.agents.base import AgentContext, AgentResponse
from app.agents.accommodation_agent import AccommodationAgent
from app.agents.food_agent import FoodAgent
from app.agents.transport_agent import TransportAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.budget_agent import BudgetAgent
from app.ai_providers import get_ai_provider, AIMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Available agent types."""
    ACCOMMODATION = "accommodation"
    FOOD = "food"
    TRANSPORT = "transport"
    ITINERARY = "itinerary"
    BUDGET = "budget"
    GENERAL = "general"


class OrchestratorState(BaseModel):
    """State for the orchestrator workflow."""
    message: str
    user_id: str
    trip_id: Optional[str] = None
    trip_data: Optional[dict] = None
    conversation_history: list[dict] = Field(default_factory=list)
    selected_agent: Optional[str] = None
    response: Optional[dict] = None
    error: Optional[str] = None


class MasterOrchestrator:
    """
    Master Orchestrator that routes requests to specialized agents.

    Uses LangGraph for workflow management and intelligent routing.
    """

    def __init__(self):
        self.logger = logger

        # Initialize agents
        self.agents = {
            AgentType.ACCOMMODATION: AccommodationAgent(),
            AgentType.FOOD: FoodAgent(),
            AgentType.TRANSPORT: TransportAgent(),
            AgentType.ITINERARY: ItineraryAgent(),
            AgentType.BUDGET: BudgetAgent(),
        }

        # Intent classification keywords
        self.intent_keywords = {
            AgentType.ACCOMMODATION: [
                "khách sạn", "hotel", "phòng", "room", "lưu trú", "stay",
                "đặt phòng", "booking", "resort", "homestay", "hostel",
                "chỗ ở", "accommodation", "check-in", "check-out"
            ],
            AgentType.FOOD: [
                "ăn", "eat", "nhà hàng", "restaurant", "quán", "món",
                "đặc sản", "food", "cuisine", "bún", "phở", "bánh",
                "đói", "hungry", "ẩm thực", "menu", "drink", "café"
            ],
            AgentType.TRANSPORT: [
                "đi", "travel", "bay", "flight", "máy bay", "xe", "bus",
                "tàu", "train", "grab", "taxi", "di chuyển", "transport",
                "vé", "ticket", "sân bay", "airport", "thuê xe"
            ],
            AgentType.ITINERARY: [
                "lịch trình", "itinerary", "kế hoạch", "plan", "schedule",
                "ngày", "day", "tham quan", "visit", "điểm đến", "destination",
                "tour", "hoạt động", "activity", "sắp xếp"
            ],
            AgentType.BUDGET: [
                "ngân sách", "budget", "chi phí", "cost", "tiền", "money",
                "giá", "price", "rẻ", "cheap", "đắt", "expensive",
                "tiết kiệm", "save", "tốn", "spend", "ước tính", "estimate"
            ],
        }

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for agent orchestration."""

        # Create state graph
        workflow = StateGraph(OrchestratorState)

        # Add nodes
        workflow.add_node("classify", self._classify_intent)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("handle_general", self._handle_general)
        workflow.add_node("process_response", self._process_response)

        # Set entry point
        workflow.set_entry_point("classify")

        # Add edges
        workflow.add_conditional_edges(
            "classify",
            self._should_use_agent,
            {
                "agent": "route_to_agent",
                "general": "handle_general"
            }
        )

        workflow.add_edge("route_to_agent", "process_response")
        workflow.add_edge("handle_general", "process_response")
        workflow.add_edge("process_response", END)

        return workflow.compile()

    def _classify_intent(self, state: OrchestratorState) -> OrchestratorState:
        """Classify user intent and select appropriate agent."""
        message_lower = state.message.lower()

        # Score each agent type
        scores = {}
        for agent_type, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[agent_type] = score

        # Select agent with highest score
        if scores:
            selected = max(scores, key=scores.get)
            state.selected_agent = selected.value
        else:
            state.selected_agent = AgentType.GENERAL.value

        self.logger.info(
            "intent_classified",
            user_id=state.user_id,
            message_preview=state.message[:50],
            selected_agent=state.selected_agent,
            scores={k.value: v for k, v in scores.items()}
        )

        return state

    def _should_use_agent(self, state: OrchestratorState) -> str:
        """Determine if we should route to a specific agent or handle generally."""
        if state.selected_agent and state.selected_agent != AgentType.GENERAL.value:
            return "agent"
        return "general"

    async def _route_to_agent(self, state: OrchestratorState) -> OrchestratorState:
        """Route request to the selected agent."""
        try:
            agent_type = AgentType(state.selected_agent)
            agent = self.agents.get(agent_type)

            if not agent:
                state.error = f"Agent not found: {state.selected_agent}"
                return state

            # Create agent context
            context = AgentContext(
                user_id=state.user_id,
                trip_id=state.trip_id,
                message=state.message,
                conversation_history=[
                    AIMessage(**msg) for msg in state.conversation_history
                ],
                trip_data=state.trip_data
            )

            # Process with agent
            response = await agent.process(context)

            state.response = {
                "message": response.message,
                "agent_type": response.agent_type,
                "data": response.data,
                "suggestions": response.suggestions,
                "actions": response.actions
            }

        except Exception as e:
            self.logger.error(
                "agent_routing_error",
                error=str(e),
                agent=state.selected_agent
            )
            state.error = str(e)

        return state

    async def _handle_general(self, state: OrchestratorState) -> OrchestratorState:
        """Handle general queries that don't match specific agents."""
        try:
            provider = get_ai_provider()

            system_prompt = """Bạn là trợ lý du lịch Việt Nam thân thiện và hữu ích.

Bạn có thể giúp người dùng với:
- Tìm khách sạn và chỗ ở
- Gợi ý nhà hàng và món ăn
- Tư vấn phương tiện di chuyển
- Lập lịch trình du lịch
- Tính toán ngân sách

Hãy trả lời câu hỏi của người dùng và gợi ý họ hỏi thêm về các chủ đề trên nếu cần.
Sử dụng tiếng Việt tự nhiên và thân thiện."""

            messages = [
                AIMessage(**msg) for msg in state.conversation_history
            ]
            messages.append(AIMessage(role="user", content=state.message))

            response = await provider.chat(messages, system_prompt)

            state.response = {
                "message": response.content,
                "agent_type": "general",
                "suggestions": [
                    "Tìm khách sạn",
                    "Gợi ý món ăn",
                    "Lập lịch trình",
                    "Tính ngân sách"
                ]
            }

        except Exception as e:
            self.logger.error("general_handler_error", error=str(e))
            state.error = str(e)

        return state

    def _process_response(self, state: OrchestratorState) -> OrchestratorState:
        """Process and finalize the response."""
        if state.error and not state.response:
            state.response = {
                "message": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. Bạn có thể thử lại?",
                "agent_type": "error",
                "suggestions": [
                    "Thử lại",
                    "Hỏi câu khác"
                ]
            }

        return state

    async def process(
        self,
        message: str,
        user_id: str,
        trip_id: Optional[str] = None,
        trip_data: Optional[dict] = None,
        conversation_history: Optional[list[dict]] = None
    ) -> AgentResponse:
        """
        Process a user message through the orchestrator.

        Args:
            message: User's message
            user_id: User identifier
            trip_id: Optional trip identifier
            trip_data: Optional trip context data
            conversation_history: Previous conversation messages

        Returns:
            AgentResponse with the result
        """
        start_time = datetime.utcnow()

        # Create initial state
        initial_state = OrchestratorState(
            message=message,
            user_id=user_id,
            trip_id=trip_id,
            trip_data=trip_data,
            conversation_history=conversation_history or []
        )

        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)

            # Extract response
            response_data = final_state.get("response", {})

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                "orchestrator_processed",
                user_id=user_id,
                trip_id=trip_id,
                selected_agent=final_state.get("selected_agent"),
                duration_ms=duration
            )

            return AgentResponse(
                message=response_data.get("message", ""),
                agent_type=response_data.get("agent_type", "unknown"),
                data=response_data.get("data"),
                suggestions=response_data.get("suggestions", []),
                actions=response_data.get("actions", [])
            )

        except Exception as e:
            self.logger.error(
                "orchestrator_error",
                error=str(e),
                user_id=user_id
            )

            return AgentResponse(
                message="Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.",
                agent_type="error",
                suggestions=["Thử lại"]
            )

    async def process_with_context(
        self,
        context: AgentContext
    ) -> AgentResponse:
        """
        Process a request using an AgentContext directly.

        Args:
            context: AgentContext with all necessary information

        Returns:
            AgentResponse with the result
        """
        return await self.process(
            message=context.message,
            user_id=context.user_id,
            trip_id=context.trip_id,
            trip_data=context.trip_data,
            conversation_history=[
                {"role": msg.role, "content": msg.content}
                for msg in context.conversation_history
            ]
        )


# Singleton instance
_orchestrator: Optional[MasterOrchestrator] = None


def get_orchestrator() -> MasterOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MasterOrchestrator()
    return _orchestrator
