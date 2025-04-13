# Vizier

### From Noise to Signal: Because 'Insight' Isn't Just Another Token

## 🚀 Inspiration

Every serious researcher — from grad students grinding out their lit reviews to tenured professors trying to track five subfields at once — knows the pain:

- New research moves **too fast**
- It's **scattered across a dozen platforms**
- And if you blink, you've missed a whole trend

Between arXiv, Twitter threads, conference keynotes, and shadow releases on GitHub, **there's no single feed that captures the full signal**.

We weren't inspired by another one-shot summarizer. We were inspired by how actual researchers work:
- Constant pivots between sources
- Zooming in and out across timescales
- Evaluating claims, not just regurgitating them
- Prioritizing trust, depth, and novelty

So we built Vizier — not another autocomplete wrapper, but a system that actually understands your goals and assembles a live research team around them.

Because in 2025, **Insight isn't just another token.** 

## 🧠 What Vizier Actually Does

Vizier is a **modular, agentic research engine** — your personal research ops team, not just a chatbot. Whether you're building a newsletter, writing a paper, pitching an idea, or just staying on the bleeding edge, Vizier gives you:

- 🔍 Precision-curated content from **credible, multi-platform sources**
- 🧱 Structured, editable reports tailored to your research priorities
- 🧠 Control over what gets emphasized, where deeper sourcing is needed, and how frequent updates should be

### Built for:

- 🧑‍🔬 **Researchers and technical professionals** who need rigorous updates on specialized domains
- 🎓 **Students and professors** tracking rapid fields like GenAI, climate science, or synthetic bio
- 📣 **Content creators and analysts** writing newsletters, reports, or breakdowns on bleeding-edge developments

Once you've locked in a great output, you can:
- 📅 **Schedule that research plan to auto-run** daily, weekly, or monthly
- 🔁 Revisit past reports, tweak scopes, swap source weights, or layer in new domains

## 🔁 What Makes Vizier *Agentic*?

This isn't just "use LangChain and call it a day." Vizier's agents **think for themselves**.

### 🧭 Router v0_4
Analyzes your refined query and decides:
- How many agents to spawn
- Which domains get which budget
- Which model contexts are needed

### 🔎 Web and Twitter Search Agents
Don't just follow rules — they *evaluate*:
- How noisy a domain is
- Whether depth is sufficient
- If second-level validation is required

### 🧪 Source Review Agents
Actively rerank or prune content if trust scores fall short, pushing quality higher through intelligent evaluation.

## 🛠 Technical Architecture

### Core Components

1. 🧠 **Query Refiner**  
   - Builds multi-component research plans
   - Considers user role and goals
   - Sets update frequency parameters

2. 🧭 **Router v0_4**  
   - Maps query scope to modality
   - Assigns sourcing budgets
   - Manages independent agents

3. ✍️ **Writer Agent**  
   - Synthesizes modular content
   - Auto-queries for clarification
   - Enables source re-ranking

4. ⚡ **Live Agent Graph UI**  
   - SSE-driven real-time updates
   - Visual decision tracing
   - Interactive feedback system

## 🛠 Backend Architecture

### Core Components

1. **Query Processor Pipeline**
   - Query Refinement (Claude 3 Sonnet)
   - Web Search Agent
   - Twitter Search Agent
   - Source Review & Reranking
   - Router_04 for Agent Orchestration
   - Draft Generation

2. **State Management**
   - Real-time SSE progress streaming
   - Session persistence
   - Source caching and reranking

3. **Database Schema**
   - Queries table with JSONB for source storage
   - Drafts with versioning
   - User profiles and preferences

### API Design

1. **Query Flow**
   ```
   POST /queries          # Create new query
   GET  /queries/{id}     # Get query status
   POST /queries/{id}/refine  # Start refinement
   GET  /queries/stream/{id}  # SSE progress updates
   ```

2. **Source Review**
   ```
   GET  /queries/{id}/sources      # Get sources for review
   POST /queries/{id}/sources/review  # Submit reviewed sources
   ```

3. **Draft Management**
   ```
   POST /drafts/generate  # Generate from sources
   GET  /drafts/{id}      # Get draft content
   POST /drafts/{id}/accept  # Accept draft
   POST /drafts/{id}/reject  # Reject with feedback
   GET  /drafts/stream/{id}  # Stream generation
   ```

### Data Flow

1. **Query Processing**
   ```mermaid
   graph TD
   A[Raw Query] --> B[Query Refinement]
   B --> C[Web Search]
   B --> D[Twitter Search]
   C --> E[Source Review]
   D --> E
   E --> F[Router_04]
   F --> G[Draft Generation]
   ```

