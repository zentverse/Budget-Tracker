Set-Location -LiteralPath $PSScriptRoot
& ".\.venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --server.port 3069
