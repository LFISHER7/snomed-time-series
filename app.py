import streamlit as st
import pandas as pd
import pathlib
import pyautogui
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

path = pathlib.Path(__file__).parent.absolute()
DATA_PATH = path / "data/processed/combined_data.csv"


if st.sidebar.button("Reset"):
    pyautogui.hotkey("ctrl", "F5")


@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["year_start"] = pd.to_datetime(df["year_start"], format="%Y-%m-%d")
    # replace any '*" in usage column with np.nan
    df["Usage"] = df["Usage"].replace("*", np.nan)
    df["Usage"] = df["Usage"].astype(float)
    return df


data = load_data()

data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

st.sidebar.title("Code Input")
st.sidebar.write("Enter a SNOMED-CT code to see the counts for that code.")
code_input = st.sidebar.text_input("Enter a code")


def plot_time_series(data):
    data.loc[:, "year_start"] = data["year_start"] - pd.DateOffset(months=6)

    xlabels = data["year_start"].dt.strftime("%Y").unique().tolist()
    plt.figure(figsize=(10, 5))
    plt.bar(
        data["year_start"],
        data["Usage"],
        width=365,
        color="blue",
        alpha=0.5,
        edgecolor="black",
        linewidth=0.5,
    )
    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.xlabel("Date", fontsize=14)
    plt.ylabel("Usage", fontsize=14)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.xticks(xlabels, fontsize=12, rotation=45)
    plt.yticks(fontsize=12)
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.margins(0, 0)
    plt.savefig("plot.png", bbox_inches="tight")

    return plt


if code_input:
    filtered_data = data[data["SNOMED_Concept_ID"] == code_input]

    if not filtered_data.empty:
        st.title(f"Counts for Code: {code_input}")
        # dislpay the data, year start should be in the format YYYY-MM-DD
        formatted_data = filtered_data[["year_start", "Usage"]]
        formatted_data.columns = ["Year", "Usage"]
        formatted_data.loc[:, "Year"] = formatted_data["Year"].dt.strftime("%Y-%m-%d")
        formatted_data = formatted_data.set_index("Year")
        st.write(formatted_data)

        st.write("Time Series Graph")
        st.pyplot(plot_time_series(filtered_data))

    else:
        st.error(
            f"The code {code_input} was not found. Please ensure the code entered is a SNOMED-CT code."
        )
