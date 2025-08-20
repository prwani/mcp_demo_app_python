import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, workers=1)
