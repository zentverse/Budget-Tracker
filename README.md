# Budget Tracker Filter

A Streamlit application for filtering and translating monthly budget data from Excel files.

## Features

- **Upload Excel Data**: Load your monthly budget `.xlsx` files.
- **Dynamic Filtering**: Filter by date range, category, subcategory, account, etc.
- **Favorites**: Quickly apply predefined favorite filters.
- **Translation**: Translate filtered data to Sinhala using `deep-translator`.
- **Export**: Download filtered data as Excel or Image (PNG), and translated data as Excel or Image.
- **Total Row**: Option to add a total row for amounts.

## Setup

1.  **Clone the repository** (or download the files).
2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    ```
3.  **Activate the virtual environment**:
    -   Windows: `.\.venv\Scripts\Activate`
    -   Mac/Linux: `source .venv/bin/activate`
4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```
The application will open in your default web browser.
