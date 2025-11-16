import bcrypt
import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client

from models import (
    CompanyResponse,
    DashboardCompanyResponse,
    LoginRequest,
    LoginResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    SignupRequest,
    SignupResponse,
)
from supabase_client import get_supabase


FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app = FastAPI(title="B2B SaaS Backend", version="1.0.0")

# Allow multiple origins for Vercel deployment
allowed_origins = [
    FRONTEND_ORIGIN,
    "http://localhost:3000",
    "https://*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Backend running!"}


@app.get("/dashboard/{company_id}", response_model=DashboardCompanyResponse)
def get_dashboard(
    company_id: str, supabase: Client = Depends(get_supabase)
) -> DashboardCompanyResponse:
    """
    Returns dashboard data for a given company.
    Fetches company from companies table and dashboard_data if exists.
    """

    # Fetch company
    company_result = (
        supabase.table("companies")
        .select("*")
        .eq("id", int(company_id))
        .maybe_single()
        .execute()
    )

    company_data: Optional[dict] = getattr(company_result, "data", None)

    if not company_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found.",
        )

    # Fetch dashboard data if exists (most recent first)
    dashboard_result = (
        supabase.table("dashboard_data")
        .select("*")
        .eq("company_id", int(company_id))
        .order("created_at", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )

    dashboard_data: Optional[dict] = getattr(dashboard_result, "data", None)
    data_json = dashboard_data.get("data_json") if dashboard_data else None

    return DashboardCompanyResponse(
        company_id=company_id,
        name=company_data.get("name", ""),
        data=data_json if data_json else None,
    )


@app.get("/settings/{company_id}", response_model=CompanyResponse)
def get_settings(
    company_id: str, supabase: Client = Depends(get_supabase)
) -> CompanyResponse:
    """
    Returns company settings including Shopify credentials.
    Reads from companies table which contains shopify_domain, api_key, access_token.
    """

    result = (
        supabase.table("companies")
        .select("*")
        .eq("id", int(company_id))
        .maybe_single()
        .execute()
    )

    data: Optional[dict] = getattr(result, "data", None)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found.",
        )

    return CompanyResponse(
        id=data.get("id"),
        name=data.get("name", ""),
        shopify_domain=data.get("shopify_domain"),
        api_key=data.get("api_key"),
        access_token=data.get("access_token"),
        created_at=data.get("created_at", ""),
    )


@app.post("/settings/{company_id}", response_model=CompanyResponse)
def update_settings(
    company_id: str,
    payload: SettingsUpdateRequest,
    supabase: Client = Depends(get_supabase),
) -> CompanyResponse:
    """
    Updates Shopify credentials for a company.
    Updates the companies table with shopify_domain, api_key, access_token.
    """

    shopify = payload.shopify

    update_data = {
        "shopify_domain": shopify.shop_domain,
        "api_key": shopify.api_key,
        "access_token": shopify.access_token,
    }

    result = (
        supabase.table("companies")
        .update(update_data)
        .eq("id", int(company_id))
        .select()
        .execute()
    )

    updated_data: Optional[List[dict]] = getattr(result, "data", None)

    if not updated_data or len(updated_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} not found.",
        )

    company = updated_data[0]

    return CompanyResponse(
        id=company.get("id"),
        name=company.get("name", ""),
        shopify_domain=company.get("shopify_domain"),
        api_key=company.get("api_key"),
        access_token=company.get("access_token"),
        created_at=company.get("created_at", ""),
    )


@app.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest, supabase: Client = Depends(get_supabase)
) -> LoginResponse:
    """
    Authenticates user and returns userId and companyId.
    Checks users table for matching email and verifies password using bcrypt.
    """

    # Find user by email
    user_result = (
        supabase.table("users")
        .select("*")
        .eq("email", payload.email)
        .maybe_single()
        .execute()
    )

    user_data: Optional[dict] = getattr(user_result, "data", None)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Get stored password hash
    stored_password_hash = user_data.get("password_hash")

    if not stored_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User account has no password set.",
        )

    # Verify password using bcrypt
    # Handle both bytes and string stored hashes
    if isinstance(stored_password_hash, str):
        stored_password_hash = stored_password_hash.encode("utf-8")

    try:
        password_valid = bcrypt.checkpw(
            payload.password.encode("utf-8"), stored_password_hash
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying password.",
        )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_id = str(user_data.get("id"))
    company_id = str(user_data.get("company_id"))

    return LoginResponse(userId=user_id, companyId=company_id)


@app.post("/auth/signup", response_model=SignupResponse)
def signup(
    payload: SignupRequest, supabase: Client = Depends(get_supabase)
) -> SignupResponse:
    """
    Creates a new user and company.
    First creates company, then creates user linked to that company.
    Uses bcrypt to hash passwords securely.
    """

    # Check if email already exists
    existing_user = (
        supabase.table("users")
        .select("id")
        .eq("email", payload.email)
        .maybe_single()
        .execute()
    )

    if getattr(existing_user, "data", None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    # Hash password using bcrypt
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(payload.password.encode("utf-8"), salt)
    # Store as string (bcrypt hash is safe to store as string)
    password_hash_str = password_hash.decode("utf-8")

    # Create company
    company_result = (
        supabase.table("companies")
        .insert(
            {
                "name": payload.company_name,
                "shopify_domain": None,
                "api_key": None,
                "access_token": None,
            }
        )
        .select()
        .execute()
    )

    company_data: Optional[List[dict]] = getattr(company_result, "data", None)

    if not company_data or len(company_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company.",
        )

    company_id = company_data[0].get("id")

    # Create user linked to company
    try:
        user_result = (
            supabase.table("users")
            .insert(
                {
                    "email": payload.email,
                    "password_hash": password_hash_str,
                    "company_id": company_id,
                }
            )
            .select()
            .execute()
        )

        user_data: Optional[List[dict]] = getattr(user_result, "data", None)

        if not user_data or len(user_data) == 0:
            # Company was created but user creation failed - could clean up company here
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )
    except Exception as e:
        # If user creation fails, try to clean up the company
        try:
            supabase.table("companies").delete().eq("id", company_id).execute()
        except:
            pass  # Best effort cleanup
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )

    user_id = str(user_data[0].get("id"))

    return SignupResponse(userId=user_id, companyId=str(company_id))
