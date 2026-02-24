# 🧠 NL2SQL — Natural Language → SQL for Manufacturing Analytics

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Chatbot%20UI-FF4B4B?logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-Project%20Use-informational)

> A production‑ready NL2SQL system that converts **natural language** questions into **validated SQL**, executes them on an **AdventureWorks-style manufacturing database**, and returns:
> - Human-friendly answers  
> - Final SQL  
> - Tabular results  
> - Auto-generated charts  

---

## ✨ Key Highlights

- **Complete NL2SQL pipeline:**  
  *User Query → Intent → SQL Generation → Validation → Execution → Answer → Visualization*
- **Manufacturing-aware:** costs, suppliers, work orders, rejects, timestamps, currency/date analytics  
- **Safe SQL generation:** SELECT-only, schema validated, retry logic  
- **Insightful outputs:** human-like answers, SQL, data table, chart recommendations  

---



## 🧭 Architecture at a Glance

```mermaid
flowchart LR

  %% ================= Styles (Azure theme) =================
  classDef azureBlue fill:#0078D4,stroke:#005A9E,color:#ffffff,stroke-width:1.3px,rx:6,ry:6;
  classDef panel fill:#E6F1FB,stroke:#C7E0F4,color:#1A1A1A,stroke-width:1px,rx:10,ry:10;
  classDef card fill:#FFFFFF,stroke:#005A9E,color:#1A1A1A,stroke-width:1.2px,rx:8,ry:8;
  classDef data fill:#FFFFFF,stroke:#5B9BD5,color:#1A1A1A,stroke-width:1.2px,rx:8,ry:8;
  linkStyle default stroke:#005A9E,stroke-width:1.2px;

  %% ================= Input Layer =================
  subgraph INPUT[Input]
    direction TB
    USER["(User / Streamlit UI)"]:::card
    LLM["[Azure OpenAI<br/>GPT-4o / GPT-4.1]"]:::azureBlue
  end
  class INPUT panel

  %% ================= Core Pipeline =================
  subgraph CORE[NL2SQL System]
    direction TB
    ORCH[Orchestrator]:::card
    LINK[Schema / Metadata Linker]:::card
    SQLA[SQL Synthesis Agent]:::card
    VAL[Validator & Guard]:::card
    EXEC[Query Executor]:::card
    DEC{Execution Result?}:::card
    DBG["Debug Agent (auto-repair)"]:::card
    ANSLLM[LLM Answer Generator]:::card
    OUT[Final Response to User]:::card
  end
  class CORE panel

  %% ================= Data & Registry =================
  subgraph DATA[Data & Registry]
    direction LR
    DB["(Read-only Database)"]:::data
    MR["(Metadata Registry)"]:::data
  end
  class DATA panel

  %% ================= Tools (compact strip) =================
  subgraph TOOLS[Tools & Libraries]
    direction TB
    TOOLSTRIP[LangGraph · FastAPI · SQLAlchemy · sqlglot · dateutil · Altair/Vega-Lite]:::card
  end
  class TOOLS panel

  %% ================= Main Control/Data Flow =================
  USER --> ORCH
  LLM --> ORCH
  ORCH --> LINK --> SQLA --> VAL --> EXEC --> DEC

  %% ======= Branches after execution (3 explicit conditions) =======
  DEC -->|Rows returned| ANSLLM
  DEC -->|Empty result| DBG
  DEC -->|SQL error| DBG

  %% ======= Retry path from Debug back to Orchestrator =======
  DBG -->|repair & retry| ORCH

  %% ======= Human-like response back to the user =======
  ANSLLM --> OUT --> USER

  %% ======= Minimal data references (kept uncluttered) =======
  LINK --- MR
  SQLA --- MR
  EXEC --- DB
```


### 📌 Chart Selection Rules
- **Line chart** → Time series  
- **Bar chart** → Category-based aggregates  
- **Pie chart** → Composition breakdowns  

---

## 🏭 Manufacturing Scope

### Supported Analytics
- Raw material & production **costs**  
- Work order **scheduled vs actual** timestamps  
- Supplier **purchase order quantities**  
- Incoming **reject/scrap quantities**  
- Integer, currency, and date-based manufacturing metrics  

### Example Queries
- “Total raw material cost for January 2024”  
- “Work orders where actual end date exceeded scheduled date”  
- “Top 10 suppliers by purchase order quantity”  
- “Monthly trend of incoming rejects”  

---

