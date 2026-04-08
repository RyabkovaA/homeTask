from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, decode_token
from app.models.user import User
from app.models.member import HouseMember
from app.schemas.user import UserOut, TokenOut
from pydantic import BaseModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class RegisterPayload(BaseModel):
    email: str
    name: str
    password: str


@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterPayload, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserOut)
async def me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    return await get_current_user(token, db)


class MemberInfo(BaseModel):
    house_id: str
    member_id: str


@router.get("/auth/member", response_model=MemberInfo)
async def get_member_info(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Returns current user's first house membership info."""
    member = await get_current_member(token, db)
    return MemberInfo(house_id=str(member.house_id), member_id=str(member.id))


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401)
    return user


async def get_current_member(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> HouseMember:
    """Returns first HouseMember of current user (MVP: single house)."""
    user = await get_current_user(token, db)
    result = await db.execute(
        select(HouseMember).where(HouseMember.user_id == user.id).limit(1)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(403, "Not a member of any house")
    return member
