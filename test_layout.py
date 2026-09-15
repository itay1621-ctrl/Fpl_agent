import streamlit as st

st.markdown("""
<style>
@media (max-width: 600px) {
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.3rem !important;
    }
    div[data-testid="column"] {
        padding: 0 !important;
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)

cols = st.columns(4)
for i, col in enumerate(cols):
    with col:
        st.markdown(f'<div style="background: red; text-align: center;">Col {i}</div>', unsafe_allow_html=True)
