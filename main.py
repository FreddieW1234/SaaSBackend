import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client

from models import (
    AuthResponse,
    DashboardMetrics,
    DashboardResponse,
    LoginRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    SignupRequest,
)
from supabase_client import get_supabase


FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app = FastAPI(title="B2B SaaS Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Backend running!"}


@app.get("/dashboard/{company_id}", response_model=DashboardResponse)
def get_dashboard(
    company_id: str, supabase: Client = Depends(get_supabase)
) -> DashboardResponse:
    """
    Returns dashboard data for a given company.
    Expects a `dashboard_metrics` table in Supabase with columns:
    company_id, total_revenue, total_customers, active_subscriptions.
    """

    result = (
        supabase.table("dashboard_metrics")
        .select("*")
        .eq("company_id", company_id)
        .maybe_single()
        .execute()
    )

    data: Optional[dict] = getattr(result, "data", None)

    if not data:
        # Return an empty but well-typed response if no data exists yet
        return DashboardResponse(
            company_id=company_id,
            metrics=DashboardMetrics(),
        )

    metrics = DashboardMetrics(
        total_revenue=data.get("total_revenue"),
        total_customers=data.get("total_customers"),
        active_subscriptions=data.get("active_subscriptions"),
    )

    return DashboardResponse(company_id=company_id, metrics=metrics)


@app.get("/settings/{company_id}", response_model=SettingsResponse)
def get_settings(
    company_id: str, supabase: Client = Depends(get_supabase)
) -> SettingsResponse:
    """
    Returns Shopify credentials for a company.
    Expects a `company_settings` table in Supabase with columns:
    company_id, shopify_shop_domain, shopify_access_token, shopify_api_key, shopify_api_secret.
    """

    result = (
        supabase.table("company_settings")
        .select("*")
        .eq("company_id", company_id)
        .maybe_single()
        .execute()
    )

    data: Optional[dict] = getattr(result, "data", None)

    if not data:
        return SettingsResponse(company_id=company_id, shopify=None)

    shopify = {
        "shop_domain": data.get("shopify_shop_domain"),
        "access_token": data.get("shopify_access_token"),
        "api_key": data.get("shopify_api_key"),
        "api_secret": data.get("shopify_api_secret"),
    }

    return SettingsResponse(company_id=company_id, shopify=shopify)


@app.post("/settings/{company_id}", response_model=SettingsResponse)
def update_settings(
    company_id: str,
    payload: SettingsUpdateRequest,
    supabase: Client = Depends(get_supabase),
) -> SettingsResponse:
    """
    Updates Shopify credentials for a company.
    Uses an upsert into the `company_settings` table.
    """

    shopify = payload.shopify

    row = {
        "company_id": company_id,
        "shopify_shop_domain": shopify.shop_domain,
        "shopify_access_token": shopify.access_token,
        "shopify_api_key": shopify.api_key,
        "shopify_api_secret": shopify.api_secret,
    }

    result = supabase.table("company_settings").upsert(row).execute()

    # Use the sent data as the source of truth for the response
    if not getattr(result, "data", None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings.",
        )

    return SettingsResponse(company_id=company_id, shopify=shopify)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """
    Placeholder login endpoint.
    Wire this up later to Supabase Auth or your own auth logic.
    """

    # Placeholder behavior: always succeed.
    return AuthResponse(message="Login successful (placeholder).")


@app.post("/auth/signup", response_model=AuthResponse)
def signup(payload: SignupRequest) -> AuthResponse:
    """
    Placeholder signup endpoint.
    Wire this up later to Supabase Auth or your own auth logic.
    """

    # Placeholder behavior: always succeed.
    return AuthResponse(message="Signup successful (placeholder).")
