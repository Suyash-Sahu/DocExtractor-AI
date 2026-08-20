"""
LLM-based document field extraction.

Primary provider:
    OpenRouter

Fallback provider:
    Ollama

The LLM extracts information from invoices/receipts.
The output is then:

    LLM
      ↓
    JSON parsing
      ↓
    Required-field validation
      ↓
    Output normalization
      ↓
    Pydantic validation
      ↓
    Deterministic validation
"""

import json
import re

from extractor.llm.provider import generate_response


# ============================================================
# Required Output Fields
# ============================================================

REQUIRED_OUTPUT_FIELDS = [
    "document_type",
    "document_id",
    "vendor",
    "customer",
    "invoice_date",
    "due_date",
    "currency",
    "line_items",
    "subtotal",
    "tax_amount",
    "discount",
    "total",
    "payment_status",
    "payment_method",
]


# ============================================================
# System Prompt
# ============================================================

EXTRACTION_SYSTEM_PROMPT = """
You are a professional document data extraction engine.

Your task is to extract structured information from
invoices and receipts.

============================================================
OUTPUT RULES
============================================================

Return ONLY valid JSON.

Do NOT return:

- Markdown
- Code fences
- Explanations
- Comments
- Extra fields
- Text before the JSON
- Text after the JSON

The response MUST be exactly one JSON object.

============================================================
REQUIRED JSON KEYS
============================================================

Your JSON object MUST ALWAYS contain ALL of these keys:

- document_type
- document_id
- vendor
- customer
- invoice_date
- due_date
- currency
- line_items
- subtotal
- tax_amount
- discount
- total
- payment_status
- payment_method

IMPORTANT:

"Required key" means the KEY must exist.

It does NOT mean the value must exist.

If information is unavailable, use null.

For example:

"currency": null

Do NOT remove the currency key.

If customer information is absent:

"customer": null

Do NOT remove the customer key.

If discount is absent:

"discount": null

Do NOT remove the discount key.

============================================================
EXACT JSON STRUCTURE
============================================================

Return exactly this structure:

{
  "document_type": "invoice",
  "document_id": null,

  "vendor": {
    "name": "",
    "address": null,
    "tax_id": null
  },

  "customer": null,

  "invoice_date": null,
  "due_date": null,

  "currency": null,

  "line_items": [],

  "subtotal": null,
  "tax_amount": null,
  "discount": null,

  "total": 0,

  "payment_status": null,
  "payment_method": null
}

IMPORTANT:

The values above are examples only.

Replace them with values extracted from the document.

Do NOT copy the example values.

Do NOT remove any keys.

============================================================
VENDOR
============================================================

vendor MUST always be an object.

Example:

"vendor": {
  "name": "ABC Technologies Pvt Ltd",
  "address": "Bengaluru, Karnataka, India",
  "tax_id": "29ABCDE1234F1Z5"
}

The vendor name must come from the document.

Do not invent vendor information.

If vendor information is truly unavailable, use:

"vendor": {
  "name": null,
  "address": null,
  "tax_id": null
}

============================================================
CUSTOMER
============================================================

If customer information exists, customer MUST be an object.

Example:

"customer": {
  "name": "XYZ Solutions Pvt Ltd",
  "address": "Bengaluru, Karnataka, India",
  "tax_id": null
}

If customer information does not exist:

"customer": null

Never return customer as a plain string.

============================================================
EXTRACTION RULES
============================================================

1. Extract ONLY information explicitly present in the
   document.

2. NEVER invent, guess, or assume information.

3. If a field is not present, return null.

4. Dates MUST use:

   YYYY-MM-DD

5. DOCUMENT ID EXTRACTION

Look for document identifiers associated with labels such as:

- Invoice #
- Invoice No
- Invoice No.
- Invoice Number
- Bill No
- Bill Number
- Receipt #
- Receipt No
- Receipt Number

The value associated with these labels must be extracted
as document_id.

Example:

Invoice #
TN-8742

must produce:

"document_id": "TN-8742"

6. NUMERIC VALUES

Numeric fields MUST be JSON numbers.

Correct:

"total": 132160

Incorrect:

"total": "132,160"

Remove:

- Currency symbols
- Thousands separators

7. LINE ITEMS

Extract every identifiable line item.

Each line item MUST contain:

- description
- quantity
- unit_price
- tax_rate
- amount

Example:

{
  "description": "Laptop",
  "quantity": 2,
  "unit_price": 55000,
  "tax_rate": 18,
  "amount": 110000
}

If tax rate is not explicitly available:

"tax_rate": null

IMPORTANT LINE ITEM RULE:

If the document provides quantity and total line-item amount
but does NOT explicitly provide unit price, you MAY calculate:

unit_price = amount / quantity

ONLY when:

- quantity is explicitly available
- amount is explicitly available
- quantity is greater than zero
- the division produces a meaningful numeric value

Example:

Laptop
Quantity: 1
Amount: 65000

Therefore:

"quantity": 1,
"unit_price": 65000,
"amount": 65000

Example:

Keyboard
Quantity: 2
Amount: 3000

Therefore:

"quantity": 2,
"unit_price": 1500,
"amount": 3000

This is a deterministic calculation, not a guessed value.

Do NOT calculate unit price if quantity or amount is missing.
In that case use:

"unit_price": null

8. TAX

If tax is split into CGST and SGST, combine them.

Example:

CGST = 6120
SGST = 6120

Then:

"tax_amount": 12240

Do NOT create separate cgst or sgst fields.

9. SUBTOTAL

Extract subtotal or taxable value when explicitly
provided.

Example:

"Taxable Value": 68000

should become:

"subtotal": 68000

Do not invent a subtotal.

10. TOTAL

Extract the final payable amount explicitly shown
in the document.

Possible labels include:

- Total
- Grand Total
- Amount Payable
- Total Amount
- Net Amount

Example:

"Amount Payable": 80240

must become:

"total": 80240

11. CUSTOMER

Do not invent customer information.

If customer information does not exist:

"customer": null

12. CURRENCY

Extract currency ONLY when explicitly present.

Examples:

- INR
- USD
- EUR
- GBP
- ₹
- $
- €

Do NOT assume INR because the document is from India.

If currency is absent:

"currency": null

13. PAYMENT METHOD AND PAYMENT STATUS

These are different fields.

Payment method examples:

- UPI
- Cash
- Credit Card
- Debit Card
- Bank Transfer
- Card

These must be stored in:

"payment_method"

Example:

Document says:

Payment: UPI

Output:

"payment_status": null,
"payment_method": "UPI"

14. PAYMENT STATUS

Only populate payment_status when the document
explicitly states a payment status.

Examples:

- Paid
- Payment Completed
- Settled
- Unpaid
- Pending
- Partially Paid

Example:

Document says:

Status: Paid

Output:

"payment_status": "Paid",
"payment_method": null

15. DOCUMENT TYPE

document_type MUST be exactly one of:

"invoice"

or

"receipt"

Use the detected document type provided by the
application as guidance.

16. DO NOT OMIT FIELDS

Every required top-level key MUST exist.

If information is unavailable, use null.

============================================================
FINAL CHECK
============================================================

Before returning the response, verify:

- Is it valid JSON?
- Is it exactly one JSON object?
- Are all required keys present?
- Is document_type invoice or receipt?
- Is document_id extracted if explicitly shown?
- Is vendor an object?
- Is customer an object or null?
- Are dates YYYY-MM-DD?
- Are numbers actual JSON numbers?
- Are CGST and SGST combined?
- Is currency null if absent?
- Is payment method separated from payment status?
- Did you avoid guessing?
- Did you include every required key?

Return ONLY the JSON object.
"""


