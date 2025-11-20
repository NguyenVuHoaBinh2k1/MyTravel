"""
Food & Dining Agent for restaurant and cuisine recommendations.
"""

from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.agents.prompts.base_prompts import get_food_system_prompt
from app.ai_providers import AIMessage
from app.integrations.google_maps import search_restaurants, PlaceResult
from app.core.logging import get_logger

logger = get_logger(__name__)


# Vietnamese cuisine knowledge base
VIETNAMESE_CUISINE = {
    "north": {
        "name": "Miền Bắc",
        "specialties": [
            {"name": "Phở Hà Nội", "description": "Phở bò truyền thống với nước dùng trong, thơm"},
            {"name": "Bún chả", "description": "Bún với chả nướng và nước mắm pha"},
            {"name": "Bánh cuốn", "description": "Bánh cuốn nóng với nhân thịt, mộc nhĩ"},
            {"name": "Chả cá Lã Vọng", "description": "Cá lăng chiên với nghệ và thì là"},
            {"name": "Bún bò Nam Bộ", "description": "Bún trộn với bò xào, đậu phộng"},
            {"name": "Bánh tôm Hồ Tây", "description": "Bánh chiên giòn với tôm nguyên con"},
        ],
        "street_food": ["Bánh mì", "Xôi", "Bánh rán", "Kem Tràng Tiền"]
    },
    "central": {
        "name": "Miền Trung",
        "specialties": [
            {"name": "Bún bò Huế", "description": "Bún với bò và giò heo, nước dùng cay"},
            {"name": "Cơm hến", "description": "Cơm nguội trộn hến, rau sống, mắm ruốc"},
            {"name": "Bánh bèo", "description": "Bánh bột gạo với tôm khô, mỡ hành"},
            {"name": "Mì Quảng", "description": "Mì với nước dùng sệt, tôm, thịt, đậu phộng"},
            {"name": "Cao lầu Hội An", "description": "Mì đặc biệt chỉ có ở Hội An"},
            {"name": "Bánh mì Đà Nẵng", "description": "Bánh mì với các loại nhân đặc trưng"},
        ],
        "street_food": ["Bánh tráng cuốn thịt heo", "Bê thui", "Chè Huế"]
    },
    "south": {
        "name": "Miền Nam",
        "specialties": [
            {"name": "Hủ tiếu Nam Vang", "description": "Hủ tiếu với nước dùng trong, thịt băm"},
            {"name": "Cơm tấm", "description": "Cơm gạo tấm với sườn nướng, bì, chả"},
            {"name": "Bánh mì Sài Gòn", "description": "Bánh mì giòn với nhiều loại nhân"},
            {"name": "Bún mắm", "description": "Bún với nước mắm cá linh, heo quay"},
            {"name": "Lẩu mắm", "description": "Lẩu với nước mắm, rau đồng, cá"},
            {"name": "Bánh canh cua", "description": "Bánh canh với cua, chả cá"},
        ],
        "street_food": ["Gỏi cuốn", "Bánh tráng trộn", "Chè miền Tây", "Trái cây"]
    }
}


class FoodAgent(BaseAgent):
    """Agent for restaurant and food recommendations."""

    def __init__(self):
        super().__init__(
            name="food",
            description="Tư vấn nhà hàng, quán ăn và món ăn đặc sản Việt Nam"
        )

    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt with context information."""
        context_info = ""

        if context.trip_data:
            destination = context.trip_data.get('destination', '')
            region = self._get_region(destination)

            context_info = f"""
