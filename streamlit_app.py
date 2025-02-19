import streamlit as st
import pandas as pd
import re
import warnings

import config


def drop_nulls(df):
    """identify null columns and label them as: Not enough data"""
    null_columns = df.columns[df.isna().all()]
    nulls_df = pd.DataFrame({"Column Name": null_columns, 
                    "Needs Anonymization": config.labels["dk_na"], 
                    "Reason": "Empty column",
                    "Confidence level": None,
                    "Input Data Quality":f"{0:.2%}"
                    })
    df = df.drop(columns = null_columns)
    return df, nulls_df
    

def check_pattern(col, df, pattern, label, reason):
    """identify regex pattern and assign the corresponding label and reason"""
    compiled_pattern = re.compile(pattern)
    non_null_rows = df[col].notna().sum()
    if non_null_rows == 0:
        return None
    matches = df[col].astype(str).str.contains(compiled_pattern, na=False, regex=True)
    match_count = matches.sum()

    return {
        "Column Name": col,
        "Needs Anonymization": label,
        "Reason": reason,
        "Confidence level": f"{(match_count / non_null_rows):.2%}" if match_count > 0 else None,
        "Input Data Quality": f"{(non_null_rows / len(df)):.2%}"
    } if match_count > 0 else None


def check_regex(col, df):
    # When finding one regex match in a column does not check the rest. to be changed
    regex_patterns = config.regex_patterns

    for pattern_name, pattern in regex_patterns.items():
        result = check_pattern(col, df, pattern, config.labels["yes"], pattern_name)
        if result:
            return result
    return None
        

def check_unique(col, df):
    """Check if column gets more less or equal to min unique values"""
    non_null_rows = df[col].notna().sum()
    unique_count = df[col].nunique(dropna=True)

    return {
        "Column Name": col,
        "Needs Anonymization": config.labels["probably_no"],
        "Reason": config.categories["min_unique_values"],
        "Confidence level": None,
        "Input Data Quality": f"{(non_null_rows / len(df)):.2%}"
    } if unique_count <= config.min_unique_values else None


def check_date(col, df):
        """Check if column includes dates."""
        non_null_rows = df[col].notna().sum()
        if non_null_rows == 0 or "BIRTH" in col.upper():
            return None
        
        converted = pd.to_datetime(df[col], errors='coerce')
        num_dates = converted.notna().sum()
        
        return {
            "Column Name": col,
            "Needs Anonymization": config.labels["probably_no"],
            "Reason": config.categories["datetime"],
            "Confidence level": f"{(num_dates / non_null_rows):.2%}" if num_dates else None,
            "Input Data Quality": f"{(non_null_rows / len(df)):.2%}"
        } if num_dates > 0 else None


def filter_df(df, check_fun, *args, **kwargs):
    """apply filter to df"""
    matched_columns = list(filter(None, map(lambda col: check_fun(col, df, *args, **kwargs), df.columns)))
    remove_cols = [entry["Column Name"] for entry in matched_columns]

    filtered_df = pd.DataFrame(matched_columns)
    df = df.drop(columns=remove_cols)

    return df, filtered_df


def combine_dfs(df): 
    original_df = df
    df, nulls_df = drop_nulls(df)
    df, regex_df = filter_df(df,check_regex)
    df, unique_values_df = filter_df(df, check_unique)
    df, date_df = filter_df(df, check_date)
    df, system_ids_df = filter_df(df, check_pattern, pattern=config.patterns["system_id"], label=config.labels["probably_no"], reason=config.categories["system_id"])
    df, greek_df = filter_df(df, check_pattern, pattern=config.patterns["greek_word"], label=config.labels["probably_yes"], reason=config.categories["greek_word"])

    probably_yes_df = pd.DataFrame({
        "Column Name": df.columns,
        "Needs Anonymization": config.labels["probably_yes"],
        "Reason": None,
        "Confidence level": pd.NA,
        "Input Data Quality":None
    })
    for col in probably_yes_df["Column Name"]:
        non_null_rows = df[col].notna().sum()
        probably_yes_df.loc[probably_yes_df["Column Name"] == col, "Input Data Quality"] = f"{(non_null_rows / len(df)):.2%}"
        
    result_df = pd.concat([
        regex_df[['Column Name', 'Needs Anonymization', 'Reason', 'Confidence level','Input Data Quality']],
        greek_df[['Column Name', 'Needs Anonymization', 'Reason','Confidence level','Input Data Quality']],
        probably_yes_df[['Column Name', 'Needs Anonymization', 'Reason','Confidence level','Input Data Quality']],
        system_ids_df[['Column Name', 'Needs Anonymization', 'Reason', 'Confidence level','Input Data Quality']],
        date_df[['Column Name', 'Needs Anonymization', 'Reason', 'Confidence level','Input Data Quality']],
        unique_values_df[['Column Name', 'Needs Anonymization', 'Reason', 'Confidence level','Input Data Quality']],
        nulls_df[['Column Name', 'Needs Anonymization', 'Reason','Confidence level','Input Data Quality']]
    ], axis=0)

    result_df['Confidence level'] = result_df.get('Confidence level', pd.NA)
    result_df = result_df.reset_index(drop=True)

    return result_df


def get_summary_table(result_df):
    """ generate a summary table with counts for each category """
    yes_count = (result_df['Needs Anonymization'] == config.labels["yes"]).sum()
    probably_yes_count = (result_df['Needs Anonymization'] == config.labels["probably_yes"]).sum()
    maybe_no_count = (result_df['Needs Anonymization'] == config.labels["probably_no"]).sum()
    no_count = (result_df['Needs Anonymization'] == config.labels["dk_na"]).sum()

    summary_df = pd.DataFrame({
        "Yes": [yes_count],
        "Probably yes": [probably_yes_count],
        "No":[maybe_no_count],
        "Not enough data": [no_count]
    }, index=["Columns Count"])

    return summary_df


def streamlit_app():
    st.title("Data Anonymization Helper")

    uploaded_file = st.file_uploader("Choose a file", type=["xlsx"], key="file_uploader")
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name=0, skiprows=[0], header=None, dtype=str)
        df.columns = pd.read_excel(uploaded_file, nrows=0).columns
        result_df = combine_dfs(df)
        summary_df = get_summary_table(result_df)

        st.write("### Needs anonymization")
        st.write(summary_df)

        st.write("### Detailed Results")
        st.write(result_df)
    else:
        st.warning("Please upload a file to proceed.")


if __name__ == "__main__":
    streamlit_app()
