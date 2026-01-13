# Actuarial Model Projection Tool

A web-based actuarial projection tool for term life insurance that accepts natural language input, parses assumptions using an LLM, and generates month-by-month cashflow projections.

## Features

- **Natural Language Input**: Describe your policy in plain English (e.g., "1,000 policies, £100k sum assured, 10-year term, age 40, 3% interest, £50 monthly premium")
- **AI-Powered Parsing**: Uses Claude to extract structured assumptions from free-form text
- **ELT17 Mortality Table**: Standard UK mortality table (English Life Table No. 17) from ONS
- **Month-by-Month Projections**: Calculates deaths, premiums, claims, and reserves for each month
- **CPU/GPU Compute Options**: Run projections on CPU or GPU
- **CSV Export**: Download the complete cashflow table for further analysis
- **Activity Tracking**: View execution history with timestamps, response times, and full request/response data

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **LLM**: Anthropic Claude API
- **Database**: SQLite (activity logging)
- **Data Processing**: Pandas

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/themitchelli/ai-built-actuarial-model.git
   cd ai-built-actuarial-model
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Anthropic API key:
   ```bash
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

5. Start the server:
   ```bash
   python run.py
   ```

6. Open http://localhost:8000 in your browser

## Usage

1. Enter your policy assumptions in natural language in the text box
2. Click **Parse & Review** to extract structured assumptions using AI
3. Review the parsed assumptions
4. Click **Run Projection** to generate the cashflow projection
5. View results in the table or click **Download CSV** to export

## Example Input

```
1,000 policies, £100k sum assured, 10-year term, age 40, standard mortality, 3% interest, £50 monthly premium
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/activity` | GET | Activity dashboard |
| `/execution/{id}` | GET | Execution detail page |
| `/api/parse` | POST | Parse natural language to structured assumptions |
| `/api/project` | POST | Run projection with given assumptions |
| `/api/export` | POST | Download CSV of projection results |
| `/api/executions` | GET | List all executions (with stats) |
| `/api/executions/{id}` | GET | Get execution details |
| `/docs` | GET | Swagger API documentation |

## Projection Model

The projection calculates for each month:

- **Deaths**: Using ELT17 mortality rates converted to monthly probabilities
- **Premiums**: Collected from policies in force
- **Claims**: Death benefit payments
- **Reserves**: Prospective reserve (PV of future benefits - PV of future premiums)

### Mortality Conversion

Annual mortality rates (qx) are converted to monthly rates using:
```
qx_monthly = 1 - (1 - qx_annual)^(1/12)
```

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLite activity logging
│   ├── llm_parser.py        # Natural language parsing with Claude
│   ├── models.py            # Pydantic data models
│   ├── mortality_tables.py  # ELT17 mortality data
│   └── projection_engine.py # Actuarial calculations
├── static/
│   ├── index.html           # Web interface
│   ├── activity.html        # Activity dashboard
│   └── execution.html       # Execution detail page
├── .env                     # API key (not in repo)
├── .gitignore
├── requirements.txt
├── run.py                   # Entry point
└── README.md
```

## License

MIT
