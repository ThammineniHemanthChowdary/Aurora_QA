import uvicorn
from app.api import app

if __name__ == "__main__":
    # Runs the FastAPI app on localhost:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
