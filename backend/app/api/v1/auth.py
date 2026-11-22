from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import re
import secrets
import time
import uuid

from app.core.db import get_db
from app.models.user import User
from app.models.account import Account
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_google_id_token
)
from app.services.firebase_service import verify_firebase_id_token
from app.deps.auth import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_CACHE: Dict[str, Dict[str, Any]] = {}

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    google_id: Optional[str] = None
    id_token: Optional[str] = None

class PhoneAuthRequest(BaseModel):
    id_token: Optional[str] = None
    idToken: Optional[str] = None
    full_name: Optional[str] = None

class SendOtpRequest(BaseModel):
    phone: str
    full_name: Optional[str] = None

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    is_demo: bool = False

@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register_user(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()

    # Block registration for demo account
    if clean_email == "arun.sharma@example.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo account arun.sharma@example.com cannot be registered. Use 'Explore sample data' to view demo mode."
        )

    if not clean_email or not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )

    # Password complexity check (minimum 8 characters)
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        if existing_user.password_hash == "GOOGLE_OAUTH_VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email was registered using Google Sign-In. Please sign in with Google."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    # Create user with bcrypt password hash
    new_user = User(
        email=clean_email,
        full_name=req.full_name.strip(),
        password_hash=hash_password(req.password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default primary savings account
    primary_account = Account(
        user_id=new_user.id,
        account_type="SAVINGS",
        bank_name="Primary Bank",
        account_mask="**1001",
        currency="INR",
        virtual_balance=50000.0
    )
    db.add(primary_account)
    db.commit()

    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_demo=False
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login_user(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()

    # Block direct password login for demo account
    if clean_email == "arun.sharma@example.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct login for demo user arun.sharma@example.com is blocked. Please click 'Explore sample data' to view the demo."
        )

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password.")

    if user.password_hash == "GOOGLE_OAUTH_VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was registered with Google Sign-In. Please sign in with Google."
        )

    if not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password.")
    
    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=False
    )

@router.post("/otp/send")
@limiter.limit("3/minute")
def send_otp(request: Request, req: SendOtpRequest):
    clean_digits = re.sub(r"\D", "", req.phone)
    if len(clean_digits) < 10:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")
    
    phone_10 = clean_digits[-10:]
    fast2sms_key = os.getenv("FAST2SMS_API_KEY")
    if not fast2sms_key:
        raise HTTPException(status_code=503, detail="Phone verification is not configured. Please use another sign-in method.")

    otp_code = str(secrets.randbelow(900000) + 100000)
    expires_at = time.time() + 300  # 5 minutes

    import requests
    try:
        sms_res = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": fast2sms_key},
            json={
                "route": "otp",
                "variables_values": otp_code,
                "numbers": phone_10
            },
            timeout=5
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Unable to send verification code. Please try again.") from exc
    if sms_res.status_code != 200:
        raise HTTPException(status_code=502, detail="Unable to send verification code. Please try again.")

    OTP_CACHE[phone_10] = {
        "otp": otp_code,
        "expires_at": expires_at,
        "full_name": (req.full_name or "").strip(),
        "attempts": 0
    }

    return {
        "success": True,
        "phone": f"+91 {phone_10}",
        "message": f"Verification code sent to +91 {phone_10}",
        "expires_in": 300
    }

