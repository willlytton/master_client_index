import pandas as pd
from rapidfuzz import fuzz

from mci.extract import safe_extract
from mci.builder import build_master_client_index
from mci.scoring import compute_score

if __name__== "__main__":
    df = pd.read_csv("demographics_data.csv")

    df = df.sample(n = 500, random_state = 42).reset_index(drop = True)

    # Normalize columns
    df.columns = df.columns.str.strip()
    df.rename(columns = {"Zip": "ZIP"}, inplace = True)


    # Extract anonymous fields
    df = df.apply(safe_extract, axis = 1)

    print(df.head())
    print(df.columns)

    # Build MCI
    df_with_ids, mci_df, borderline_matches = build_master_client_index(
        df,
        starting_id = 1,
        score_function = compute_score,
        high_threshold= 85,
        borderline_thresold = 65)

    mci_df.to_excel("master_client_index.xlsx", index=False)
    df_with_ids.to_excel("clients_with_mci.xlsx", index=False)
    pd.DataFrame(borderline_matches).to_excel("borderline_matches.xlsx", index=False)

    print("✅ MCI created successfully using hybrid DOB approach!")
    print("Files saved:")
    print(" - master_client_index.xlsx")
    print(" - clients_with_mci.xlsx")
    print(" - borderline_matches.xlsx (review optional)")
