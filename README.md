# NL2SQL Chatbot Application

A full-stack natural language to SQL application with Streamlit frontend and FastAPI backend.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit Frontend                      │
│              (app/frontend.py :8501)                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend                             │
│   (app/__init__.py + app/routes.py :8000)               │
│                                                          │
│  POST /api/nl2sql          → Process NL question        │
│  POST /api/session/create  → Create chat session        │
│  GET /api/session/{id}     → Get session details        │
│  GET /api/health          → Health check               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            LangChain Agent Engine                        │
│   (main.py - build_agent + tools)                       │
│                                                          │
│  ├─ schema_linker   → Identify relevant tables          │
│  ├─ sql_synthesis   → Generate SQL                      │
│  ├─ sql_validator   → Validate SQL                      │
│  ├─ sql_executor    → Execute SQL                       │
│  ├─ debug_agent     → Fix SQL errors                    │
│  └─ answering_agent → Generate natural language answer  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            SQLite Database                               │
│        (data/adventureworks.sqlite3)                     │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- Virtual environment activated (included in `lang/`)
- Azure OpenAI credentials in `.env`

### 1. Activate Virtual Environment

```bash
# Windows PowerShell
& ".\lang\Scripts\Activate.ps1"

# macOS/Linux
source lang/bin/activate
```

### 2. Set Environment Variables

Create a `.env` file in the project root:

```env
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name


# Database (optional, defaults to bundled SQLite)
DATABASE_URL=sqlite:///data/adventureworks.sqlite3

# Backend configuration
BACKEND_URL=http://127.0.0.1:8000/api
```

### 3. Terminal 1 - Start FastAPI Backend

```bash
python run_api.py
```

The backend will start at `http://127.0.0.1:8000`

- API Docs: http://127.0.0.1:8000/api/docs
- ReDoc: http://127.0.0.1:8000/api/redoc

### 4. Terminal 2 - Start Streamlit Frontend

```bash
python run_frontend.py
```

Or manually:

```bash
streamlit run app/frontend.py
```

The frontend will open at `http://localhost:8501`

## Project Structure

```
langchain_project/
├── main.py                      # Agent builder & CLI
├── run_api.py                   # FastAPI startup
├── run_frontend.py              # Streamlit startup
├── requirements.txt             # Python dependencies
│
├── app/
│   ├── __init__.py              # FastAPI app creation
│   ├── frontend.py              # Streamlit UI
│   ├── routes.py                # API endpoints
│   └── schemas.py               # Pydantic models
│
├── tools/
│   ├── state.py                 # Global state (debug counter)
│   ├── debug.py                 # SQL debugging tool
│   ├── general_answers.py       # General QA tool
│   ├── schema_linker.py         # Table/column identification
│   ├── sql_synthesis.py         # SQL generation
│   ├── sql_executor.py          # SQL execution
│   ├── sql_validator.py         # SQL validation
│   └── answer.py                # NL answer generation
│
├── config/
│   ├── azure_client.py          # Azure OpenAI setup
│   └── settings.py              # Configuration
│
├── metadata/
│   ├── metadata_loader.py       # Load table metadata
│   └── metadata.csv             # Table descriptions
│
├── data/
│   └── adventureworks.sqlite3   # Sample database
│
└── lang/                         # Python virtual environment
```

## Key Features

### Frontend (Streamlit)
- **Multi-session chat**: Manage multiple conversations simultaneously
- **Dark mode**: Default theme with light mode toggle
- **SQL Viewer**: See generated and executed SQL
- **Results Display**: Table view and auto-generated charts
- **Suggestions**: Smart suggestions for common queries
- **Token tracking**: Monitor API usage

### Backend (FastAPI)
- **Session Management**: Independent chat sessions
- **Stateful Conversations**: Maintain context across turns
- **SQL-First Response**: Return SQL, results, and execution flow
- **Error Handling**: Graceful error messages and debugging
- **CORS Support**: Works seamlessly with Streamlit

