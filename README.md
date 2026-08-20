# 📄 Document Data Extractor

> **AI-powered invoice and receipt extraction with independent deterministic verification**

Document Data Extractor is a production-oriented document processing system that reads invoices and receipts, converts unstructured document content into structured data, validates the extracted data against a Pydantic schema, independently verifies financial calculations using deterministic Python logic, and produces a final confidence-based decision.

The core principle is simple:

**The LLM extracts the information. Python independently verifies the numbers.**

---

## 🎯 Project Overview

Companies often receive invoices and receipts in different layouts and formats. Manually reading these documents and entering vendor details, dates, line items, taxes, and totals into another system is slow and error-prone.

This project automates that workflow.

You provide an invoice or receipt, and the system performs:

```text
Document
   ↓
Text Extraction
   ↓
Document Classification
   ↓
LLM Structured Extraction
   ↓
Pydantic Schema Validation
   ↓
Deterministic Arithmetic Verification
   ↓
Confidence & Status Decision
   ↓
Structured JSON
```

The system is intentionally designed **not to blindly trust the LLM**.

For example, if an invoice contains:

```text
Subtotal: ₹112,000
Tax:      ₹20,160
Total:    ₹140,000
```

the deterministic validation layer calculates:

```text
₹112,000 + ₹20,160 = ₹132,160
```

Since the extracted total is ₹140,000, the document can be flagged for human review rather than being silently accepted.

---

## ✨ Key Features

### 1. Multi-layout document extraction

The system is designed to extract the same structured fields from documents with different layouts.

Example document types included in the project:

- Invoice layout A
- Invoice layout B
- Receipt layout A
- Scanned receipt
- Text documents
- Invalid/mathematically inconsistent invoice

This demonstrates that the extraction pipeline is not tied to a single hardcoded invoice template.

### 2. Automatic document classification

The classifier determines the document type before extraction.

Currently supported:

- `invoice`
- `receipt`

The classification result includes a confidence score.

### 3. LLM-based structured extraction

The LLM extracts fields such as:

- Document type
- Document ID
- Vendor
- Customer
- Tax ID
- Invoice date
- Due date
- Currency
- Line items
- Quantity
- Unit price
- Tax rate
- Amount
- Subtotal
- Tax amount
- Discount
- Total
- Payment status
- Payment method

### 4. Pydantic schema validation

LLM output is validated against strongly typed Pydantic models before it is accepted by the rest of the pipeline.

This prevents malformed structured output from silently entering the system.

### 5. Deterministic financial verification

The project independently checks:

- Line item arithmetic
- Subtotal
- Total calculation
- Invoice/due-date consistency
- Required fields
- Optional-field warnings

For line items:

```text
quantity × unit_price = amount
```

For subtotal:

```text
sum(line_item.amount) = subtotal
```

For total:

```text
subtotal + tax - discount = total
```

These calculations are performed using Python logic rather than an LLM.

### 6. Confidence and decision system

The final result contains:

- Status
- Confidence score
- Confidence level
- Validation checks
- Missing fields
- Failed checks
- Warnings
- Detailed validation information

Possible outcomes include:

```text
ACCEPTED
REVIEW_REQUIRED
```

### 7. OpenRouter + Ollama fallback

The project supports an LLM provider strategy:

```text
Primary
   ↓
OpenRouter
   ↓
If unavailable/fails
   ↓
Local Ollama
```

This allows the system to continue processing when the remote provider is unavailable or rate-limited, assuming Ollama is configured locally.

### 8. Streamlit user interface

The project includes a Streamlit frontend where users can:

- Upload documents
- Start processing
- View document classification
- View confidence
- View vendor/customer information
- View financial information
- View line items
- View deterministic verification results
- View warnings
- Inspect structured JSON
- Download the generated JSON

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │   Streamlit UI      │
                         │      app.py         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   pipeline.py       │
                         │ Orchestrates flow   │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ file_utils.py  │ │ classifier.py  │ │ llm_extract.py │
        │ Text extraction│ │ Doc type       │ │ Structured     │
        │                │ │ classification │ │ extraction     │
        └────────────────┘ └────────────────┘ └───────┬────────┘
                                                       │
                                                       ▼
                                             ┌──────────────────┐
                                             │ llm/provider.py  │
                                             │ OpenRouter       │
                                             │ Ollama fallback  │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │    schema.py     │
                                             │ Pydantic models  │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │  validators.py   │
                                             │ Deterministic    │
                                             │ verification     │
                                             └────────┬─────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │    status.py     │
                                             │ Confidence +     │
                                             │ final decision   │
                                             └──────────────────┘
