"""
This script sets up a FastAPI server for serving Cloud Optimized GeoTIFF (COG) files. 

Key features include:
- A root endpoint ("/") that returns a message indicating the server is running and lists available endpoints.
- An endpoint ("/available_days") that retrieves and returns a list of available days for specific months based on the directory structure of historic raster data stored on an external drive. The months considered are April through October.
- The server runs on host "0.0.0.0" and port 8000, with automatic reloading enabled for development purposes.

The script utilizes the `uvicorn` server to run the FastAPI application.
"""

from fastapi import FastAPI
from titiler.core.factory import TilerFactory
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

# Add a root endpoint
@app.get("/")
def read_root():
    return {"message": "TiTiler server is running", "endpoints": ["/cog", "/available_days", "/docs"]}


# Enable CORS for all origins (adjust as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cog = TilerFactory()
app.include_router(cog.router, prefix="/cog", tags=["Cloud Optimized GeoTIFF"])

# Endpoint to get available days based on data directories
@app.get("/available_days", tags=["Metadata"])
def get_available_days():
    BASE_DIR = '/Volumes/Drew_ext_drive/NDVI_Proj/historic_rasters/2024'
    months = ["April", "May", "June", "July", "August", "September", "October"]
    available_days = {}

    for month in months:
        month_path = os.path.join(BASE_DIR, month)
        if os.path.isdir(month_path):
            available_days[month] = [
                d for d in os.listdir(month_path)
                if os.path.isdir(os.path.join(month_path, d))
            ]
    return available_days


if __name__ == "__main__":
    uvicorn.run("titiler_server:app", host="0.0.0.0", port=8000, reload=True)