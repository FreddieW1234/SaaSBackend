from typing import Optional

from pydantic import BaseModel, EmailStr


class ShopifyCredentials(BaseModel):
    shop_domain: Optional[str] = None
    access_token: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class SettingsResponse(BaseModel):
    company_id: str
    shopify: Optional[ShopifyCredentials] = None


class SettingsUpdateRequest(BaseModel):
    shopify: ShopifyCredentials


class DashboardMetrics(BaseModel):
    total_revenue: Optional[float] = None
    total_customers: Optional[int] = None
    active_subscriptions: Optional[int] = None


class DashboardResponse(BaseModel):
    company_id: str
    metrics: DashboardMetrics


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str


class AuthResponse(BaseModel):
    message: str