## 🗂️ Repository Structure

```
project/
│── .gitignore
│── main.py
│── README.md
│── requirements.txt
│
├── .vscode/
│   ├── extensions.json
│   ├── launch.json
│   └── settings.json
│
├── app/
│   ├── frontend.py
│   ├── graph.py
│   ├── routes.py
│   ├── schemas.py
│   └── __init__.py
│
└── tests/
    ├── test_graph.py
    └── test_main.py
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/mahithi906/NL2SQL.git
cd NL2SQL
```

### 2️⃣ Create & activate virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🖥️ Visual Studio Code Quick Start

Open the project folder in VS Code:

```bash
code .
```

Then follow these steps:

### 1️⃣ Select the Python interpreter
- Press **Ctrl+Shift+P** → `Python: Select Interpreter`
- Choose **`.venv`** (the virtual environment created above)

### 2️⃣ Install recommended extensions
VS Code will prompt you to install the recommended extensions automatically.  
If not, press **Ctrl+Shift+P** → `Extensions: Show Recommended Extensions`.

| Extension | Purpose |
|---|---|
| Python (ms-python.python) | Core Python support |
| Pylance | Fast type-checking & IntelliSense |
| Black Formatter | Auto-format on save |
| Debugpy | Advanced debugging |
| GitLens | Git history & blame |
| GitHub Copilot | AI code completion |

### 3️⃣ Run / Debug
Use the **Run & Debug** panel (**Ctrl+Shift+D**) and pick a configuration:

| Configuration | What it does |
|---|---|
| **FastAPI: uvicorn (dev)** | Starts the API on `http://localhost:8000` with hot-reload |
| **Streamlit: frontend** | Starts the chatbot UI on `http://localhost:8501` |
| **Pytest: all tests** | Runs all tests with verbose output |

### 4️⃣ Run tests from the Testing panel
- Press **Ctrl+Shift+P** → `Python: Configure Tests` → select **pytest** and `tests/` folder
- Click the ▶️ icon in the **Testing** side panel to run or debug individual tests

---

## 🔌 Database Configuration

Create `.env` file:

```env
DB_DRIVER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=adventureworks
DB_USER=your_user
DB_PASSWORD=your_password
```

### Data Sources
- Kaggle: https://www.kaggle.com/datasets/universalanalyst/adventureworks-sample-mfg-database-tables  
- Microsoft Docs: https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure

Ensure your DB matches `config/schema.json`.

---

## ▶️ How to Run

### 1️⃣ Start backend (FastAPI)
```bash
uvicorn backend.api:app --reload --port 8000
```

### 2️⃣ Start chatbot UI (Streamlit)
```bash
streamlit run frontend.py
```

Visit: http://localhost:8501/

---

## 💬 Example Prompts

- “Total raw material cost for January 2024”  
- “How many work orders finished after the scheduled end date?”  
- “Top 10 suppliers by purchase order quantity in 2023”  
- “Monthly trend of incoming rejects”  
- “Average production cost by product category”  

---

## 🧠 API (FastAPI)

### POST `/nl2sql/query`

#### Request
```json
{
  "question": "Show total raw material cost for January 2024",
  "options": { "limit": 100, "visualize": true }
}
```

#### Success Response
```json
{
  "answer": "The total raw material cost for January 2024 was ₹5,43,000.",
  "sql": "SELECT ...",
  "table": [{ "col1": "value" }],
  "chart": { "type": "bar", "data": {} },
  "meta": { "elapsed_ms": 128, "rows": 12 }
}
```

#### On Failure (after 3 attempts)
```json
{
  "error": "No valid result could be generated for your query.",
  "retries": 3
}
```

---

## ✅ SQL Safety & Validation

- SELECT-only (no INSERT/UPDATE/DELETE)  
- Validates tables & columns  
- Ensures join paths  
- Rejects unsafe patterns  
- Retry loop (≤3 times)  

---

## 📊 Visualization Engine

- **Line** → time-series  
- **Bar** → category-based  
- **Pie** → composition  
- Outputs JSON config for Streamlit rendering  

---

## 🧪 Testing

```bash
pytest -q
```

Quick test:
```bash
curl -X POST http://localhost:8000/nl2sql/query \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Top 10 suppliers by purchase order quantity\"}"
```
## 🙌 Credits
- Developed by: Mahithi Reddy
- Mentorship: Ashfak K A
- Inspired by AdventureWorks Manufacturing Schema
---