# ============================================================
# JSON Cleaning
# ============================================================

def clean_json_response(raw_response: str) -> str:
    """
    Remove common Markdown formatting from an LLM response.

    Example:

        ```json
        {"total": 100}
        ```

    becomes:

        {"total": 100}
    """

    if not raw_response:
        return ""

    text = raw_response.strip()

    # Remove opening Markdown code fence.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove closing Markdown code fence.
    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


# ============================================================
# Required Field Checker
# ============================================================

def check_required_output_fields(
    data: dict,
) -> list[str]:
    """
    Check whether the LLM returned every required
    top-level JSON key.

    Returns:
        List of missing field names.
    """

    return [
        field
        for field in REQUIRED_OUTPUT_FIELDS
        if field not in data
    ]


# ============================================================
# Output Normalization
# ============================================================

def normalize_extracted_data(
    data: dict,
) -> dict:
    """
    Normalize common LLM output variations before
    Pydantic validation.

    This function does NOT invent information.

    It only converts valid extracted information into
    the expected schema shape.

    Example:

        "customer": "XYZ Solutions Pvt Ltd"

    becomes:

        "customer": {
            "name": "XYZ Solutions Pvt Ltd",
            "address": null,
            "tax_id": null
        }
    """

    # --------------------------------------------------------
    # Normalize vendor
    # --------------------------------------------------------

    vendor = data.get("vendor")

    if isinstance(vendor, str):

        data["vendor"] = {
            "name": vendor,
            "address": None,
            "tax_id": None,
        }

    # --------------------------------------------------------
    # Normalize customer
    # --------------------------------------------------------

    customer = data.get("customer")

    if isinstance(customer, str):

        data["customer"] = {
            "name": customer,
            "address": None,
            "tax_id": None,
        }

    # --------------------------------------------------------
    # Normalize vendor/customer dictionaries
    # --------------------------------------------------------

    for field in ("vendor", "customer"):

        value = data.get(field)

        if isinstance(value, dict):

            value.setdefault(
                "name",
                None,
            )

            value.setdefault(
                "address",
                None,
            )

            value.setdefault(
                "tax_id",
                None,
            )

            data[field] = value

    # --------------------------------------------------------
    # Normalize missing line_items
    # --------------------------------------------------------

    if data.get("line_items") is None:

        data["line_items"] = []

    # --------------------------------------------------------
    # Normalize optional fields
    # --------------------------------------------------------

    optional_fields = [
        "document_id",
        "customer",
        "invoice_date",
        "due_date",
        "currency",
        "subtotal",
        "tax_amount",
        "discount",
        "payment_status",
        "payment_method",
    ]

    for field in optional_fields:

        if field not in data:

            data[field] = None

    # --------------------------------------------------------
    # Normalize line items
    # --------------------------------------------------------

    line_items = data.get("line_items")

    if isinstance(line_items, list):

        for item in line_items:

            if not isinstance(item, dict):
                continue

            # Ensure expected keys exist
            item.setdefault("description", None)
            item.setdefault("quantity", None)
            item.setdefault("unit_price", None)
            item.setdefault("tax_rate", None)
            item.setdefault("amount", None)

            # ------------------------------------------------
            # Derive unit price when possible
            # ------------------------------------------------

            quantity = item.get("quantity")
            amount = item.get("amount")
            unit_price = item.get("unit_price")

            if (
                unit_price is None
                and quantity is not None
                and amount is not None
            ):

                try:

                    quantity_value = float(quantity)
                    amount_value = float(amount)

                    if quantity_value > 0:

                        item["unit_price"] = (
                            amount_value / quantity_value
                        )

                except (
                    TypeError,
                    ValueError,
                    ZeroDivisionError,
                ):
                    pass

            # ------------------------------------------------
            # Convert numeric strings to numbers
            # ------------------------------------------------

            numeric_fields = [
                "quantity",
                "unit_price",
                "tax_rate",
                "amount",
            ]

            for field in numeric_fields:

                value = item.get(field)

                if isinstance(value, str):

                    cleaned = (
                        value
                        .replace(",", "")
                        .replace("₹", "")
                        .replace("$", "")
                        .strip()
                    )

                    try:
                        item[field] = float(cleaned)

                    except ValueError:
                        pass
    
    return data


