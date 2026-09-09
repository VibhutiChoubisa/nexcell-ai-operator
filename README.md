# NexCell AI Operator

A small working prototype of an AI-powered CRM operator built for the NexCell Autumn Cohort AI Challenge.

The application provides a chat interface where users can ask questions about a fictional CRM dataset or request CRM actions. Read operations can be executed automatically, while write operations require explicit user confirmation before any data is changed.

## Features

* Natural-language CRM interaction through a Streamlit chat interface
* Real LLM integration using Google Gemini
* Typed read-only tools for CRM search and insights
* Typed write tool for creating CRM tasks
* Explicit confirmation before write operations
* Mock CRM dataset stored locally as JSON
* Prevents hallucinated CRM information when records do not exist
* Clearly rejects unsupported operations

## Architecture

```text
User
  |
  v
Streamlit Chat Interface
  |
  v
Gemini AI Operator
  |
  +--------------------+
  |                    |
  v                    v
Ask Tools           Run Tool
(read-only)         (write request)
  |                    |
  v                    v
Mock CRM JSON      Confirmation UI
                       |
                  +----+----+
                  |         |
                Cancel    Confirm
                  |         |
                  v         v
                No write   Execute
                              |
                              v
                         Mock CRM JSON
```

## LLM Provider

* Provider: Google Gemini
* Model: `gemini-3.5-flash-lite`
* SDK: `google-genai`

The model is responsible for interpreting the user's request and selecting an appropriate tool. Application code is responsible for executing the tool and modifying CRM data.

## Available Tools

### Ask tools

#### `search_leads(query)`

Searches the fictional CRM leads by:

* Name
* Company
* Email
* Interest
* Status

This is a read-only operation.

#### `get_insights()`

Returns computed CRM statistics including:

* Total number of leads
* Lead status counts
* Total tasks
* Pending tasks

This is a read-only operation.

### Run tool

#### `create_task(title, due, related_to)`

Prepares a request to create a CRM task.

This is a write operation. The application intercepts the request and displays a confirmation UI before executing the actual database write.

## Safety Design

The prototype follows three key principles:

### 1. Model talks, code operates

The Gemini model decides which tool should be used, but it never directly modifies the CRM data.

Python application code executes the actual tool functions.

### 2. Confirm before act

Every write operation requires explicit user confirmation.

For example:

```text
User request
     |
     v
Gemini proposes create_task
     |
     v
Application displays confirmation
     |
   +---+---+
   |       |
Confirm   Cancel
   |       |
   v       v
 Write   No write
```

### 3. Never invent

If a requested CRM record does not exist, the operator reports that it was not found rather than generating fictional CRM information.

Unsupported operations are also rejected clearly.

## Project Structure

```text
nexcell-ai-operator/
│
├── agent/
│   ├── ai_operator.py
│   └── tools.py
│
├── data/
│   └── crm_data.json
│
├── app.py
├── test_tools.py
├── test_gemini.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env
```

> `.env` contains the Gemini API key and must not be committed to source control.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd nexcell-ai-operator
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

### 5. Run the application

```bash
streamlit run app.py
```

The Streamlit interface will open in the browser.

## Example Interactions

### CRM search

```text
Find the leads interested in AI automation.
```

The operator searches the CRM and returns matching leads.

### CRM insights

```text
How many leads are in the CRM?
```

The operator calls `get_insights()` and returns the computed result.

### Safe write operation

```text
Create a task to call Aisha Khan tomorrow.
```

The operator identifies Aisha Khan, prepares a `create_task` request, and displays a confirmation interface.

The task is only written after the user selects **Confirm**.

### Missing data

```text
Find the lead John Smith.
```

The operator reports that no matching lead exists rather than inventing one.

### Unsupported operation

```text
Delete all leads from the CRM.
```

The operator clearly reports that deletion is unsupported.

## Testing

The project includes basic tests for the local tools and Gemini connection.

Test CRM tools:

```bash
python test_tools.py
```

Test Gemini connectivity:

```bash
python test_gemini.py
```

## Dataset

The project uses a small fictional CRM dataset for demonstration purposes.

No real client, customer, or production CRM data is used.

## Limitations and Next Steps

This prototype intentionally focuses on the core AI Operator interaction and safety pattern.

Possible future improvements include:

* Additional CRM tools such as updating lead status
* More sophisticated date handling
* Stronger tool argument validation
* Persistent database storage
* Authentication and multi-tenant access control
* Audit logging
* Production-grade error handling
* More comprehensive automated tests
* Deployment to a hosted environment

These features are outside the scope of this prototype.
