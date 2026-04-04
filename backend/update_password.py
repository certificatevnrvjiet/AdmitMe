from database import supabase
import bcrypt

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def update_all_passwords():
    # Fetch all users
    response = supabase.table("users").select("*").execute()

    if not response.data:
        print("No users found.")
        return

    users = response.data
    print(f"Found {len(users)} users. Updating passwords...")

    for user in users:
        user_id = user.get("id")
        plain_password = user.get("password")

        if not plain_password:
            print(f"Skipping user {user_id} (no password found)")
            continue

        # Hash password
        hashed_password = hash_password(plain_password)

        # Update user record
        update_response = (
            supabase.table("users")
            .update({"password": hashed_password})
            .eq("id", user_id)
            .execute()
        )

        if update_response.data:
            print(f"Updated password for user ID {user_id}")
        else:
            print(f"Failed to update user ID {user_id}")

if __name__ == "__main__":
    update_all_passwords()
