import pandas as pd
import streamlit as st

@st.cache_data
def load_data(path="data/clean/dataset.csv"):
    return pd.read_csv(path)