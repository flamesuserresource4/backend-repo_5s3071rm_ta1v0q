"""
Database Schemas for AI Marketplace

Each Pydantic model maps to a MongoDB collection whose name is the lowercase
version of the class name. Use these to validate incoming data and to keep a
consistent shape for documents.
"""

from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile avatar URL")
    is_seller: bool = Field(False, description="Whether user is a seller")


class Listing(BaseModel):
    title: str = Field(..., description="Product title")
    type: str = Field(..., description="Type of AI product (chatbot, webflow, workflow, template, other)")
    description: str = Field(..., description="Detailed description of the product")
    price: float = Field(..., ge=0, description="Price in USD")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    seller_name: str = Field(..., description="Seller display name")
    seller_email: EmailStr = Field(..., description="Seller contact email")
    demo_url: Optional[HttpUrl] = Field(None, description="Demo or preview URL")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail or cover image URL")


class Order(BaseModel):
    listing_id: str = Field(..., description="ID of the purchased listing")
    buyer_name: str = Field(..., description="Buyer name")
    buyer_email: EmailStr = Field(..., description="Buyer email")
    status: str = Field("completed", description="Order status")
