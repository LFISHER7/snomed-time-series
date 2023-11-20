import streamlit as st
import pandas as pd
import pathlib
import pyautogui
import requests
import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from bs4 import BeautifulSoup


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

        st.write("Time Series Graph")
        st.pyplot(plot_time_series(filtered_data))

    else:
        st.error(
            f"The code {code_input} was not found. Please ensure the code entered is a SNOMED-CT code."
        )

st.sidebar.title("Upload a Code List")
st.sidebar.write('Upload a CSV file with a column named "SNOMED_Concept_ID"')
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")


def show_plots(code_list, data, column_name):
    code_list[column_name] = code_list[column_name].astype(str)

    data_subset = data[data[column_name].isin(code_list[column_name])]
    # Find which codes in the uploaded file are not in the main dataset
    missing_codes = code_list[~code_list[column_name].isin(data[column_name])][
        column_name
    ].unique()

    if len(missing_codes) > 0:
        st.title("Missing Codes")
        # Display the missing codes
        st.error("Some codes from the uploaded list were not found.")
        # show the missing codes in a dataframe
        st.write(pd.DataFrame(missing_codes, columns=["Missing Codes"], dtype=str))

    # If there are no missing codes, proceed with the merge and rest of the analysis
    merged_data = pd.merge(data_subset, code_list, on=column_name)

    # convert usage to float
    # replace any '*" in usage column with np.nan
    merged_data["Usage"] = merged_data["Usage"].replace("*", np.nan)

    # convert non-null values to int
    merged_data["Usage"] = merged_data["Usage"].astype(float)

    # aggregate count by code and display in table
    code_counts = merged_data.groupby(column_name)[["Usage"]].sum().reset_index()
    code_counts[column_name] = code_counts[column_name].astype(str)
    st.title("Total recorded codes")
    st.write(code_counts)

    time_series_data = merged_data.groupby("year_start")["Usage"].sum().reset_index()

    st.title("Time Series for Uploaded Code List")
    st.pyplot(plot_time_series(time_series_data))

    individual_counts = (
        merged_data.groupby(["year_start", column_name])["Usage"].sum().reset_index()
    )
    for code in code_list[column_name].unique():
        # write title
        st.title(f"Time Series for Code: {code}")
        if code not in missing_codes:
            code_data = individual_counts[individual_counts[column_name] == code]
            st.pyplot(plot_time_series(code_data))

        else:
            st.error(f"The code {code} was not found.")


if uploaded_file is not None:
    code_list = pd.read_csv(uploaded_file)

    # Once the file is uploaded, show a select box with column names
    column_name = st.sidebar.selectbox(
        "Select the column containing the codes",
        code_list.columns,
        key="column_selector",
    )

    # rename main dataset column to match the uploaded file
    data = data.rename(columns={"SNOMED_Concept_ID": column_name})

    if st.sidebar.button("Analyse Code List"):
        show_plots(code_list, data, column_name)


@st.cache_data(show_spinner=False)
def get_codes_from_url(url):
    try:
        print(f"Fetching data from {url}")
        page = requests.get(url)

        soup = BeautifulSoup(page.content, "html.parser")
        print(soup)

        # there is a dl section on the page. in it there is a dt with the text "Coding system". Find it then find the siister dd element next to it. See if it is SNOMED-CT
        coding_system_sec = soup.find(
            "dt", string=lambda text: "Coding system" in (text or "")
        )
        coding_system = coding_system_sec.find_next_sibling("dd").text

        if coding_system != "SNOMED CT":
            st.error(
                "The coding system for this codelist is not SNOMED-CT. Please check the URL and try again."
            )
            return []

        download_link = soup.find(
            "a", string=lambda text: "Download CSV" in (text or "")
        )["href"]

        download_link = f"https://www.opencodelists.org{download_link}"

        r = requests.get(download_link)

        codes_df = pd.read_csv(io.StringIO(r.content.decode("utf-8")))

        # return the codes
        return codes_df

    except Exception as e:
        st.error(
            "Failed to retrieve data from the URL. Please check the URL and try again."
        )
        return []


st.sidebar.title("Fetch Codes from OpenCodelists")
url_input = st.sidebar.text_input("Enter a URL")
st.sidebar.write(
    "Enter a URL from https://www.opencodelists.org/ and the codes will be fetched. e.g. https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/cpeptide_cod/20200812"
)


if url_input:
    codes_df = get_codes_from_url(url_input)
  

    # Once the file is uploaded, show a select box with column names
    column_name = st.sidebar.selectbox(
        "Select the column containing the codes",
        codes_df.columns,
        key="column_selector",
    )

    if st.sidebar.button("Analyse Code List"):
        codes = codes_df[column_name].unique().tolist()
        if codes:
            code_list = pd.DataFrame(codes, columns=["SNOMED_Concept_ID"])
            code_list["SNOMED_Concept_ID"] = code_list["SNOMED_Concept_ID"].astype(str)

            data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)

            data["Usage"] = data["Usage"].replace("*", np.nan)
            data["Usage"] = data["Usage"].astype(float)

            show_plots(code_list, data, "SNOMED_Concept_ID")