```

---

# 📁 Project Structure

```text
document-data-extractor/
│
├── extractor/
│   ├── llm/
│   │   └── provider.py
│   │
│   ├── __init__.py
│   ├── classifier.py
│   ├── file_utils.py
│   ├── llm_extract.py
│   ├── pipeline.py
│   ├── schema.py
│   ├── status.py
│   └── validators.py
│
├── output/
│
├── results/
│   └── invoice_layout_a.json
│
├── samples/
│   ├── expected/
│   │   ├── invoice_layout_a.json
│   │   ├── invoice_layout_b.json
│   │   └── receipt_layout_a.json
│   │
│   ├── invoice_invalid.txt
│   ├── invoice_layout_a.pdf
│   ├── invoice_layout_b.pdf
│   ├── receipt_layout_a.pdf
│   ├── receipt_ocr.png
│   ├── receipt_scanned.pdf
│   └── test_document.txt
│
├── tests/
│   ├── test-validators.py
│   ├── test_classifier.py
│   ├── test_file_utils.py
│   ├── test_pipeline.py
│   ├── test_status.py
│   ├── test_status_integration.py
│   ├── test_validation_integration.py
│   └── test_validators.py
│
├── .env.example
├── .gitignore
├── README.md
├── app.py
├── create_scanned_pdf.py
├── demo_extraction.py
├── main.py
├── requirements.txt
├── test.py
├── test_llm.py
├── test_ollama.py
└── test_openrouter.py
```

---

# 🔄 Processing Pipeline

## Step 1 — Text Extraction

The document is read and converted into usable text.

Supported project inputs include:

- PDF
- TXT
- PNG
- JPG
- JPEG

The extracted text becomes the input for classification and structured extraction.

---

## Step 2 — Document Classification

The classifier analyzes the extracted content and determines whether the document is an:

```text
invoice
```

or:

```text
receipt
```

The classifier also produces a confidence score.

---

## Step 3 — LLM Extraction

The extracted text is passed to the configured LLM provider.

The LLM converts the document into structured fields.

Example:

```json
{
  "document_type": "invoice",
  "document_id": "INV-2026-001",
  "vendor": {
    "name": "ABC Technologies Pvt Ltd",
    "address": "Bengaluru, Karnataka, India",
    "tax_id": "29ABCDE1234F1Z5"
  },
  "invoice_date": "2026-08-19",
  "line_items": [
    {
      "description": "Laptop",
      "quantity": 2,
      "unit_price": 55000,
      "amount": 110000
    }
  ],
  "subtotal": 112000,
  "tax_amount": 20160,
  "total": 132160
}
```

---

## Step 4 — Pydantic Validation

The extracted dictionary is validated against the application's Pydantic schema.

This catches issues such as:

- Incorrect data types
- Invalid numeric values
- Invalid field structures
- Missing required schema information

Only schema-valid data continues to deterministic validation.

---

## Step 5 — Deterministic Verification

The validator does not ask the LLM whether the invoice is correct.

Instead, Python independently calculates the values.

### Line item verification

```text
quantity × unit price = amount
```

### Subtotal verification

```text
Σ line item amounts = subtotal
```

### Total verification

```text
subtotal + tax - discount = total
```

### Date verification

```text
due date >= invoice date
```

### Required fields

The system also checks required fields according to document type.

---

## Step 6 — Confidence

The validation and extraction signals are combined into a confidence decision.

Example:

```text
Status           : ACCEPTED
Confidence       : 0.94
Confidence Level : HIGH
```

Warnings can still be reported without rejecting a document.

For example:

```text
Currency was not explicitly present in the document.
Payment method was not explicitly present.
```

---

## Step 7 — Final Decision

The final decision separates warnings from actual validation failures.

```text
ACCEPTED
```

means the required fields and deterministic checks passed.

```text
REVIEW_REQUIRED
```

means the system found something that should be checked by a human.

This prevents the LLM from being the final authority over financial correctness.

---

# 🧾 Example Output

For a valid invoice:

```json
{
  "document_type": "invoice",
  "document_id": "INV-2026-001",
  "vendor": {
    "name": "ABC Technologies Pvt Ltd",
    "address": "Bengaluru, Karnataka, India",
    "tax_id": "29ABCDE1234F1Z5"
  },
  "invoice_date": "2026-08-19",
  "due_date": "2026-09-18",
  "line_items": [
    {
      "description": "Laptop",
      "quantity": 2,
      "unit_price": 55000,
      "tax_rate": 18,
      "amount": 110000
    },
    {
      "description": "Wireless Mouse",
      "quantity": 2,
      "unit_price": 1000,
      "amount": 2000
    }
  ],
  "subtotal": 112000,
  "tax_amount": 20160,
  "total": 132160,
  "validation": {
    "status": "ACCEPTED",
    "is_valid": true,
    "confidence": 0.94,
    "confidence_level": "HIGH"
  }
}
```

---

# 🚨 Invalid Document Example

The repository includes:

```text
samples/invoice_invalid.txt
```

This document is intentionally useful for testing deterministic validation.

For example:

```text
Calculated subtotal = 112000
Tax                  = 20160
Expected total       = 132160
Extracted total      = 140000
```

The deterministic validator correctly identifies:

```python
{
    "passed": False,
    "calculated_total": 132160.0,
    "extracted_total": 140000.0,
    "difference": 7840.0
}
```

This is one of the most important parts of the project because the system does not simply trust the LLM's extracted total.

---

# 🖥️ User Interface

The Streamlit application provides a simple interface for the complete backend pipeline.

The UI includes:

```text
Document Upload
      ↓