2. **Source Processing**
   ```mermaid
   graph TD
   A[Raw Sources] --> B[Trust Scoring]
   B --> C[User Review]
   C --> D[Final Reranking]
   D --> E[Router_04]
   ```

### Real-time Updates

The backend uses Server-Sent Events (SSE) to provide real-time updates on:
- Query refinement progress
- Source collection status
- Source review readiness
- Draft generation progress

Events are emitted in the format:
```json
{
  "stage": "ProcessStage",
  "timestamp": "datetime",
  "data": { stage-specific data }
}
```

### Technologies Used

- **FastAPI** - Asynchronous API framework
- **PostgreSQL** - JSONB storage for flexible document handling
- **SSE** - Real-time event streaming
- **OpenRouter** - Model provider abstraction and fallback
- **Claude 3 Sonnet** - Primary LLM for refinement and generation
- **JWT** - Authentication and session management

## 💻 Development Setup

### Prerequisites

#### Frontend
- Node.js (v18+)
- npm (v9+) or yarn
- Visual Studio Code (recommended)

#### Backend
- Python 3.10+
- PostgreSQL
- Google OAuth credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/vizier.git
cd vizier
```

2. Backend Setup:
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. Configure Backend Environment:
Create a `.env` file:
```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:3000
JWT_SECRET=
DATABASE_URL=
sslmode=require
```

4. Frontend Setup:
```bash
cd frontend
npm install
```

### Running the Application

#### Development Mode

Backend:
```bash
uvicorn main:app --reload
```

Frontend:
```bash
npm run dev
# or
yarn dev
```

Access the application at `http://localhost:5173`

## Backend Development Setup

1. Set up PostgreSQL:
   ```bash
   createdb vizier
   ```

2. Configure environment:
   ```bash
   cp example.env .env
   # Edit .env with your credentials:
   # - DATABASE_URL
   # - JWT_SECRET
   # - OPENROUTER_API_KEY
   ```

3. Initialize database:
   ```bash
   python -m alembic upgrade head
   ```

4. Run development server:
   ```bash
   uvicorn main:app --reload
   ```

## 📂 Project Structure

```
vizier/
├── frontend/
│   ├── public/                        # Static files
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/                 # Application pages
│   │   │   │   ├── discover/          # Discover page
│   │   │   │   ├── graph/             # Graph visualization
│   │   │   │   ├── library/           # Library page
│   │   │   │   ├── login/             # Login and authentication
│   │   │   │   ├── onboarding/        # User onboarding
│   │   │   │   ├── query/             # Query interface
│   │   │   │   ├── settings/          # Settings page
│   │   │   │   └── spaces/            # Spaces page
│   │   │   ├── App.tsx                # Main application component
│   │   │   ├── App.css                # Main application styles
│   │   │   ├── index.css              # Global styles
│   │   │   └── main.tsx               # Application entry point
│   │   ├── components/                # Reusable components
│   │   │   ├── navigation/            # Navigation components
│   │   │   └── querybar/              # Query bar components
│   │   └── vite-env.d.ts              # Vite environment typings
│   ├── index.html                     # HTML entry point
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── tsconfig.app.json              # App-specific TypeScript config
│   ├── tsconfig.node.json             # Node-specific TypeScript config
│   ├── vite.config.ts                 # Vite configuration
│   ├── package.json                   # Project dependencies and scripts
│   └── README.md                      # Project documentation

├── backend/
│   ├── .gitignore
│   ├── database.py
│   ├── dummyapi.py
│   ├── main.py
│   ├── README.md
│   ├── requirements.txt
│   ├── test.py
│   ├── processes/
│   │   ├── main.py
│   │   ├── connectors/
│   │   │   ├── router_0.py
│   │   │   └── router_04.py
│   │   ├── query/
│   │   │   └── refiner.py
│   │   ├── report/
│   │   │   ├── refiner.py
│   │   │   └── writer.py
│   │   ├── search/
│   │   │   ├── agents.py
│   │   │   ├── twitter.py
│   │   │   └── web.py
│   │   ├── sourcing/
│   │   │   ├── agent.py
│   │   │   └── director.py
│   │   └── writer/
│   │       └── generator.py
│   └── routers/
│       ├── auth.py
│       ├── drafts.py
│       ├── openrouter.py
│       ├── queries.py
│       └── user.py
```

## 🔌 API Integration

Refer to our [API Documentation](docs/API.md) for detailed endpoint specifications and integration guides.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.