### Agent (LangChain)
- **Multi-tool Pipeline**: Structured NL→SQL workflow
- **Self-Healing**: Debug agent fixes SQL errors automatically
- **Context Awareness**: Remembers conversation history
- **Metadata-Driven**: Uses table/column metadata for grounding

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Create Session
```bash
POST /api/session/create
{
  "name": "My Chat",
  "session_id": "optional-uuid"
}
```

### Process NL2SQL Question
```bash
POST /api/nl2sql
{
  "question": "What is the color of product CN-6137?",
  "session_id": "session-uuid"
}

Response:
{
  "answer": "The color of product CN-6137 is Black.",
  "sql": "SELECT Color FROM Product WHERE ProductNumber = 'CN-6137' LIMIT 100",
  "validated_sql": "SELECT Color FROM Product WHERE ProductNumber = 'CN-6137' LIMIT 100",
  "rows": [{"Color": "Black"}],
  "row_count": 1,
  "execution_error": "",
  "flow": ["[USER] What is the color...", "[sql_synthesis]", "[sql_executor]", "[answering_agent]"],
  "session_id": "session-uuid"
}
```

### Get Session Details
```bash
GET /api/session/{session_id}
```

### List All Sessions
```bash
GET /api/sessions
```

## Configuration

### Environment Variables

```env
# Required
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT_NAME=...

# Optional
DATABASE_URL=sqlite:///data/adventureworks.sqlite3
BACKEND_URL=http://127.0.0.1:8000/api
```

### Database Setup

The application ships with a bundled SQLite database (`data/adventureworks.sqlite3`).

To use a different database:
- Set `DATABASE_URL` in `.env`
- Supported: SQLite, PostgreSQL, MySQL, SQL Server

## Workflow

### User Question Flow

1. **Frontend**: User enters question → Streamlit captures input
2. **API Call**: Frontend POSTs to `/api/nl2sql` with session ID
3. **Session Lookup**: Backend retrieves conversation history
4. **Agent Invocation**: Build fresh agent with history context
5. **Tool Pipeline**:
   - `schema_linker`: Identify relevant tables/columns
   - `sql_synthesis`: Generate SQL query
   - `sql_validator`: Validate syntax
   - `sql_executor`: Run SQL, get results
   - `debug_agent`: Fix SQL if errors occur (up to 3 attempts)
   - `answering_agent`: Convert results to natural language
6. **Response**: Return SQL + results + answer
7. **Frontend Update**: Display answer, SQL, charts

## Troubleshooting

### Backend Connection Error
- Ensure FastAPI is running: `python run_api.py`
- Check BACKEND_URL in frontend environment
- Look at backend logs for details

### SQL Execution Errors
- Check `execution_error` in API response
- Review generated SQL in frontend "SQL" tab
- Debug agent will attempt 3 automatic fixes

### Session Not Found
- Frontend creates sessions automatically
- Sessions are stored in-memory (resets on backend restart)
- For persistence, replace `SESSIONS` dict with database

### Azure OpenAI Errors
- Verify `.env` credentials
- Check deployment name matches
- Test: `curl -X GET http://localhost:8000/api/health`

## Development

### Run Tests
```bash
pytest tests/
```

### Format Code
```bash
black app/ tools/ config/
```

### Type Checking
```bash
mypy app/ tools/
```

## Production Deployment

### Docker Setup
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "run_api.py"]
```

### Session Persistence
Replace in-memory `SESSIONS` dict with:
- Redis
- PostgreSQL
- DynamoDB

### Scaling
- Run multiple FastAPI instances behind nginx
- Use load balancer for session affinity
- Share state via Redis or database

## Support

For issues or questions:
1. Check logs: `streamlit run app/frontend.py --logger.level=debug`
2. Review API docs: http://localhost:8000/api/docs
3. Test SQL directly against database
4. Check Azure OpenAI quotas and rate limits