Processing Status
      ↓
Document Classification
      ↓
Confidence
      ↓
Extracted Information
      ↓
Financial Summary
      ↓
Line Items
      ↓
Independent Verification
      ↓
Warnings
      ↓
Structured JSON
      ↓
Download JSON
```

Run the UI with:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

---

# ⚙️ Installation

## 1. Clone the project

```bash
git clone <your-repository-url>
cd document-data-extractor
```

If the repository is already downloaded:

```bash
cd document-data-extractor
```

---

## 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell activation is restricted, use:

```powershell
venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Copy the example environment file:

```powershell
copy .env.example .env
```

Then configure the required LLM settings in `.env`.

The project supports:

```text
OpenRouter
Ollama
```

Keep API keys and other secrets in `.env`.

Do **not** commit `.env` to Git.

The repository already contains `.gitignore` for protecting local environment and generated files.

---

# 🤖 LLM Provider Strategy

The extraction layer follows this strategy:

```text
                    ┌───────────────┐
                    │   Extraction  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  OpenRouter   │
                    └───────┬───────┘
                            │
                     failure/rate limit
                            │
                            ▼
                    ┌───────────────┐
                    │    Ollama     │
                    │    Local      │
                    └───────────────┘
```

This provides a remote provider and a local fallback.

If OpenRouter reaches a rate limit, the application can switch to the configured local Ollama provider.

---

# 🦙 Ollama

If you want to use the local fallback, install and run Ollama separately and make sure the required model is available.

Verify the Ollama API is reachable:

```powershell
Invoke-WebRequest http://localhost:11434/api/tags -UseBasicParsing
```

You can also use:

```powershell
curl.exe http://localhost:11434/api/tags
```

> On Windows PowerShell, `curl` can map to `Invoke-WebRequest`. Using `curl.exe` avoids that alias behavior.

---

# ▶️ Running the Project

## Streamlit application

```bash
streamlit run app.py
```

---

## CLI processing

The command-line interface can process an individual document:

```bash
python main.py --file samples/invoice_layout_a.pdf
```

Example:

```bash
python main.py --file samples/invoice_invalid.txt
```

The processed JSON is written to the output directory.

---

## Demo pipeline

Run the demonstration pipeline:

```bash
python demo_extraction.py
```

This processes the sample documents and prints:

- Text extraction
- Classification
- LLM provider
- Pydantic validation
- Deterministic checks
- Confidence
- Final status
- Structured JSON

---

# 🧪 Testing

Run the project test suite:

```bash
pytest
```

Or:

```bash
python -m pytest
```

The test suite covers areas including:

```text
Classifier
File utilities
Pipeline
Status/Confidence
Validators
Validation integration
Status integration
```

Individual tests can also be executed, for example:

```bash
python -m pytest tests/test_validators.py
```

---

# 🧪 Manual Testing

The repository contains several useful test scripts:

```text
test.py
test_llm.py
test_ollama.py
test_openrouter.py
```

These can be used to troubleshoot individual components independently from the full pipeline.

---

# 📂 Sample Documents

The `samples/` directory contains documents used during development and testing.

### Standard documents

```text
invoice_layout_a.pdf
invoice_layout_b.pdf
receipt_layout_a.pdf
```

These demonstrate extraction across different document layouts.

### Scanned/OCR documents

```text
receipt_scanned.pdf
receipt_ocr.png
```

These are useful for testing documents where normal text extraction may be insufficient.

### Invalid document

```text
invoice_invalid.txt
```

