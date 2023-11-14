import streamlit as st
import pandas as pd
import pathlib
import numpy as np


path = pathlib.Path(__file__).parent.absolute()
DATA_PATH = path / "data/processed/combined_data.csv"

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("data.csv", parse_dates=["year_start"])
    # replace any '*" in usage column with np.nan
    df["Usage"] = df["Usage"].replace("*", np.nan)
    return df


data = st.cache_data(pd.read_csv)(
    DATA_PATH, parse_dates=["year_start"]
).reset_index(drop=True)

data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

st.sidebar.title("Code Input")
st.sidebar.write("Enter a SNOMED-CT code to see the counts for that code.")
code_input = st.sidebar.text_input("Enter a code")