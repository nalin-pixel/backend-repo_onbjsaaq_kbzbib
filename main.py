import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Service, Booking

app = FastAPI(title="Adventist Community Services API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility to convert Mongo docs

def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    # Convert datetime to iso
    for k, v in list(doc.items()):
        try:
            import datetime
            if isinstance(v, (datetime.datetime, datetime.date)):
                doc[k] = v.isoformat()
        except Exception:
            pass
    return doc


@app.get("/")
def root():
    return {"message": "Adventist Community Services API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Services
@app.post("/api/services", response_model=dict)
async def create_service(service: Service):
    try:
        new_id = create_document("service", service)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services", response_model=List[dict])
async def list_services(q: Optional[str] = None, category: Optional[str] = None):
    try:
        filter_dict = {}
        if q:
            # Simple regex search across title/description/tags
            filter_dict["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}},
            ]
        if category:
            filter_dict["category"] = {"$regex": f"^{category}$", "$options": "i"}

        docs = get_documents("service", filter_dict)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services/{service_id}", response_model=dict)
async def get_service(service_id: str):
    try:
        doc = db["service"].find_one({"_id": ObjectId(service_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Service not found")
        return serialize_doc(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Bookings
@app.post("/api/bookings", response_model=dict)
async def create_booking(booking: Booking):
    try:
        # Verify service exists
        try:
            _ = db["service"].find_one({"_id": ObjectId(booking.service_id)})
            if _ is None:
                raise HTTPException(status_code=404, detail="Service not found for booking")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid service_id")

        new_id = create_document("booking", booking)
        return {"id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookings", response_model=List[dict])
async def list_bookings(service_id: Optional[str] = None, status: Optional[str] = None):
    try:
        filter_dict = {}
        if service_id:
            try:
                filter_dict["service_id"] = service_id
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid service_id")
        if status:
            filter_dict["status"] = status
        docs = get_documents("booking", filter_dict)
        return [serialize_doc(d) for d in docs]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple schema reflection for admin tooling
class SchemaInfo(BaseModel):
    name: str
    fields: List[str]


@app.get("/schema", response_model=List[SchemaInfo])
async def get_schema():
    return [
        SchemaInfo(name="service", fields=list(Service.model_fields.keys())),
        SchemaInfo(name="booking", fields=list(Booking.model_fields.keys())),
    ]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
