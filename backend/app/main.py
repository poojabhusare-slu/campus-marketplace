import logging

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.security import hash_password
from app.db import engine
from app.schemas.auth import RegisterRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("campus_marketplace")

app = FastAPI(title="Campus Marketplace API")


@app.post("/auth/register", status_code=201)
def register_user(user: RegisterRequest):
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    INSERT INTO users (email, password_hash, name, role)
                    VALUES (:email, :password_hash, :name, :role)
                    """
                ),
                {
                    "email": str(user.email).lower(),
                    "password_hash": hash_password(user.password),
                    "name": user.name,
                    "role": user.role,
                },
            )
            user_id = result.lastrowid
    except IntegrityError as exc:
        logger.warning("Registration rejected: duplicate email")
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        ) from exc
    except SQLAlchemyError as exc:
        logger.exception("Registration failed because of a database error")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    logger.info("User registered: user_id=%s role=%s", user_id, user.role)
    return {"user_id": user_id}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "database connected"}
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc
