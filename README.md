# Budget Tracker Filter

A Streamlit application for filtering and translating monthly budget data from Excel files.

## Features
- **Upload & Auto-Update**:
    - Upload monthly budget Excel files.
    - **Master Dataset**: Automatically updates a tracked `master/master.xlsx` file with new unique records (based on `Period` timestamp).
    - **Backup**: Keeps a local copy of uploaded files in `data/` (ignored by git).
- **Dynamic Filtering**: Cascading filters for Date, Category, Subcategory, etc.
- **Favorites**: One-click application of frequently used filter sets.
- **Translation**: Translate filtered results to **Sinhala** using Google Translate (Deep Translator).
- **Export Options**:
    - **Excel**: Download filtered or translated datasets.
    - **Image (PNG)**: Download a beautifully formatted image of your data table.
- **Total Row**: Toggle a summary row to see total amounts.

## Workflow
1.  **Launch App**: `streamlit run app.py`
    -   *Default URL*: `http://localhost:3069`
2.  **Upload**: Drag & drop your latest budget Excel file.
    -   *System Action*: Updates `master/master.xlsx` with new entries and saves backup to `data/`.
3.  **Filter**: Use the sidebar to drill down into specific expenses/incomes.
4.  **Visualize/Translate**: Check your data, optionally translate to Sinhala.
5.  **Export**: Download the result as an Excel sheet or a PNG image for sharing.

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
The application will open in your default web browser on `http://localhost:3069`.
