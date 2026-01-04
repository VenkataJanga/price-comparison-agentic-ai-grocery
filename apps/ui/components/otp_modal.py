import streamlit as st


def otp_modal(auth_session_id: str) -> str | None:
    """
    Simple OTP input section. Streamlit doesn't have a native modal without extra libs,
    so we render a dedicated section.
    Returns OTP string if user submits, else None.
    """
    st.info("OTP required. Enter the OTP you received.")
    otp = st.text_input("OTP", type="password", placeholder="Enter OTP", key=f"otp_{auth_session_id}")
    if st.button("Submit OTP", key=f"submit_otp_{auth_session_id}"):
        return otp
    return None
