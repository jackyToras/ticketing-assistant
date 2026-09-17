"""Streamlit frontend. It communicates with FastAPI only, never with SQLite directly."""

import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Support Decision Assistant", page_icon="🎫", layout="centered")


def api_request(method: str, path: str, *, token: str | None = None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=90, **kwargs)
    except requests.RequestException:
        st.error("Cannot reach the backend. Start FastAPI at http://127.0.0.1:8000 first.")
        return None
    if not response.ok:
        try:
            detail = response.json().get("detail", "Request failed")
        except ValueError:
            detail = "Request failed"
        st.error(detail)
        return None
    return response.json()


def login_or_register():
    st.title("🎫 Support Decision Assistant")
    st.caption("Evidence-backed support recommendations from company policy documents.")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            result = api_request("POST", "/login", json={"email": email, "password": password})
            if result:
                st.session_state.token = result["access_token"]
                st.rerun()

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password (at least 8 characters)", type="password", key="register_password")
            submitted = st.form_submit_button("Create account", use_container_width=True)
        if submitted:
            result = api_request("POST", "/register", json={"email": email, "password": password})
            if result:
                st.success("Account created. You can now log in.")


def decision_view(decision: dict):
    st.subheader(decision["action"].replace("_", " ").title())
    st.metric("Confidence", f"{decision['confidence']:.0%}")
    st.write(decision["reason"])
    st.caption("Policy sources: " + ", ".join(decision["sources"]))


def new_decision(token: str):
    st.header("New decision")
    st.caption("Provide the known order details. Missing details may correctly result in “Needs More Information.”")
    with st.form("ticket_form"):
        message = st.text_area("What happened?", placeholder="My order arrived damaged yesterday.", height=120)
        left, right = st.columns(2)
        with left:
            order_value = st.number_input("Order value (₹)", min_value=0.0, value=None, step=100.0)
            days_delivery = st.number_input("Days since delivery", min_value=0, value=None, step=1)
            product_type = st.selectbox("Product type", ["unknown", "non_food", "food", "mixed"])
        with right:
            days_dispatch = st.number_input("Days since dispatch", min_value=0, value=None, step=1)
            opened_status = st.selectbox("Opened status", ["unknown", "unopened", "opened"])
            order_status = st.selectbox("Order status", ["unknown", "delivered", "dispatched", "not_dispatched"])
        submitted = st.form_submit_button("Get recommendation", type="primary", use_container_width=True)

    if submitted:
        payload = {
            "message": message,
            "order_value_inr": order_value,
            "days_since_delivery": days_delivery,
            "days_since_dispatch": days_dispatch,
            "product_type": product_type,
            "opened_status": opened_status,
            "order_status": order_status,
        }
        with st.spinner("Retrieving policy evidence and generating a decision…"):
            ticket = api_request("POST", "/tickets", token=token, json=payload)
        if ticket:
            st.success("Decision saved to your history.")
            decision_view(ticket["decision"])


def history(token: str):
    st.header("Decision history")
    tickets = api_request("GET", "/tickets", token=token)
    if tickets is None:
        return
    if not tickets:
        st.info("No decisions yet. Create your first ticket from the New decision page.")
        return
    for ticket in tickets:
        with st.expander(f"#{ticket['id']} · {ticket['message'][:80]}"):
            st.caption(f"Created: {ticket['created_at']}")
            if ticket["decision"]:
                decision_view(ticket["decision"])


def app():
    token = st.session_state.get("token")
    if not token:
        login_or_register()
        return

    user = api_request("GET", "/me", token=token)
    if not user:
        st.session_state.pop("token", None)
        return
    with st.sidebar:
        st.write(f"Signed in as `{user['email']}`")
        page = st.radio("Menu", ["New decision", "History"])
        if st.button("Log out", use_container_width=True):
            st.session_state.pop("token", None)
            st.rerun()

    if page == "New decision":
        new_decision(token)
    else:
        history(token)


app()
