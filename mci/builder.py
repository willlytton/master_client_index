import pandas as pd

from rapidfuzz import fuzz
from tqdm import tqdm

from mci import compute_score



def build_master_client_index(df, starting_id = 1, score_function = None, high_threshold = 85, borderline_thresold = 85):
    """
    Build a Master Client Index (MCI) from a demographics DateFrame

    Parameter:
    - df: pd.DataFrame with client data must include:
        ['Client ID','First Name', 'Last Name', 'Date of Birth', 'ZIP','IsAnon',
            ' FirstInitial', 'LastInitial', 'BirthMonthFromID', BirthYearFromID']
    - starting_id: integer to start assigning MCI_IDs
    - score_func: function that takes (row1, row2) and return similarity score 0-100
    - high_threshold: score above which clients are considered duplicates
    - borderline_thresold: score above which clients are flagged as possible duplicates

    Returns:
    - df_wth_ids: original df with MCI_ID column assigned
    - mci: Master Client Index DataFrame
    - borderline_matches: list of possible duplicate matches
    
    """
    # Assigns MCI_IDs and creates a deduplicated MCI file
    # Keeps borderline matches in a seperate file.

    if score_function is None:
        raise ValueError("A scoring function must be provided via score_function parameter.")
    
    # Make a copy of the input dataframe
    df_with_ids = df.copy()

    # Initialize empty MCI DataFram
    mci = pd.DataFrame(columns=[
        "MCI_ID", "First Name", "Last Name", "Date of Birth","FirstInitial",
        "LastInitial", "BirthMonthFromID", "BirthYearFromID",
        "ZIP", "Original_Client_IDs", "IsAnon"
    ])
    next_id = starting_id
    borderline_matches = []
    

    for idx, row in tqdm(df_with_ids.iterrows(), total=len(df_with_ids), desc="Checking clients"):
        found_match = False

        # Compre current row to all other existing MCI entries
        for i, mci_row in mci.iterrows():
            score = compute_score(row, mci_row)

            if score >= high_threshold: # strong match
                # # High confidence match -> assign existing MCI_ID
                df_with_ids.at[idx, "MCI_ID"] = mci_row["MCI_ID"]
                mci.at[i, "Original_Client_IDs"] += f",{row["Client ID"]}"
                found_match = True
                break
            

            elif borderline_thresold <= score <= high_threshold:
                # Borderline match -> flag for manual review
                borderline_matches.append({
                    "Record1_ID": row["Client ID"],
                    "MCI_ID": mci_row["MCI_ID"],
                    "Score": score,
                    "FirstName1": row["First Name"],
                    "LastName1": row["Last Name"],
                    "FirstName2": mci_row["First Name"],
                    "LastName2": mci_row["Last Name"],
                    "DOB1": row["Date of Birth"] if not row["IsAnon"] 
                        else f"{row.get('BirthMonthFromID')}/{row.get('BirthYearFromID')}",
                    "DOB2": mci_row["Date of Birth"] if not mci_row["IsAnon"]
                        else f"{mci_row.get('BirthMonthFromID')}/{mci_row.get('BirthYearFromID')}",
                    "ZIP1": row.get("ZIP"),
                    "ZIP2": mci_row.get("ZIP"),
                })

        if not found_match:
            # New client -> create new MCI entry
            df_with_ids.at[idx, "MCI_ID"] = next_id
            new_row = {
                "MCI_ID": next_id,
                "First Name": row["First Name"],
                "Last Name": row["Last Name"],
                "Date of Birth": row["Date of Birth"], # Date of Birth exists for all clients
                "FirstInitial": row.get("FirstInitial"),
                "LastInitial": row.get("LastInitial"),
                "BirthMonthFromID": row.get("BirthMonthFromID") if row["IsAnon"] else pd.NA,
                "BirthYearFromID": row.get("BirthYearFromID") if row["IsAnon"] else pd.NA,
                "ZIP": row["ZIP"],
                "Original_Client_IDs": str(row["Client ID"]),
                "IsAnon": row["IsAnon"]
            }

            mci.loc[len(mci)] = new_row
            next_id += 1

    return df_with_ids, mci, borderline_matches