This intentionally contains inconsistent financial values and is useful for testing the verification layer.

### Expected results

```text
samples/expected/
```

contains expected JSON outputs for selected sample documents.

---

# 📤 Output

Processed documents generate structured JSON.

Example:

```text
output/
    invoice_invalid.json
```

The output contains both the extracted document information and the validation result.

A typical structure is:

```text
document
├── document_type
├── document_id
├── vendor
├── customer
├── invoice_date
├── due_date
├── currency
├── line_items
├── subtotal
├── tax_amount
├── discount
├── total
├── payment_status
├── payment_method
└── validation
    ├── status
    ├── is_valid
    ├── confidence
    ├── confidence_level
    ├── checks
    ├── missing_fields
    ├── failed_checks
    ├── warnings
    └── details
```

---

# 🧩 Core Modules

| Module | Responsibility |
|---|---|
| `file_utils.py` | Document/text extraction utilities |
| `classifier.py` | Document type classification |
| `llm_extract.py` | Structured field extraction |
| `llm/provider.py` | OpenRouter/Ollama provider handling |
| `schema.py` | Pydantic data models |
| `validators.py` | Deterministic validation |
| `status.py` | Confidence and final status decision |
| `pipeline.py` | End-to-end orchestration |
| `main.py` | CLI entry point |
| `app.py` | Streamlit web interface |
| `demo_extraction.py` | Demonstration runner |

---

# 🔍 Why This Is More Than Basic LLM Extraction

A simple implementation would be:

```text
PDF
 ↓
LLM
 ↓
JSON
```

That approach assumes the LLM is always correct.

This project instead uses:

```text
PDF
 ↓
Text Extraction
 ↓
Classification
 ↓
LLM
 ↓
Pydantic
 ↓
Deterministic Verification
 ↓
Confidence
 ↓
Decision
```

The distinction is important.

The LLM is responsible for understanding messy document content.

Python is responsible for checking whether the extracted numbers are internally consistent.

This separation makes the system more reliable for financial-document processing.

---

# 🛡️ Validation Philosophy

The project follows a simple rule:

> **AI proposes. Deterministic code verifies.**

The LLM can extract:

```text
Subtotal = 112000
Tax = 20160
Total = 140000
```

But Python independently calculates:

```text
112000 + 20160 = 132160
```

Therefore:

```text
Extracted total = 140000
Calculated total = 132160
Difference = 7840
```

The application can then return:

```text
REVIEW_REQUIRED
```

instead of incorrectly accepting the document.

---

# 📊 Example Processing Result

A successful document may produce:

```text
Document Type : INVOICE
Document ID   : INV-2026-001
Confidence    : 94%
Level         : HIGH

Line Item Arithmetic : PASSED
Subtotal             : PASSED
Total Calculation    : PASSED
Date Validation      : PASSED

Status : ACCEPTED
```

Warnings such as missing payment method or currency can still be displayed separately without necessarily causing rejection.

---

# 🚀 Future Improvements

Potential extensions include:

- REST API using FastAPI
- Database persistence
- Batch document processing
- Human review dashboard
- Document history
- Authentication and authorization
- More document types
- Advanced OCR
- Better table extraction
- Multi-page invoice support
- Currency normalization
- Duplicate invoice detection
- Vendor-specific analytics
- Audit logs
- Docker deployment
- Cloud deployment
- Background job processing
- Evaluation metrics for extraction accuracy
- Confidence calibration
- Automated regression testing against expected JSON

---

# 🎓 Project Value

This project demonstrates practical skills in:

- Python
- Generative AI
- LLM integration
- Structured extraction
- Prompt engineering
- Pydantic
- Data validation
- Deterministic business logic
- Document processing
- OCR-aware workflows
- Fallback architecture
- Streamlit
- CLI application design
- Automated testing
- Software modularity

More importantly, it demonstrates a practical AI engineering pattern:

```text
LLM
+
Structured Output
+
Deterministic Verification
+
Confidence
+
Human Review
```

rather than relying on an LLM alone.

---

# 👨‍💻 Author

**Suyash Sahu**

Computer Science & Engineering

AI/ML • Generative AI • Full Stack Development

---

## ⭐ Summary

Document Data Extractor is an AI-powered invoice and receipt processing system that:

```text
READS
  ↓
UNDERSTANDS
  ↓
STRUCTURES
  ↓
VALIDATES
  ↓
CALCULATES
  ↓
VERIFIES
  ↓
DECIDES
```

The key idea is:

> **The AI extracts the data. The system independently checks whether the data makes sense.**