@router.post("/otp/verify", response_model=TokenResponse)
@limiter.limit("5/minute")
def verify_otp(request: Request, req: VerifyOtpRequest, db: Session = Depends(get_db)):
    clean_digits = re.sub(r"\D", "", req.phone)
    phone_10 = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
    
    record = OTP_CACHE.get(phone_10)
    if not record:
        raise HTTPException(status_code=400, detail="No active verification code found for this mobile number.")
    
    if time.time() > record["expires_at"]:
        if phone_10 in OTP_CACHE:
            del OTP_CACHE[phone_10]
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new code.")
    
    record["attempts"] = record.get("attempts", 0) + 1
    valid_code = secrets.compare_digest(record["otp"], req.otp.strip())
    if not valid_code:
        remaining = max(0, 3 - record["attempts"])
        if record["attempts"] >= 3:
            del OTP_CACHE[phone_10]
            raise HTTPException(status_code=400, detail="Too many failed attempts. This verification code has been invalidated. Please request a new code.")
        raise HTTPException(status_code=400, detail=f"Invalid verification code. {remaining} attempt(s) remaining.")
    
    if phone_10 in OTP_CACHE:
        del OTP_CACHE[phone_10]
        
    phone_email = f"{phone_10}@phone.mandateradar.in"
    user = db.query(User).filter(User.email == phone_email).first()
    
    user_name = (req.full_name or "").strip()
    if record and record.get("full_name"):
        user_name = user_name or record["full_name"]
    if not user_name:
        user_name = f"User +91 {phone_10[-4:]}"
        
    if not user:
        user = User(
            email=phone_email,
            phone=f"+91{phone_10}",
            full_name=user_name,
            password_hash="OTP_VERIFIED",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        account = Account(
            user_id=user.id,
            account_type="SAVINGS",
            bank_name="Primary Bank",
            account_mask=f"**{phone_10[-4:]}",
            currency="INR",
            virtual_balance=25000.0
        )
        db.add(account)
        db.commit()
        
    token = create_access_token({"sub": user.id, "email": user.email, "full_name": user.full_name})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=False
    )

@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticates user using Google ID token credential.
    Verifies token with Google OAuth, strictly requiring email_verified == True.
    Identity (email and name) is extracted ONLY from verified claims.
    Rejects raw email/name submissions with 401.
    """
    token_str = req.credential or req.id_token
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google ID token credential is required. Raw email or unverified identity is rejected."
        )

    id_info = verify_google_id_token(token_str)
    if not id_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed: invalid or expired token credential."
        )

    if not id_info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified."
        )

    clean_email = str(id_info.get("email", "")).strip().lower()
    if not clean_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google profile: missing verified email claim."
        )

    # Block demo email login via Google
    if clean_email == "arun.sharma@example.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo account arun.sharma@example.com is reserved. Please use 'Explore sample data' to view demo mode."
        )

    display_name = str(id_info.get("name") or id_info.get("given_name") or clean_email.split("@")[0].title()).strip()

    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        user_id_val = "user_primary" if clean_email == "arun.sharma@example.com" else f"usr_{uuid.uuid4().hex[:12]}"
        user = User(
            id=user_id_val,
            email=clean_email,
            full_name=display_name,
            password_hash="GOOGLE_OAUTH_VERIFIED",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(
            user_id=user.id,
            account_type="SAVINGS",
            bank_name="Primary Bank",
            account_mask="**0000",
            currency="INR",
            virtual_balance=50000.0
        )
        db.add(account)
        db.commit()

    token = create_access_token({"sub": user.id, "email": user.email, "full_name": user.full_name})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=False
    )

@router.post("/phone", response_model=TokenResponse)
def phone_auth(req: PhoneAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticates user using verified Firebase Phone Auth ID token.
    Extracts phone_number from verified claims. Never trusts client phone input.
    """
    token_str = req.id_token or req.idToken
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token is required for phone verification."
        )

    try:
        decoded_claims = verify_firebase_id_token(token_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Firebase phone verification failed: Invalid or expired token ({str(e)})"
        )

    phone_number = decoded_claims.get("phone_number")
    if not phone_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token does not contain a verified phone_number claim."
        )

    clean_digits = re.sub(r"\D", "", phone_number)
    phone_10 = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits

    phone_email = f"{phone_10}@phone.mandateradar.in"
    user = db.query(User).filter((User.phone == phone_number) | (User.email == phone_email)).first()

    display_name = (req.full_name or "").strip()
    if not display_name:
        display_name = f"User +91 {phone_10[-4:]}"

    if not user:
        user = User(
            email=phone_email,
            phone=phone_number,
            full_name=display_name,
            password_hash="FIREBASE_PHONE_VERIFIED",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        account = Account(
            user_id=user.id,
            account_type="SAVINGS",
            bank_name="Primary Bank",
            account_mask=f"**{phone_10[-4:]}",
            currency="INR",
            virtual_balance=25000.0
        )
        db.add(account)
        db.commit()
    else:
        if not user.phone:
            user.phone = phone_number
            db.commit()

    token = create_access_token({"sub": user.id, "email": user.email, "full_name": user.full_name})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_demo=False
    )

@router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    }
