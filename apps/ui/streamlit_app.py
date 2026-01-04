import uuid
import requests
import streamlit as st

from components.otp_modal import otp_modal



API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")
CORRELATION_HEADER = "X-Correlation-ID"


def api_headers() -> dict:
    # Persist correlation id in UI session (one per "user session" in browser)
    if "correlation_id" not in st.session_state:
        st.session_state["correlation_id"] = str(uuid.uuid4())
    return {CORRELATION_HEADER: st.session_state["correlation_id"]}


st.set_page_config(page_title="Grocery Price Compare (MVP)", layout="wide")

st.title("🛒 Grocery Price Comparison (Module 0 Bootstrap)")
st.caption("FastAPI backend + Streamlit UI with correlation ID and structured logs.")

with st.sidebar:
    st.subheader("Diagnostics")
    st.write("API Base:", API_BASE)
    st.write("Correlation ID:", st.session_state.get("correlation_id", "(not set yet)"))
    if st.button("New Correlation ID"):
        st.session_state["correlation_id"] = str(uuid.uuid4())
        st.rerun()

st.divider()

# --- Auth section
st.subheader("1) Platform Login (Mock OTP Flow)")
platform = st.selectbox("Platform", ["jiomart", "bigbasket"], index=0)

colA, colB = st.columns(2)
with colA:
    if st.button("Start Login"):
        r = requests.post(f"{API_BASE}/auth/{platform}/start", headers=api_headers(), timeout=20)
        st.session_state["auth_start_resp"] = r.json()
with colB:
    if st.button("Check Status"):
        r = requests.get(f"{API_BASE}/auth/{platform}/status", headers=api_headers(), timeout=20)
        st.session_state["auth_status_resp"] = r.json()

if "auth_start_resp" in st.session_state:
    st.write("Auth start response:", st.session_state["auth_start_resp"])

# OTP section if needed
resp = st.session_state.get("auth_start_resp")
if resp and resp.get("status") == "OTP_REQUIRED":
    auth_session_id = resp.get("auth_session_id")
    otp = otp_modal(auth_session_id)
    if otp is not None:
        payload = {"auth_session_id": auth_session_id, "otp": otp}
        r = requests.post(f"{API_BASE}/auth/{platform}/submit", json=payload, headers=api_headers(), timeout=20)
        st.success(f"OTP submit result: {r.json()}")

if "auth_status_resp" in st.session_state:
    st.write("Auth status:", st.session_state["auth_status_resp"])

st.divider()

# --- Compare section
st.subheader("2) Compare Prices (Mock Best-Per-Item Split Cart)")
pincode = st.text_input("PIN Code", value="560001")

default_items = [
    {"id": "1", "itemname": "Milk", "brand": "Nandini", "quantity": 1, "unit": "L"},
    {"id": "2", "itemname": "Rice", "brand": "India Gate", "quantity": 5, "unit": "kg"},
    {"id": "3", "itemname": "Sugar", "brand": None, "quantity": 1, "unit": "kg"},
]

items = st.data_editor(default_items, num_rows="dynamic", use_container_width=True)

if st.button("Run Comparison"):
    payload = {"pincode": pincode, "items": items}
    r = requests.post(f"{API_BASE}/compare", json=payload, headers=api_headers(), timeout=30)

    # show correlation id echoed back
    corr_back = r.headers.get(CORRELATION_HEADER)
    st.info(f"Response Correlation ID: {corr_back}")

    data = r.json()
    st.subheader("Result")
    st.json(data)
