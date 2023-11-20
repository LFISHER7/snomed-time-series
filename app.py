import pathlib
import pyautogui
import streamlit as st
import pandas as pd
import numpy as np

from src.utils import (
    load_data,
    plot_time_series,
    get_codes_from_url,
    show_plots,
    select_column,
)

path = pathlib.Path(__file__).parent.absolute()
DATA_PATH = path / "data/processed/combined_data.csv"


def handle_code_input(data):
    st.sidebar.title("Code Input")
    st.sidebar.write("Enter a SNOMED-CT code to see the counts for that code.")
    code_input = st.sidebar.text_input("Enter a code")

    if code_input:
        filtered_data = data[data["SNOMED_Concept_ID"] == code_input]

        if not filtered_data.empty:
            st.title(f"Counts for Code: {code_input}")
            # dislpay the data, year start should be in the format YYYY-MM-DD
            formatted_data = filtered_data[["year_start", "Usage"]]
            formatted_data.columns = ["Year", "Usage"]
            formatted_data.loc[:, "Year"] = formatted_data["Year"].dt.strftime(
                "%Y-%m-%d"
            )
            formatted_data = formatted_data.set_index("Year")

            st.write("Time Series Graph")
            st.pyplot(plot_time_series(filtered_data))

        else:
            st.error(
                f"The code {code_input} was not found. Please ensure the code entered is a SNOMED-CT code."
            )


def display_code_data(filtered_data, code_input):
    st.title(f"Counts for Code: {code_input}")
    formatted_data = filtered_data[["year_start", "Usage"]]
    formatted_data.columns = ["Year", "Usage"]
    formatted_data["Year"] = formatted_data["Year"].dt.strftime("%Y-%m-%d")
    st.write(formatted_data.set_index("Year"))
    st.write("Time Series Graph")
    st.pyplot(plot_time_series(filtered_data))


def handle_file_upload(data):
    st.sidebar.title("Upload a Code List")
    st.sidebar.write('Upload a CSV file with a column named "SNOMED_Concept_ID"')
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        code_list = pd.read_csv(uploaded_file)

        column_name = select_column(code_list, "select_column_file_upload")

        data = data.rename(columns={"SNOMED_Concept_ID": column_name})

        if st.sidebar.button("Analyse Code List"):
            show_plots(code_list, data, column_name)


def handle_url_input(data):
    st.sidebar.title("Fetch Codes from OpenCodelists")
    url_input = st.sidebar.text_input("Enter a URL")
    st.sidebar.write(
        "Enter a URL from https://www.opencodelists.org/ and the codes will be fetched. e.g. https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/cpeptide_cod/20200812"
    )

    if url_input:
        codes_df = get_codes_from_url(url_input)

        column_name = select_column(codes_df, "select_column_url")

        if st.sidebar.button("Analyse Code List from URL"):
            codes = codes_df[column_name].unique().tolist()
            if codes:
                code_list = pd.DataFrame(codes, columns=["SNOMED_Concept_ID"])
                code_list["SNOMED_Concept_ID"] = code_list["SNOMED_Concept_ID"].astype(
                    str
                )

                data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

                data["Usage"] = data["Usage"].replace("*", np.nan)
                data["Usage"] = data["Usage"].astype(float)

                show_plots(code_list, data, "SNOMED_Concept_ID")


def main():
    if st.sidebar.button("Reset"):
        pyautogui.hotkey("ctrl", "F5")

    st.title("SNOMED-CT Explorer")

    data = load_data(DATA_PATH)
    data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

    handle_code_input(data)
    handle_file_upload(data)
    handle_url_input(data)


if __name__ == "__main__":
    main()