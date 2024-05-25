import pathlib
import streamlit as st
import pandas as pd
import numpy as np

from src.utils import (
    load_data,
    plot_time_series,
    get_codes_from_url,
    show_plots,
    select_columns,
    show_download_button,
)

path = pathlib.Path(__file__).resolve().parents[1]
DATA_PATH = path / "data/processed/combined_data.csv"


def handle_code_input(data):
    st.sidebar.title("Code Input")
    st.sidebar.write("Enter a SNOMED CT code to see the counts for that code.")

    code_input = st.sidebar.text_input("Enter a code", key="code_input")

    if code_input:
        filtered_data = data[data["SNOMED_Concept_ID"] == code_input]
        if not filtered_data.empty:
            code_description = filtered_data["Description"].values[0]

            st.title(f"Counts for Code: {code_input}")
            st.write(f"Code Description: {code_description}")

            filtered_data["year_start"] = pd.to_datetime(
                filtered_data["year_start"]
            ).dt.date

            filtered_data["Year"] = pd.to_datetime(
                filtered_data["year_start"]
            ) - pd.DateOffset(months=6)

            filtered_data = filtered_data.loc[:, ["Year", "Usage"]]

            formatted_data = filtered_data.copy()
            formatted_data["Year"] = formatted_data["Year"].astype(str)

            formatted_data = formatted_data.set_index("Year")

            st.write(formatted_data)
            st.pyplot(plot_time_series(filtered_data))

            show_download_button(formatted_data.reset_index().to_csv(index=False).encode('utf-8'), f"snomed_code_usage_{code_input}.csv", f"download_csv_{code_input}")

        else:
            st.error(
                f"The code {code_input} was not found. Please ensure the code entered is a SNOMED CT code."
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
    uploaded_file = st.sidebar.file_uploader(
        "Choose a CSV file", type="csv", key="uploaded_file"
    )

    if uploaded_file is not None:
        code_list = pd.read_csv(uploaded_file)

        columns = {
            "column": "file_upload_code_column",
            "description": "file_upload_description_column",
        }

        column_names = select_columns(code_list, columns)

        data = data.rename(columns={"SNOMED_Concept_ID": column_names["column_name"]})

        if st.sidebar.button("Analyse Code List"):

            code_list[column_names["column_name"]] = code_list[
                column_names["column_name"]
            ].astype(str)
            if column_names["description_column_name"]:
                code_list[column_names["description_column_name"]] = code_list[
                    column_names["description_column_name"]
                ].astype(str)

            data_subset = data[
                data[column_names["column_name"]].isin(
                    code_list[column_names["column_name"]]
                )
            ]

            show_plots(
                code_list,
                column_names["description_column_name"],
                data_subset,
                column_names["column_name"],
            )


def handle_url_input(data):
    st.sidebar.title("Fetch Codes from OpenCodelists")
    url_input = st.sidebar.text_input("Enter a URL", key="url_input")
    st.sidebar.write(
        "Enter a URL from https://www.opencodelists.org/ and the codes will be fetched. e.g. https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/cpeptide_cod/20200812"
    )

    if url_input:
        codes_df = get_codes_from_url(url_input)

        columns = {"column": "url_code_column", "description": "url_description_column"}

        column_names = select_columns(codes_df, columns)
        column_name = column_names["column_name"]
        description_column_name = column_names["description_column_name"]

        if st.sidebar.button("Analyse Code List from URL"):
            codes = codes_df[column_name].unique().tolist()

            if codes:
                code_list = pd.DataFrame(codes, columns=[column_name])

                if description_column_name:
                    code_list = code_list.merge(
                        codes_df[[column_name, description_column_name]],
                        on=column_name,
                        how="left",
                    )

                code_list = code_list.rename(columns={column_name: "SNOMED_Concept_ID"})

                code_list["SNOMED_Concept_ID"] = code_list["SNOMED_Concept_ID"].astype(
                    str
                )

                data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

                data["Usage"] = data["Usage"].replace("*", np.nan)
                data["Usage"] = data["Usage"].astype(float)

                if description_column_name:
                    code_list[description_column_name] = code_list[
                        description_column_name
                    ].astype(str)

                data_subset = data[
                    data["SNOMED_Concept_ID"].isin(code_list["SNOMED_Concept_ID"])
                ]

                csv = data_subset.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name=f"snomed_code_usage.csv",
                    mime="text/csv",
                    key=f"download_csv_url",
                )

                show_plots(
                    code_list, description_column_name, data_subset, "SNOMED_Concept_ID"
                )


def main():

    st.set_page_config(
    page_title="Analyse",
    page_icon="📈",
)

    if st.sidebar.button("Reset"):
        st.session_state["code_input"] = ""
        st.session_state["url_input"] = ""
        st.rerun()

    st.title("Analyse")

    with st.expander(expanded=True, label="How to use"):
        
        st.markdown(
            """
            Use one of the 3 options in the sidebar for exploring this data:

            1. **Entering a single code** - Explore usage over time for a single code.
            2. **Uploading a codelist** - Explore usage over time for a list of codes in a local [codelist](https://www.bennett.ox.ac.uk/blog/2023/09/what-are-codelists-and-how-are-they-constructed/).
            3. **Finding a codelist on OpenCodelists** - Explore usage over time for a list of codes on [OpenCodelists](https://opencodelists.org/).
            
            """
        )
    
    

    data = load_data(DATA_PATH)
    data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

    handle_code_input(data)
    handle_file_upload(data)
    handle_url_input(data)


if __name__ == "__main__":
    main()
