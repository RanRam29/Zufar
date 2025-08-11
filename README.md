
# Zufar – Casualty Management

## Local run
```
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
set JWT_SECRET=devsecret  # PowerShell: $env:JWT_SECRET="devsecret"
set DATABASE_URL=sqlite:///./zufar.db
python -m uvicorn backend.app:app --reload
```
Open http://127.0.0.1:8000/static/