# ============================================================
# Extraction Function
# ============================================================

def extract_fields(
    text: str,
    doc_type: str,
) -> dict:
    """
    Extract structured fields from document text.

    Provider strategy:

        1. OpenRouter
        2. Ollama fallback

    The provider manager handles the actual LLM request.

    This function handles:

        - Prompt construction
        - JSON parsing
        - Required field validation
        - Output normalization
        - Retry logic

    Args:
        text:
            Raw text extracted from the document.

        doc_type:
            Document classification.

    Returns:
        Structured dictionary.

    Raises:
        ValueError:
            If extraction fails.

        RuntimeError:
            If all LLM providers fail.
    """

    # ========================================================
    # Input Validation
    # ========================================================

    if not text or not text.strip():

        raise ValueError(
            "Cannot extract fields from empty text."
        )

    if doc_type not in {
        "invoice",
        "receipt",
    }:

        raise ValueError(
            f"Unsupported document type: {doc_type}"
        )

    # ========================================================
    # Initial Messages
    # ========================================================

    messages = [
        {
            "role": "system",
            "content": EXTRACTION_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"Detected document type: {doc_type}\n\n"
                "Extract the following document.\n\n"
                "DOCUMENT TEXT:\n"
                f"{text}"
            ),
        },
    ]

    # ========================================================
    # Extraction Attempts
    # ========================================================

    for attempt in range(2):

        print(
            f"LLM extraction attempt "
            f"{attempt + 1}/2..."
        )

        # ----------------------------------------------------
        # Call Provider Manager
        # ----------------------------------------------------

        try:

            raw_response, provider = generate_response(
                messages
            )

            print(
                f"LLM provider used: {provider}"
            )

        except Exception as exc:

            raise RuntimeError(
                "LLM extraction failed.\n"
                f"Error: {exc}"
            ) from exc

        # ----------------------------------------------------
        # Empty Response
        # ----------------------------------------------------

        if not raw_response:

            if attempt == 1:

                raise ValueError(
                    "LLM returned an empty response "
                    "after retry."
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": "",
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was empty.\n\n"
                        "Return the COMPLETE JSON object.\n"
                        "Return ONLY JSON.\n"
                        "Do not omit any required field."
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Clean Response
        # ----------------------------------------------------

        cleaned_response = clean_json_response(
            raw_response
        )

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            data = json.loads(
                cleaned_response
            )

        except json.JSONDecodeError:

            if attempt == 1:

                raise ValueError(
                    "LLM returned invalid JSON "
                    "after retry.\n\n"
                    f"Model response:\n"
                    f"{raw_response}"
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": raw_response,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not "
                        "valid JSON.\n\n"

                        "Return ONLY a valid JSON object.\n"

                        "Do not use Markdown.\n"
                        "Do not include explanations.\n"
                        "Do not add extra fields.\n"
                        "Do not omit required fields.\n\n"

                        "Required fields:\n"

                        + "\n".join(
                            f"- {field}"
                            for field in REQUIRED_OUTPUT_FIELDS
                        )
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Verify JSON Object
        # ----------------------------------------------------

        if not isinstance(data, dict):

            if attempt == 1:

                raise ValueError(
                    "LLM returned valid JSON but "
                    "the response is not a JSON object."
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": raw_response,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was JSON "
                        "but was not a JSON object.\n\n"
                        "Return exactly one JSON object "
                        "containing all required fields."
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Normalize Output
        # ----------------------------------------------------

        data = normalize_extracted_data(
            data
        )

        # ----------------------------------------------------
        # Check Required Fields
        # ----------------------------------------------------

        missing_fields = check_required_output_fields(
            data
        )

        if not missing_fields:

            print(
                "LLM returned all required fields."
            )

            return data

        # ----------------------------------------------------
        # Retry Missing Fields
        # ----------------------------------------------------

        if attempt == 1:

            raise ValueError(
                "LLM returned valid JSON but "
                "missing required fields after retry: "
                + ", ".join(
                    missing_fields
                )
            )

        print(
            "Missing required fields detected: "
            + ", ".join(
                missing_fields
            )
        )

        messages.append(
            {
                "role": "assistant",
                "content": raw_response,
            }
        )

        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous JSON was incomplete.\n\n"

                    "Missing required fields:\n"

                    + "\n".join(
                        f"- {field}"
                        for field in missing_fields
                    )

                    + "\n\n"

                    "Return the COMPLETE JSON object again.\n\n"

                    "IMPORTANT:\n"
                    "- Every required key must be present.\n"
                    "- Use null when information is unavailable.\n"
                    "- Do not omit any key.\n"
                    "- Do not invent values.\n"
                    "- Return ONLY valid JSON.\n"
                    "- Do not use Markdown.\n"
                    "- Do not add explanations."
                ),
            }
        )

    # ========================================================
    # Safety Fallback
    # ========================================================

    raise RuntimeError(
        "Unexpected extraction failure."
    )