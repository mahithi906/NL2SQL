# 🧠 NL2SQL — Natural Language ➜ SQL for Manufacturing Analytics

> Ask questions in plain English. Get **validated SQL**, **tabular results**, and **beautiful charts** — all tailored for **manufacturing** use cases.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Chatbot%20UI-FF4B4B?logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-Project%20Use-informational)

---

## ✨ What This Project Does

A complete **NL2SQL pipeline** with a **chatbot-style interface** for manufacturing ops data (AdventureWorks‑like schema). It converts natural language questions into validated **SELECT** SQL, executes the query, then returns:

- ✅ A **human-like answer**
- ✅ The **final SQL**
- ✅ **Tabular results**
- ✅ An **optional chart** (line, bar, pie — chosen intelligently)

**Processing Flow**

```mermaid
flowchart LR
    U[User Question] --> IA[Intent Analysis]
    IA --> SCHEMA[Schema & Join Discovery]
    SCHEMA --> SQLGEN[SQL Generation]
    SQLGEN --> VAL[Validation (SELECT-only, safe)]
    VAL -->|valid| EXEC[Execute]
    VAL -->|invalid| FEEDB[Corrective Feedback] --> SQLGEN
    EXEC -->|error| RETRY[Retry up to 3x] --> SQLGEN
    EXEC -->|success| ANSWER[NL Answer + Explanation + Visualization]
