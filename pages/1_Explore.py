import pathlib

import pandas as pd
import streamlit as st

from src.utils import load_data, display_metric

path = pathlib.Path(__file__).resolve().parents[1]
DATA_PATH = path / "data/processed/combined_data.csv"
METADATA_PATH = path / "data/processed/metadata.csv"


def plot_bar_chart(data, x, y, title, help_text):
    st.markdown(f"##### {title}", help=help_text)
    st.bar_chart(data, x=x, y=y)


@st.cache_data
def dashboard(data):
    data_latest_year = data[data["year_start"] == data["year_start"].max()]
    st.title("Explore")
    col = st.columns((3, 4.5, 2), gap="medium")

    with col[0]:
        st.subheader("Number of recorded events")
        total_number_recorded = data["Usage"].sum()
        display_metric(
            "Total number of recorded events",
            total_number_recorded,
            """Total number of times a SNOMED CT code was recorded in patients
            health records across the entire period""",
        )

        total_events_per_year = (
            data.resample("A", on="year_start")[["Usage"]].sum().reset_index()
        )
        total_events_per_year["Year"] = total_events_per_year[
            "year_start"
        ].dt.year.apply(lambda x: f"{x}-{x+1}")
        total_events_per_year["Usage"] = total_events_per_year["Usage"] / 1_000_000_000
        total_events_per_year = total_events_per_year.rename(
            columns={"Usage": "Total Events (Billion)"}
        )
        plot_bar_chart(
            total_events_per_year,
            "Year",
            "Total Events (Billion)",
            "Total Events per Year",
            """Total number of events recorded in patients health records
            each year (billion)""",
        )

        st.divider()
        st.subheader("Number of unique SNOMED CT codes")
        unique_codes = data["SNOMED_Concept_ID"].nunique()
        display_metric(
            "Total number of unique codes",
            unique_codes,
            """Total number of unique SNOMED CT codes recorded in patients
            health records across the entire period""",
        )

        unique_codes_per_year = (
            data.resample("A", on="year_start")[["SNOMED_Concept_ID"]]
            .count()
            .reset_index()
        )
        unique_codes_per_year["Year"] = unique_codes_per_year[
            "year_start"
        ].dt.year.apply(lambda x: f"{x}-{x+1}")
        unique_codes_per_year = unique_codes_per_year.rename(
            columns={"SNOMED_Concept_ID": "Total Codes"}
        )
        plot_bar_chart(
            unique_codes_per_year,
            "Year",
            "Total Codes",
            "Number of unique codes per year",
            """Number of unique codes recorded in patients
            health records each year""",
        )

        st.divider()
        st.subheader("Number of active codes")
        active_codes = data[data["Active_at_End"] == True][
            "SNOMED_Concept_ID"
        ].nunique()
        display_metric(
            "Number of codes currently active",
            active_codes,
            "Number of codes active in the latest available year",
        )

        active_codes_with_records = data[
            (data["Active_at_End"] == True) & (data["Usage"] > 0)
        ]["SNOMED_Concept_ID"].nunique()
        display_metric(
            "Number of codes currently active with records",
            active_codes_with_records,
            """Number of codes active in the latest year with total
            recorded usage above 0""",
        )

        st.divider()

    with col[1]:
        st.subheader("Most commonly recorded codes")
        usage_total = data_latest_year["Usage"].sum()
        percentile_90 = usage_total * 0.9
        percentile_99 = usage_total * 0.99

        codes_sorted_by_usage = data_latest_year.sort_values(
            by="Usage", ascending=False
        )
        cumulative_usage = codes_sorted_by_usage["Usage"].cumsum()
        codes_needed_90th = (cumulative_usage < percentile_90).sum()
        codes_needed_99th = (cumulative_usage < percentile_99).sum()
        display_metric(
            "Number of codes accounting for top 90% of total usage",
            codes_needed_90th,
            "",
        )
        display_metric(
            "Number of codes accounting for top 99% of total usage",
            codes_needed_99th,
            "",
        )

        total_all_time = data["Usage"].sum()
        top_20_all_time = (
            data.groupby("SNOMED_Concept_ID")
            .agg({"Usage": "sum"})
            .nlargest(20, "Usage")
        )
        top_20_all_time["% of Total Usage"] = round(
            (top_20_all_time["Usage"] / total_all_time) * 100, 2
        )
        top_20_all_time_with_descriptions = top_20_all_time.merge(
            data[["SNOMED_Concept_ID", "Description"]].drop_duplicates(),
            on="SNOMED_Concept_ID",
            how="left",
        )
        top_20_all_time_with_descriptions.rename(
            columns={"SNOMED_Concept_ID": "SNOMED CT Code"}, inplace=True
        )

        st.markdown("##### Top 20 codes used over the whole period")
        st.dataframe(
            top_20_all_time_with_descriptions.set_index("SNOMED CT Code"), height=250
        )
        usage_total_latest_year = data_latest_year["Usage"].sum()
        top_20_last_year = (
            data_latest_year.groupby("SNOMED_Concept_ID")
            .agg({"Usage": "sum"})
            .nlargest(20, "Usage")
        )
        top_20_last_year["% of Total Usage"] = round(
            (top_20_last_year["Usage"] / usage_total_latest_year) * 100, 2
        )
        top_20_last_year_with_descriptions = top_20_last_year.merge(
            data[["SNOMED_Concept_ID", "Description"]].drop_duplicates(),
            on="SNOMED_Concept_ID",
            how="left",
        )
        top_20_last_year_with_descriptions.rename(
            columns={"SNOMED_Concept_ID": "SNOMED CT Code"}, inplace=True
        )
        st.markdown("##### Top 20 codes used in the latest year")
        st.dataframe(
            top_20_last_year_with_descriptions.set_index("SNOMED CT Code"), height=250
        )

        st.divider()
        st.subheader("New codes")
        new_codes = data_latest_year[
            (data_latest_year["Active_at_End"] == 1)
            & (data_latest_year["Active_at_Start"] == 0)
        ]
        num_new_codes = new_codes["SNOMED_Concept_ID"].nunique()
        display_metric(
            "Number of new codes",
            num_new_codes,
            "Number of new codes which became active in the latest year",
        )
        st.markdown("##### Top 20 new codes")
        top_20_new_codes = (
            new_codes.groupby("SNOMED_Concept_ID")
            .agg({"Usage": "sum"})
            .nlargest(20, "Usage")
        )
        top_20_new_codes_with_descriptions = top_20_new_codes.merge(
            data[["SNOMED_Concept_ID", "Description"]].drop_duplicates(),
            on="SNOMED_Concept_ID",
            how="left",
        )
        top_20_new_codes_with_descriptions.rename(
            columns={"SNOMED_Concept_ID": "SNOMED CT Code"}, inplace=True
        )
        st.dataframe(
            top_20_new_codes_with_descriptions.set_index("SNOMED CT Code"), height=250
        )

    with col[2]:
        metadata = pd.read_csv(METADATA_PATH, header=0)
        st.subheader("Organisation data")
        plot_bar_chart(
            metadata,
            "ReportingPeriod",
            "Practices",
            "Number of general practices",
            """Number of general practices with recorded events each year
            as available in dataset metadata""",
        )
        plot_bar_chart(
            metadata,
            "ReportingPeriod",
            "RegisteredPatients",
            "Number of registered patients",
            """Number of registered patients in each year
            as available in dataset metadata""",
        )
        plot_bar_chart(
            metadata,
            "ReportingPeriod",
            "GPSystemSuppliers",
            "Number of general practice system suppliers",
            """Number of general practice system suppliers in each year
            as available in dataset metadata""",
        )


def main():
    st.set_page_config(page_title="Explore", page_icon="🔍", layout="wide")
    data = load_data(DATA_PATH)
    data["SNOMED_Concept_ID"] = data["SNOMED_Concept_ID"].astype(str)
    dashboard(data)


if __name__ == "__main__":
    main()
