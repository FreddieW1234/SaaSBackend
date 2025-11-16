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


class LoginResponse(BaseModel):
    userId: str
    companyId: str


class SignupResponse(BaseModel):
    userId: str
    companyId: str


class UserResponse(BaseModel):
    id: int
    email: str
    company_id: int
    created_at: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    shopify_domain: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    created_at: str


class DashboardCompanyResponse(BaseModel):
    company_id: str
    name: str
    data: Optional[dict] = None


