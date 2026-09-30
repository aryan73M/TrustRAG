# TrustRAG

## Corporate Intelligence & Benchmarking Platform

TrustRAG is an evidence-grounded corporate research platform that converts annual-report PDFs into structured quantitative analysis, qualitative business intelligence and an interactive research copilot.

The platform is designed to reduce the manual effort involved in comparing companies across financial performance, workforce trends, strategic developments, management changes and sustainability disclosures.

---

## Product Overview

TrustRAG follows a simple workflow:

Upload Annual Reports
→ Extract Document Evidence
→ Retrieve Relevant Passages
→ Extract Structured KPIs
→ Calculate Derived Metrics
→ Generate Qualitative Intelligence
→ Ask Questions Through Research Copilot

---

## Key Features

### 1. Quantitative Intelligence

TrustRAG extracts and analyzes:

- Revenue
- Revenue Growth
- Operating / EBIT Margin
- Profit After Tax
- EPS
- ROE
- Free Cash Flow
- Capital Expenditure
- Operating Cash Flow
- Cash / Liquid Assets
- Employee Headcount
- Employee Attrition

Derived metrics include:

- PAT Margin
- Standardized Free Cash Flow
- FCF Margin
- Revenue per Employee
- Year-over-Year Change

---

### 2. Qualitative Intelligence

The platform identifies evidence-supported developments across:

- Strategy & Business
- Management & Leadership
- Sustainability & ESG
- Workforce & Organization

Each finding is linked to the relevant annual-report page.

---

### 3. Research Copilot

Users can ask natural-language questions about uploaded reports.

Examples:

> Compare revenue growth across the uploaded companies.

> What strategic changes were discussed in FY2025?

> Compare workforce developments between FY2024 and FY2025.

> What sustainability initiatives were disclosed?

The copilot retrieves relevant evidence before generating the answer.

---

### 4. Evidence Explorer

Each extracted KPI can be traced to:

- Company
- Fiscal Year
- Source PDF
- Source Page
- Supporting Evidence

This makes the system more auditable than a conventional general-purpose chatbot.

---

## Architecture

```text
                  Annual Report PDFs
                         │
                         ▼
                 PDF Text Extraction
                         │
                         ▼
                    Chunking
                         │
                         ▼
                Semantic Retrieval
                         │
                         ▼
              Gemini Structured Output
                    ┌────┴────┐
                    │         │
                    ▼         ▼
             Quantitative   Qualitative
               Analysis      Intelligence
                    │         │
                    └────┬────┘
                         ▼
                  TrustRAG Dashboard
                         │
                         ▼
                 Research Copilot