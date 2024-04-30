import requests
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
from bs4 import BeautifulSoup


def load_data(path):
    """
    Load and preprocess CSV from a given path.

    Args:
        path (str): The file path to the CSV data.

    Returns:
        DataFrame: Preprocessed pandas DataFrame.
    """
    df = pd.read_csv(path)
    df["year_start"] = pd.to_datetime(df["year_start"], format="%Y-%m-%d")
    df["Usage"] = df["Usage"].replace("*", np.nan).astype(float)
    return df


def plot_time_series(data):
    """
    Generate a time series plot from the given data.

    Args:
        data (DataFrame): Data containing 'year_start' and 'Usage' columns.

    Returns:
        Matplotlib figure: The generated time series plot.
    """
    data_copy = data.copy()
    data_copy["year_start"] = pd.to_datetime(data_copy["year_start"]) - pd.DateOffset(
        months=6
    )
    xlabels = data_copy["year_start"].dt.strftime("%Y").unique().tolist()
    plt.figure(figsize=(10, 5))
    plt.bar(
        data_copy["year_start"],
        data_copy["Usage"],
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
    return plt


def get_codes_from_url(url):
    """
    Fetch codes from an OpenCodelists URL.

    Args:
        url (str): URL to fetch codes from. Must be in the form https://www.opencodelists.org/codelist/{org}/{codelist}/{version}

    Returns:
        DataFrame: DataFrame containing the codes, or an empty DataFrame if an error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        coding_system_sec = soup.find(
            "dt", string=lambda text: "Coding system" in (text or "")
        )
        coding_system = coding_system_sec.find_next_sibling("dd").text

        if coding_system != "SNOMED CT":
            st.error(
                "The coding system for this codelist is not SNOMED-CT. Please check the URL and try again."
            )
            return pd.DataFrame()

        download_link = soup.find(
            "a", string=lambda text: "Download CSV" in (text or "")
        )["href"]
        download_link = f"https://www.opencodelists.org{download_link}"

        r = requests.get(download_link)
        r.raise_for_status()

        return pd.read_csv(io.StringIO(r.content.decode("utf-8")))
    except Exception as e:
        st.error(
            f"Failed to retrieve data from the URL. Please check the URL and try again."
        )
        return pd.DataFrame()


def show_plots(code_list, description_column_name, data, column_name):
    """
    For the given code list and data, displays the following:
    - Codes from the uploaded list that were not found in the data
    - Total recorded codes
    - Time series for uploaded code list
    - Time series for each code in the uploaded code list

    Args:
        code_list (DataFrame): DataFrame containing the list of codes.
        description_column_name (str): The name of the column containing the code descriptions within code_list.
        data (DataFrame): The main dataset to compare against.
        column_name (str): The name of the column containing the codes.
    """
    code_list[column_name] = code_list[column_name].astype(str)
    if description_column_name:
        code_list[description_column_name] = code_list[description_column_name].astype(
            str
        )

    data_subset = data[data[column_name].isin(code_list[column_name])]

    missing_codes = code_list[~code_list[column_name].isin(data[column_name])][
        column_name
    ].unique()

    if len(missing_codes) > 0:
        st.title("Missing Codes")
        st.error("Some codes from the uploaded list were not found.")

        if description_column_name:
            missing_codes_description = code_list[
                code_list[column_name].isin(missing_codes)
            ][[column_name, description_column_name]]

            missing_codes_description = missing_codes_description.rename(
                columns={column_name: "SNOMED CT Code"}
            )
            missing_codes_description = missing_codes_description.rename(
                columns={description_column_name: "Description"}
            )
            st.write(missing_codes_description)
        else:
            missing_codes_description = code_list[
                code_list[column_name].isin(missing_codes)
            ][[column_name]]
            missing_codes_description = missing_codes_description.rename(
                columns={column_name: "SNOMED CT Code"}
            )
            st.write(missing_codes_description)

    if description_column_name:
        code_list = code_list.rename(
            columns={description_column_name: "description_temp"}
        )

    if "Description" in code_list.columns:
        code_list = code_list.drop(columns=["Description"])

    merged_data = pd.merge(data_subset, code_list, on=column_name)

    merged_data["Usage"] = merged_data["Usage"].replace("*", np.nan).astype(float)

    code_counts = merged_data.groupby(column_name)[["Usage"]].sum().reset_index()
    code_counts[column_name] = code_counts[column_name].astype(str)

    code_counts["Description"] = code_counts[column_name].apply(
        lambda x: merged_data[merged_data[column_name] == x]["Description"].values[0]
    )

    if description_column_name:

        code_counts = code_counts.merge(
            code_list[[column_name, "description_temp"]], on=column_name, how="left"
        )
        code_counts = code_counts.rename(columns={column_name: "SNOMED CT Code"})
        code_counts = code_counts[["SNOMED CT Code", "Description", "Usage"]]

    else:
        code_counts = code_counts.rename(columns={column_name: "SNOMED CT Code"})

    merged_data["Description"] = merged_data[column_name].apply(
        lambda x: merged_data[merged_data[column_name] == x]["Description"].values[0]
    )

    st.title("Total recorded codes")
    st.write(code_counts)

    time_series_data = merged_data.groupby("year_start")["Usage"].sum().reset_index()
    st.title("Time Series for Uploaded Code List")
    st.pyplot(plot_time_series(time_series_data))

    individual_counts = (
        merged_data.groupby(["year_start", column_name])["Usage"].sum().reset_index()
    )

    for code in code_list[column_name].unique():
        st.title(f"Time Series for Code: {code}")

        if code not in missing_codes:

            code_data = individual_counts[individual_counts[column_name] == code]
            code_description = merged_data[merged_data[column_name] == code][
                "Description"
            ].values[0]
            st.write(f"Description: {code_description}")
            st.pyplot(plot_time_series(code_data))

        else:
            st.error(f"The code {code} was not found.")


def select_columns(data, key_names):
    """
    Allow the user to select columns from the data.

    Args:
        data (DataFrame): DataFrame containing the data.
        key_names (dict): A dictionary with keys for the selectboxes. Should contain 'column' and 'description' keys.

    Returns:
        dict: A dictionary with the names of the selected columns.
    """
    column_name = st.sidebar.selectbox(
        "Select the column containing the codes",
        data.columns,
        key=key_names["column"],
        index=0,
    )

    if len(data.columns) > 1:
        options = ["None"] + list(data.columns)
        description_column_name = st.sidebar.selectbox(
            "Select the column containing code descriptions (optional)",
            options,
            key=key_names["description"],
            index=0,
        )

        if description_column_name == "None":
            description_column_name = None

    else:
        description_column_name = None

    return {
        "column_name": column_name,
        "description_column_name": description_column_name,
    }
