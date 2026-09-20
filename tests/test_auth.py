import sys
import os

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.auth import (
    authenticate_user,
    ROLE_USER,
    ROLE_ADMIN,
    ROLE_GLOBAL_ADMIN,
)


def test_auth_credentials():
    print("[*] Testing Role-Based Authentication & Permissions...")

    # 1. Standard User
    user_res = authenticate_user("nkk_user", "user_password")
    assert user_res is not None, "nkk_user authentication failed"
    assert user_res["role"] == ROLE_USER
    print(f"    [+] nkk_user authenticated: Role={user_res['role']}, Badge={user_res['badge']}")

    # 2. Administrator
    admin_res = authenticate_user("nkk_admin", "admin_passw0rd")
    assert admin_res is not None, "nkk_admin authentication failed"
    assert admin_res["role"] == ROLE_ADMIN
    print(f"    [+] nkk_admin authenticated: Role={admin_res['role']}, Badge={admin_res['badge']}")

    # 3. Global Administrator (strictly nikhil875171)
    owner_res = authenticate_user("nikhil875171", "nikhil_global_admin_2026")
    assert owner_res is not None, "nikhil875171 authentication failed"
    assert owner_res["role"] == ROLE_GLOBAL_ADMIN
    print(f"    [+] nikhil875171 authenticated: Role={owner_res['role']} (STRICT GLOBAL ROOT)")

    # 4. Invalid Password Rejection
    bad_res = authenticate_user("nkk_admin", "wrong_password")
    assert bad_res is None, "Bad password was incorrectly accepted"
    print("    [+] Invalid passwords correctly rejected.")

    # 5. Invalid Username Rejection
    unknown_res = authenticate_user("hacker_user", "some_password")
    assert unknown_res is None, "Unknown user was incorrectly accepted"
    print("    [+] Unknown users correctly rejected.")

    # 6. Verify role hierarchy: only nikhil875171 has GLOBAL_ADMIN
    assert admin_res["role"] != ROLE_GLOBAL_ADMIN, "Admin must NOT have Global Admin rights"
    assert user_res["role"] != ROLE_GLOBAL_ADMIN, "User must NOT have Global Admin rights"
    assert owner_res["role"] == ROLE_GLOBAL_ADMIN, "nikhil875171 must have Global Admin rights"
    print("    [+] Strict role boundary verified: ONLY nikhil875171 holds Global Admin rights!")

    # 7. Test get_all_users and update_user_credentials
    from core.auth import get_all_users, update_user_credentials
    users = get_all_users()
    assert "nikhil875171" in users
    assert "nkk_admin" in users
    assert "nkk_user" in users

    update_user_credentials("test_analyst", "test_pass_123", name="Test Analyst", role=ROLE_USER)
    new_user_res = authenticate_user("test_analyst", "test_pass_123")
    assert new_user_res is not None
    assert new_user_res["name"] == "Test Analyst"
    print("    [+] User credential management verified: dynamic account addition and authentication successful.")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING ALPHASHIELD AUTHENTICATION TEST SUITE")
    print("=" * 60)
    test_auth_credentials()
    print("=" * 60)
    print("ALL AUTH & PERMISSION CHECKS PASSED PERFECTLY!")
    print("=" * 60 + "\n")

