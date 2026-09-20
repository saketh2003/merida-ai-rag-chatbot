import sys
import argparse
from app.database import SessionLocal, engine, Base
from app.models import User
from app.security import hash_password
from app.config import settings

def seed_admin(email: str, password: str, full_name: str):
    """Seed or promote an admin user in the database."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = "admin"
            user.hashed_password = hash_password(password)
            if full_name:
                user.full_name = full_name
            db.commit()
            print(f"✅ User '{email}' was updated to Admin role successfully.")
        else:
            admin_user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name or "System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Admin user '{email}' created successfully.")
    except Exception as e:
        print(f"❌ Error seeding admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial admin user into chatbot database.")
    parser.add_argument("--email", type=str, default=settings.INITIAL_ADMIN_EMAIL, help="Admin email address")
    parser.add_argument("--password", type=str, default=settings.INITIAL_ADMIN_PASSWORD, help="Admin password")
    parser.add_argument("--name", type=str, default=settings.INITIAL_ADMIN_NAME, help="Admin full name")

    args = parser.parse_args()
    seed_admin(args.email, args.password, args.name)
