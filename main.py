import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Listing, Order, User

app = FastAPI(title="AI Marketplace API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class ListingOut(BaseModel):
    id: str
    title: str
    type: str
    description: str
    price: float
    tags: List[str] = []
    seller_name: str
    seller_email: str
    demo_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class OrderOut(BaseModel):
    id: str
    listing_id: str
    buyer_name: str
    buyer_email: str
    status: str


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    d = {**doc}
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # convert ObjectId fields if present
    if "listing_id" in d and isinstance(d["listing_id"], ObjectId):
        d["listing_id"] = str(d["listing_id"])
    return d


@app.get("/")
def read_root():
    return {"message": "AI Marketplace Backend Running"}


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
            response["database_name"] = db.name
            # Try listing collections
            collections = db.list_collection_names()
            response["collections"] = collections[:10]
            response["connection_status"] = "Connected"
            response["database"] = "✅ Connected & Working"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


@app.get("/schema")
def get_schema():
    return {
        "user": User.model_json_schema(),
        "listing": Listing.model_json_schema(),
        "order": Order.model_json_schema(),
    }


# Listings
@app.post("/api/listings", response_model=ListingOut)
def create_listing(payload: Listing):
    inserted_id = create_document("listing", payload)
    doc = db["listing"].find_one({"_id": ObjectId(inserted_id)})
    return ListingOut(**serialize_doc(doc))


@app.get("/api/listings", response_model=List[ListingOut])
def list_listings(
    q: Optional[str] = Query(None, description="Search text across title and description"),
    type: Optional[str] = Query(None, description="Filter by product type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=100)
):
    filter_dict: dict = {}
    if type:
        filter_dict["type"] = type
    if tag:
        filter_dict["tags"] = {"$in": [tag]}
    if q:
        # Simple regex search on title/description
        regex = {"$regex": q, "$options": "i"}
        filter_dict["$or"] = [{"title": regex}, {"description": regex}, {"tags": regex}]

    docs = get_documents("listing", filter_dict, limit)
    return [ListingOut(**serialize_doc(d)) for d in docs]


@app.get("/api/listings/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: str):
    try:
        oid = ObjectId(listing_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid listing id")
    doc = db["listing"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingOut(**serialize_doc(doc))


# Orders
@app.post("/api/orders", response_model=OrderOut)
def create_order(payload: Order):
    # validate listing exists
    try:
        oid = ObjectId(payload.listing_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid listing id")

    listing = db["listing"].find_one({"_id": oid})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    data = payload.model_dump()
    # store listing_id as ObjectId
    data["listing_id"] = oid
    inserted_id = create_document("order", data)
    doc = db["order"].find_one({"_id": ObjectId(inserted_id)})
    return OrderOut(**serialize_doc(doc))


@app.get("/api/orders", response_model=List[OrderOut])
def list_orders(buyer_email: Optional[str] = None, limit: int = Query(50, ge=1, le=100)):
    filter_dict = {}
    if buyer_email:
        filter_dict["buyer_email"] = buyer_email
    docs = get_documents("order", filter_dict, limit)
    return [OrderOut(**serialize_doc(d)) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
