"""Preparo mi usuario administrador mediante variables de entorno."""
import asyncio
import os
from sqlalchemy import select
from app.database import async_session_factory
from app.models import User
from app.security import hash_password

async def main():
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise ValueError("Configuro SEED_ADMIN_PASSWORD con al menos 12 caracteres")
    username = os.environ.get("SEED_ADMIN_USERNAME", "admin")
    email = os.environ.get("SEED_ADMIN_EMAIL", "admin@example.com")
    async with async_session_factory() as db:
        if await db.scalar(select(User.id).where(User.username == username)):
            raise ValueError("El administrador ya existe; no modifico su contraseña")
        db.add(User(username=username,email=email,role="admin",hashed_password=hash_password(password)))
        await db.commit()
    print("Creé mi administrador")

if __name__ == "__main__":
    asyncio.run(main())
