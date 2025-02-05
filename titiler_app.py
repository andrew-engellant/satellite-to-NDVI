from fastapi import FastAPI
from titiler.core.factory import TilerFactory
import uvicorn

# ---- FastAPI & TiTiler Setup ----
app = FastAPI()
cog = TilerFactory()

# Include TiTiler router for COG access
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

# ---- Run TiTiler Server ----
if __name__ == "__main__":
    uvicorn.run("titiler_app:app", host="0.0.0.0", port=8000, reload=True)