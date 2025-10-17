import streamlit as st
def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.expanded_pdf = None
    st.rerun()

def go_to_login():
    st.query_params.clear()
    st.session_state.page = "login"
    st.session_state.reset_token = None
    st.rerun()