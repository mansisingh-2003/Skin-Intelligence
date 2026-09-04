# ============================================================
# SKIN INTELLIGENCE
# DEMO USER CREATION SCRIPT
# ============================================================

from database import SessionLocal, engine, Base
from models.user import User
from security import hash_password


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# DEMO USERS
# ============================================================

DEMO_USERS = [
    {
        "name": "Demo User",
        "email": "user@skinintelligence.com",
        "password": "User@12345",
        "role": "user",
        "age": 22,
        "gender": "Other",
    },

    {
        "name": "Demo Consultant",
        "email": "consultant@skinintelligence.com",
        "password": "Consultant@12345",
        "role": "consultant",
        "age": 30,
        "gender": "Other",
    },

    {
        "name": "Demo Dermatologist",
        "email": "dermatologist@skinintelligence.com",
        "password": "Dermatologist@12345",
        "role": "dermatologist",
        "age": 35,
        "gender": "Other",
    },

    {
        "name": "System Administrator",
        "email": "admin@skinintelligence.com",
        "password": "Admin@12345",
        "role": "admin",
        "age": 30,
        "gender": "Other",
    },
]


# ============================================================
# CREATE / UPDATE DEMO USERS
# ============================================================

def create_demo_users():

    db = SessionLocal()

    try:

        print()
        print("=" * 60)
        print("SKIN INTELLIGENCE - DEMO USER SETUP")
        print("=" * 60)
        print()

        for user_data in DEMO_USERS:

            email = (
                user_data["email"]
                .strip()
                .lower()
            )

            # ------------------------------------------------
            # Check whether user already exists
            # ------------------------------------------------

            existing_user = (
                db.query(User)
                .filter(
                    User.email == email
                )
                .first()
            )

            # ------------------------------------------------
            # Update existing user
            # ------------------------------------------------

            if existing_user:

                existing_user.name = (
                    user_data["name"]
                )

                existing_user.password_hash = (
                    hash_password(
                        user_data["password"]
                    )
                )

                existing_user.role = (
                    user_data["role"]
                )

                existing_user.is_active = True

                existing_user.age = (
                    user_data["age"]
                )

                existing_user.gender = (
                    user_data["gender"]
                )

                print(
                    f"UPDATED: {email}"
                )

            # ------------------------------------------------
            # Create new user
            # ------------------------------------------------

            else:

                new_user = User(
                    name=user_data["name"],
                    email=email,
                    password_hash=hash_password(
                        user_data["password"]
                    ),
                    role=user_data["role"],
                    is_active=True,
                    age=user_data["age"],
                    gender=user_data["gender"],
                )

                db.add(
                    new_user
                )

                print(
                    f"CREATED: {email}"
                )

        # ----------------------------------------------------
        # Save database changes
        # ----------------------------------------------------

        db.commit()

        print()
        print("=" * 60)
        print("DEMO USERS READY")
        print("=" * 60)
        print()

        print(
            "User:          "
            "user@skinintelligence.com"
        )

        print(
            "Consultant:    "
            "consultant@skinintelligence.com"
        )

        print(
            "Dermatologist: "
            "dermatologist@skinintelligence.com"
        )

        print(
            "Admin:         "
            "admin@skinintelligence.com"
        )

        print()
        print(
            "All demo accounts are active."
        )
        print()

    except Exception as error:

        db.rollback()

        print()
        print("=" * 60)
        print("ERROR CREATING DEMO USERS")
        print("=" * 60)
        print()
        print(error)
        print()

        raise

    finally:

        db.close()


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":

    create_demo_users()