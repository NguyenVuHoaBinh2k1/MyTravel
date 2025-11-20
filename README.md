# MyTravel - AI-Powered Vietnam Travel Planning App

An intelligent travel planning assistant that helps users plan their perfect Vietnam trip using AI-powered recommendations for accommodations, restaurants, transportation, and activities.

## Features

- **AI Chat Interface**: Natural conversation-based trip planning
- **Smart Recommendations**: Personalized suggestions for hotels, restaurants, and attractions
- **Multi-Agent System**: Specialized AI agents for different aspects of travel planning
- **Budget Tracking**: Monitor expenses and stay within budget
- **Itinerary Generation**: Automatic day-by-day schedule optimization
- **Real-time Updates**: WebSocket-based streaming responses

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Cache**: Redis
- **AI Providers**: Google Gemini, OpenAI
- **Agent Orchestration**: LangGraph
- **Migrations**: Alembic

### Frontend
- **Framework**: Next.js 15 with App Router
- **Styling**: TailwindCSS, shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Maps**: Leaflet

## Project Structure

```
MyTravel/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core configurations
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── agents/        # AI agents
│   │   ├── ai_providers/  # AI provider abstraction
│   │   └── integrations/  # External API integrations
│   ├── alembic/           # Database migrations
│   ├── tests/             # Test suite
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # React components
│   ├── lib/               # Utility functions
│   ├── stores/            # Zustand stores
│   ├── types/             # TypeScript types
│   └── hooks/             # Custom React hooks
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/MyTravel.git
   cd MyTravel
   ```

2. **Start infrastructure with Docker**
   ```bash
   docker-compose up -d db redis
   ```

3. **Set up Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Copy environment variables
   cp .env.example .env
   # Edit .env with your API keys

   # Run migrations
   alembic upgrade head

   # Start backend
   uvicorn app.main:app --reload
   ```

4. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Using Docker Compose (Full Stack)

```bash
docker-compose up --build
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mytravel
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## AI Agents

The app uses a multi-agent architecture:

1. **Master Orchestrator**: Routes conversations to appropriate agents
2. **Accommodation Agent**: Hotel and lodging recommendations
3. **Food & Dining Agent**: Restaurant and local cuisine suggestions
4. **Transportation Agent**: Flights, buses, trains, and local transport
5. **Itinerary Agent**: Day-by-day schedule optimization
6. **Budget Agent**: Cost tracking and optimization

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Backend
```bash
cd backend
pytest tests -v --cov=app
```

### Frontend
```bash
cd frontend
npm run lint
npm run type-check
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
