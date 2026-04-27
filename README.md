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

## Installation & Setup

### Prerequisites

- **Python 3.9+**
- **Virtual environment** (included in `lang/` directory)
- **Azure OpenAI credentials** (API key, endpoint, deployment name)

### Step 1: Activate Virtual Environment

**Windows PowerShell:**
```powershell
& ".\lang\Scripts\Activate.ps1"
```

**macOS/Linux:**
```bash
source lang/bin/activate
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root directory:

```env
# Azure OpenAI Configuration (REQUIRED)
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_CHAT_DEPLOYMENT=your_deployment_name
AZURE_EMBEDDINGS_DEPLOYMENT=your_embeddings_deployment

# Database Configuration (Optional - defaults to bundled SQLite)
DATABASE_URL=sqlite:///data/adventureworks.sqlite3

# Backend Configuration (Optional)
BACKEND_URL=http://127.0.0.1:8000/api
```

### Step 3: Verify Installation

```bash
python -c "import langchain; import fastapi; import streamlit; print('All dependencies installed!')"
```

---

## How to Run Backend

### Start FastAPI Backend Server

**Terminal 1:**
```bash
python run_api.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

The backend API will be available at:
- **Base URL:** `http://127.0.0.1:8000`
- **Interactive API Docs:** `http://127.0.0.1:8000/api/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/api/redoc`
- **Health Check:** `curl http://127.0.0.1:8000/api/health`

---

## How to Run Streamlit Chatbot

### Start Streamlit Frontend

**Terminal 2 (keep Terminal 1 running with backend):**
```bash
streamlit run app/frontend.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

The chatbot interface will automatically open at `http://localhost:8501`

### Usage
1. Enter your natural language question in the chat input
2. The AI will convert it to SQL and execute it
3. View results, generated SQL, and visualizations in real-time
4. Maintain multiple independent chat sessions

---

## Example Manufacturing Questions

The AdventureWorks database contains manufacturing, sales, and product data. Try these example queries:

### Product Queries
- "What are the top 5 most expensive products?"
- "What are the size and weight of the product CA‑5965?"
- "Show me products with a list price between $100 and $200"
- "What is the color of product CN-6137?"
- “What are the size and weight of product CA‑5965?”
- “List all products with DaysToManufacture greater than 0.”
- “Show the product name and total quantity sold for ProductID 783.”
- “Show the UnitPrice and product color for ProductID 318.”
- “List all products with StockedQty equal to 550.”

### Sales and Transaction Queries
- “Show the total actual cost for ProductID 783.”
- “How many transactions occurred for ProductID 921?”
- “Show the total quantity transacted for ProductID 715.”
- “Show the total quantity for ProductID 981 with transaction type ‘S’.”
- “How many transactions happened on 2014‑05‑21 for ProductID 873?”
- “Show the total actual cost for product AR‑5381 using transaction history.”
- “Show the days to manufacture for product BA‑8327.”
- “Show OrderQty and ScrappedQty for WorkOrderID 4.”
- “How many work orders exist for ProductID 732 between 2011‑06‑01 and 2011‑06‑20?”
- “Show the total OrderQty for ProductID 738 on 2011‑06‑03.”

### Manufacturing Queries
- "How many products are currently in stock?"
- “List all operation sequences and locations for WorkOrderID 13.”
- “Show the ActualStartDate and ActualEndDate for WorkOrderID 14 at LocationID 20.”
- “How many work orders exist for product CA‑5965 (ProductID 317)?”
- “Show the total routing cost for WorkOrderID 13.”


---

## Demo Video

### Watch the Chatbot in Action

A demo video showcasing the chatbot answering real manufacturing queries is available here:

**[📹 Demo Video Link - Coming Soon](#demo-video-link)**

### Demo Video Contents

The demo video demonstrates:
1. **Starting the Application**: Activating the environment and launching both backend and frontend
2. **Product Queries**: "What are the top 5 most expensive products?"
3. **Sales Queries**: "Show me the top 10 customers by total order value"
4. **Manufacturing Queries**: "How many products are currently in stock?"
5. **Real-time SQL Execution**: Viewing generated SQL and immediate results
6. ** Follow up Question Answering ** : Chatbot responding to the follow up quetsions by using the memory
7. **Multi-session Management**: Managing multiple independent conversations


### Creating Your Own Demo Video

To record a demo video of the chatbot:

1. **Setup**: Ensure both backend (`python run_api.py`) and frontend (`streamlit run app/frontend.py`) are running
2. **Recording Tool Options**:
   - **Windows**: Built-in Xbox Game Bar (Win + G)
   - **macOS**: QuickTime Player
   - **Linux**: OBS Studio (Open Broadcaster Software)
   - **Cross-platform**: OBS Studio or Camtasia
3. **Recording Steps**:
   - Open browser to `http://localhost:8501`
   - Record at 1080p (1920x1080) for clarity
   - Capture 2-3 example queries from each category
   - Include SQL viewing and results display
   - Duration: 3-5 minutes recommended
4. **Hosting Options**:
   - YouTube
   - Vimeo
   - GitHub Releases
   - Project Wiki
5. **Update Link**: Replace `#demo-video-link` above with your video URL

---

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
