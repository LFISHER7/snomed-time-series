import re
import pandas as pd
from pathlib import Path


def load_and_combine_data(raw_data_folder, processed_data_folder):
    """
    Loads all .xlsx and .txt files from the specified raw data folder, combines them into a single DataFrame,
    and saves the combined data as a CSV file in the processed data folder.

    Parameters:
    raw_data_folder (str): The folder path where .xlsx and .txt raw data files are stored.
    processed_data_folder (str): The folder path where the processed data file will be saved.

    Returns:
    None
    """
    raw_data_path = Path(raw_data_folder)
    processed_data_path = Path(processed_data_folder)

    # Ensure that the processed_data_folder exists
    processed_data_path.mkdir(parents=True, exist_ok=True)

    all_files = list(raw_data_path.glob("*.xlsx")) + list(raw_data_path.glob("*.txt"))

    df_list = []

    for file in all_files:
        print(f"Loading file: {file.name}")
        try:
            if file.suffix == ".xlsx":
                df = pd.read_excel(file)
            elif file.suffix == ".txt":
                df = pd.read_csv(file, sep="\t")
            else:
                raise ValueError(f"Unsupported file type: {file.suffix}")

            year_pattern = re.compile(r"\d{4}")
            year_match = year_pattern.search(file.name)
            if year_match:
                year = year_match.group()
                year_start = f"{year}-08-01"
                df["year_start"] = year_start
                df_list.append(df)
            else:
                print(f"Year not found in file name: {file.name}")

        except Exception as e:
            print(f"Error loading file {file.name}: {e}")

    combined_df = pd.concat(df_list, ignore_index=True).sort_values(
        by=["year_start", "SNOMED_Concept_ID"]
    )

    output_file = processed_data_path / "combined_data.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"Combined data saved to {output_file}")


# Example usage
if __name__ == "__main__":
    load_and_combine_data("data/raw", "data/processed")
