import os
import streamlit as st
from typing import Optional, Tuple

# Role definitions
ROLE_USER = "USER"
ROLE_ADMIN = "ADMIN"
ROLE_GLOBAL_ADMIN = "GLOBAL_ADMIN"

# Credential Store
USER_REGISTRY = {
    "nkk_user": {
        "password": "user_password",
        "role": ROLE_USER,
        "name": "NKK Analyst",
        "badge": "👤 Standard Analyst",
    },
    "nkk_admin": {
        "password": "admin_passw0rd",
        "role": ROLE_ADMIN,
        "name": "NKK System Admin",
        "badge": "🛡️ Administrator",
    },
    "nikhil875171": {
        "password": os.getenv("GLOBAL_ADMIN_PASSWORD", "nikhil_global_admin_2026"),
        "role": ROLE_GLOBAL_ADMIN,
        "name": "Nikhil Kumar (Owner)",
        "badge": "👑 Global Administrator",
    },
}

GLOBAL_ADMIN_GITHUB_USER = "nikhil875171"
GLOBAL_ADMIN_EMAILS = {"nikhil875171@gmail.com", "nikhilkumar@users.noreply.github.com"}


def _check_streamlit_cloud_github_user() -> Optional[Tuple[str, str, str]]:
    """Detects if running on Streamlit Cloud and authenticated via GitHub."""
    try:
        if hasattr(st, "experimental_user"):
            user = st.experimental_user
            email = getattr(user, "email", "") or ""
            if email and (email in GLOBAL_ADMIN_EMAILS or "nikhil875171" in email):
                return "nikhil875171", "Nikhil Kumar (GitHub)", ROLE_GLOBAL_ADMIN
        if hasattr(st, "user"):
            user = st.user
            email = getattr(user, "email", "") or ""
            if email and (email in GLOBAL_ADMIN_EMAILS or "nikhil875171" in email):
                return "nikhil875171", "Nikhil Kumar (GitHub)", ROLE_GLOBAL_ADMIN
    except Exception:
        pass
    return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Validates user credentials and returns user metadata dict if valid."""
    cleaned_user = username.strip().lower()

    # Check registry
    for reg_user, data in USER_REGISTRY.items():
        if reg_user.lower() == cleaned_user and data["password"] == password:
            return {
                "username": reg_user,
                "name": data["name"],
                "role": data["role"],
                "badge": data["badge"],
            }
    return None


def init_session_state():
    """Initializes authentication keys in st.session_state."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["user_role"] = None
        st.session_state["display_name"] = None
        st.session_state["user_badge"] = None

    # Auto-detect GitHub Global Admin on Streamlit Cloud
    if not st.session_state["authenticated"]:
        gh_auth = _check_streamlit_cloud_github_user()
        if gh_auth:
            uname, name, role = gh_auth
            st.session_state["authenticated"] = True
            st.session_state["username"] = uname
            st.session_state["display_name"] = name
            st.session_state["user_role"] = role
            st.session_state["user_badge"] = "👑 Global Administrator"


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    """True if user is either ADMIN or GLOBAL_ADMIN."""
    role = st.session_state.get("user_role")
    return role in [ROLE_ADMIN, ROLE_GLOBAL_ADMIN]


def is_global_admin() -> bool:
    """True ONLY for nikhil875171 (Global Administrator)."""
    return st.session_state.get("user_role") == ROLE_GLOBAL_ADMIN


def logout():
    """Clears current session authentication."""
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["user_role"] = None
    st.session_state["display_name"] = None
    st.session_state["user_badge"] = None
    st.rerun()


def render_login_gate():
    """Renders high-security institutional login modal."""
    init_session_state()

    if is_authenticated():
        return True

    # Center-aligned login container
    col_l, col_center, col_r = st.columns([1, 1.8, 1])

    with col_center:
        st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
        st.markdown("## 🛡️ **AlphaShield Gate**")
        st.markdown("<p style='color: #94A3B8;'>Institutional Market Intelligence & Capital Preservation</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("alphashield_login_form"):
            st.markdown("##### 🔐 **Authorized Personnel Sign In**")
            input_user = st.text_input("Username / ID", placeholder="e.g. nkk_user, nkk_admin, nikhil875171").strip()
            input_pass = st.text_input("Security Passphrase", type="password", placeholder="••••••••••••")
            submit_btn = st.form_submit_button("Unlock Dashboard", use_container_width=True, type="primary")

            if submit_btn:
                if not input_user or not input_pass:
                    st.error("Please enter both username and password.")
                else:
                    user_data = authenticate_user(input_user, input_pass)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_data["username"]
                        st.session_state["display_name"] = user_data["name"]
                        st.session_state["user_role"] = user_data["role"]
                        st.session_state["user_badge"] = user_data["badge"]
                        st.success(f"Access granted: Welcome, {user_data['name']}!")
                        st.rerun()
                    else:
                        st.error("Authentication failed: Invalid credentials.")

        st.markdown("""
        <div style='background-color: #151B26; padding: 14px; border-radius: 8px; border: 1px solid #232D3F; margin-top: 15px;'>
            <p style='color: #64748B; font-size: 0.8rem; margin: 0; text-align: center;'>
                🔒 <strong>Restricted Institutional Access</strong><br/>
                All queries and algorithmic suggestions are logged for risk governance.
            </p>
        </div>
        """, unsafe_allow_html=True)

    return False


def render_user_profile_sidebar():
    """Renders profile badge and logout button in sidebar."""
    if not is_authenticated():
        return

    st.sidebar.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown(f"**User:** `{st.session_state.get('display_name', 'Analyst')}`")
    st.sidebar.markdown(f"**Role:** {st.session_state.get('user_badge', '👤 User')}")

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        logout()
    st.sidebar.markdown("---")