Thông tin chuyến đi:
- Địa điểm: {destination}
- Vùng miền: {region}
- Số người: {context.trip_data.get('travelers_count', 1)}
"""
            # Add regional specialties
            if region:
                region_data = VIETNAMESE_CUISINE.get(region, {})
                if region_data:
                    specialties = region_data.get('specialties', [])
                    specialty_names = [s['name'] for s in specialties[:5]]
                    context_info += f"- Món đặc sản: {', '.join(specialty_names)}\n"

        return get_food_system_prompt(context_info)

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process food recommendation request."""
        start_time = datetime.utcnow()

        try:
            # Extract entities from user message
            entities = self.extract_entities(context.message)

            # Determine what the user wants
            intent = self._determine_intent(context.message)

            if intent == "search_restaurant":
                # Search for restaurants
                restaurants = await self._search_restaurants(context, entities)
                response = await self._generate_restaurant_response(
                    context, restaurants, entities
                )
            elif intent == "recommend_dish":
                # Recommend dishes
                response = await self._generate_dish_recommendation(context, entities)
            else:
                # General food query
                response = await self._generate_general_response(context, entities)

            # Log interaction
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                "food_agent_processed",
                user_id=context.user_id,
                trip_id=context.trip_id,
                intent=intent,
                duration_ms=duration
            )

            return response

        except Exception as e:
            self.logger.error(
                "food_agent_error",
                error=str(e),
                user_id=context.user_id
            )
            return AgentResponse(
                message="Xin lỗi, tôi gặp sự cố khi tìm kiếm nhà hàng. Bạn có thể thử lại được không?",
                agent_type=self.name,
                suggestions=["Thử tìm kiếm lại", "Hỏi về món ăn đặc sản"]
            )

    def _determine_intent(self, message: str) -> str:
        """Determine user intent from message."""
        message_lower = message.lower()

        # Restaurant search keywords
        restaurant_keywords = [
            "nhà hàng", "quán ăn", "quán", "ăn ở đâu", "chỗ ăn",
            "đi ăn", "restaurant", "đặt bàn"
        ]

        # Dish recommendation keywords
        dish_keywords = [
            "món gì", "ăn gì", "đặc sản", "nên thử", "món ngon",
            "phải ăn", "must try", "specialty"
        ]

        for keyword in restaurant_keywords:
            if keyword in message_lower:
                return "search_restaurant"

        for keyword in dish_keywords:
            if keyword in message_lower:
                return "recommend_dish"

        return "general"

    def _get_region(self, destination: str) -> Optional[str]:
        """Determine region from destination."""
        destination_lower = destination.lower()

        north_cities = ["hà nội", "hanoi", "hạ long", "sapa", "ninh bình"]
        central_cities = ["huế", "hue", "đà nẵng", "da nang", "hội an", "hoi an", "nha trang"]
        south_cities = ["hồ chí minh", "sài gòn", "saigon", "cần thơ", "phú quốc", "đà lạt"]

        for city in north_cities:
            if city in destination_lower:
                return "north"

        for city in central_cities:
            if city in destination_lower:
                return "central"

        for city in south_cities:
            if city in destination_lower:
                return "south"

        return None

    async def _search_restaurants(
        self,
        context: AgentContext,
        entities: dict
    ) -> list[PlaceResult]:
        """Search for restaurants."""
        location = (
            entities.get("locations", [""])[0] or
            context.trip_data.get("destination", "") if context.trip_data else ""
        )

        if not location:
            return []

        # Determine cuisine type from message
        cuisine_type = self._extract_cuisine_type(context.message)

        restaurants = await search_restaurants(
            location=location,
            cuisine_type=cuisine_type,
            limit=5
        )

        return restaurants

    def _extract_cuisine_type(self, message: str) -> Optional[str]:
        """Extract cuisine type from message."""
        message_lower = message.lower()

        cuisine_keywords = {
            "phở": "phở",
            "bún": "bún",
            "cơm": "cơm",
            "hải sản": "hải sản",
            "chay": "chay",
            "nướng": "nướng",
            "lẩu": "lẩu",
        }

        for keyword, cuisine in cuisine_keywords.items():
            if keyword in message_lower:
                return cuisine

        return None

    async def _generate_restaurant_response(
        self,
        context: AgentContext,
        restaurants: list[PlaceResult],
        entities: dict
    ) -> AgentResponse:
        """Generate response with restaurant recommendations."""
        if not restaurants:
            return await self._generate_general_response(context, entities)

        # Format restaurants for AI
        restaurants_info = self._format_restaurants_for_ai(restaurants)

        # Create messages for AI
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}\n\nKết quả tìm kiếm:\n{restaurants_info}"
        ))

        # Get AI response
        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        # Convert restaurants to dict
        restaurants_data = [
            {
                "name": r.name,
                "cuisine_type": "Vietnamese",
                "address": r.address,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "price_range": self._format_price_level(r.price_level),
                "rating": r.rating,
                "review_count": r.review_count,
                "opening_hours": r.opening_hours,
                "phone": r.phone,
            }
            for r in restaurants
        ]

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            data={"restaurants": restaurants_data},
            suggestions=[
                "Xem thêm nhà hàng",
                "Tìm món đặc sản",
                "Quán ăn đường phố"
            ]
        )

    async def _generate_dish_recommendation(
        self,
        context: AgentContext,
        entities: dict
    ) -> AgentResponse:
        """Generate dish recommendations based on location."""
        destination = (
            entities.get("locations", [""])[0] or
            context.trip_data.get("destination", "") if context.trip_data else ""
        )

        region = self._get_region(destination)

        # Build context with regional dishes
        dishes_info = ""
        if region and region in VIETNAMESE_CUISINE:
            region_data = VIETNAMESE_CUISINE[region]
            dishes_info = f"\n\nMón đặc sản {region_data['name']}:\n"
            for dish in region_data['specialties']:
                dishes_info += f"- {dish['name']}: {dish['description']}\n"
            dishes_info += f"\nĂn vặt: {', '.join(region_data['street_food'])}"

        # Create messages for AI
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(
            role="user",
            content=f"{context.message}{dishes_info}"
        ))

        # Get AI response
        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=[
                "Tìm nhà hàng phục vụ món này",
                "Món ăn khác",
                "Quán ăn đường phố"
            ]
        )

    async def _generate_general_response(
        self,
        context: AgentContext,
        entities: dict
    ) -> AgentResponse:
        """Generate general food-related response."""
        messages = self.format_conversation_history(context.conversation_history)
        messages.append(AIMessage(role="user", content=context.message))

        system_prompt = self.get_system_prompt(context)
        ai_response = await self.call_ai(messages, system_prompt)

        return AgentResponse(
            message=ai_response.content,
            agent_type=self.name,
            suggestions=[
                "Tìm nhà hàng gần đây",
                "Gợi ý món đặc sản",
                "Quán ăn bình dân"
            ]
        )

    def _format_restaurants_for_ai(self, restaurants: list[PlaceResult]) -> str:
        """Format restaurant results for AI context."""
        lines = []
        for i, r in enumerate(restaurants, 1):
            lines.append(
                f"{i}. {r.name}\n"
                f"   - Địa chỉ: {r.address}\n"
                f"   - Đánh giá: {r.rating}/5 ({r.review_count} reviews)\n"
                f"   - Mức giá: {self._format_price_level(r.price_level)}\n"
                f"   - Giờ mở cửa: {r.opening_hours or 'N/A'}\n"
            )
        return "\n".join(lines)

    def _format_price_level(self, level: Optional[int]) -> str:
        """Format price level to string."""
        if level is None:
            return "N/A"
        return "$" * (level + 1)
