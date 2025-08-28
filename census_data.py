import pandas as pd
from rapidfuzz import fuzz
import re
from tqdm import tqdm

anon_pattern = re.compile(r"^([A-Z])([A-Z])(\d{2})(\d{2})(?:-\d+)?$")

def parse_identifier(name: str):
    """Detects a anonymous client and parses"""
    match = anon_pattern.match(str(name).strip())
    if match:
        return {
            "IsAnon": True,
            "FirstInitial": match.group(1),
            "LastInitial" : match.group(2),
            "BirthMonthFromID": match.group(3),
            "BirthYearFromID": match.group(4),
        }
    
    return None

def is_anonymous(name: str):
    return bool(anon_pattern.match(str(name).strip()))

def safe_extract(row):

    # Parses fields for anonymous and non-anonymous clients
    # Uses parse_identifier only if the field looks like an anonymous ID

    # parsed_first = parse_identifier(str(row.get("First Name", "")))
    # parsed_last = parse_identifier(str(row.get("Last Name", "")))
    # parsed = parsed_first or parsed_last

    first_val = str(row.get("First Name", "")).strip()
    last_val = str(row.get("Last Name", "")).strip()

    parsed = None
    if is_anonymous(first_val):
        parsed = parse_identifier(first_val)
    elif is_anonymous(last_val):
        parsed = parse_identifier(last_val)

    if parsed:
        row["IsAnon"] = True
        row["FirstInitial"] = parsed["FirstInitial"]
        row["LastInitial"] = parsed["LastInitial"]
        row["BirthMonthFromID"] = parsed["BirthMonthFromID"]
        row["BirthYearFromID"] = parsed["BirthYearFromID"]
    else:
        row["IsAnon"] = False
        row["FirstInitial"] = None
        row["LastInitial"] = None
        row["BirthMonthFromID"] = None
        row["BirthYearFromID"] = None

    return row


# print(df.head())
# print(df.columns)
# df.info()
# df.fillna('')


# scoring function
def compute_score(row1, row2):
# threshold system (e.g. >= 85 definite, 65-84 possible, < 65 unlikely)
# Compute similarity score between two clients (anon or non-anon)
# Returns a score scaled from 0 to 100

    score = 0

    if row1["IsAnon"] or row2["IsAnon"]:
        max_possible = 120

        # Compare initials
        if pd.notna(row1.get("FirstInitial")) and pd.notna(row2.get("FirstInitial")):
            if row1["FirstInitial"] == row2["FirstInitial"]:
                score += 20

        if pd.notna(row1.get("LastInitial")) and pd.notna(row2.get("LastInitial")):
            if row1["LastInitial"] == row2["LastInitial"]:
                score += 20


        # Compare full DOB if it exists
        if pd.notna(row1["Date of Birth"]) and pd.notna(row2["Date of Birth"]):
            if row1["Date of Birth"] == row2["Date of Birth"]:
                score += 40

        # Compare month/year from identifier (if available)
        if pd.notna(row1.get("BirthMonthFromID")) and pd.notna(row2.get("BirthMonthFromID")):
            if row1["BirthMonthFromID"] == row2["BirthMonthFromID"]:
                score += 20

        if pd.notna(row1.get("BirthYearFromID")) and pd.notna(row2.get("BirthYearFromID")):
            if row1["BirthYearFromID"] == row2["BirthYearFromID"]:
                score += 20

    else:
        max_possible = 270

        # Non-anonymous client logic (fuzzy full name + DOB + ZIP)
        score += fuzz.partial_ratio(str(row1.get("First Name", "")), str(row2.get("FirstName", "")))
        score += fuzz.partial_ratio(str(row1.get("Last Name", "")), str(row2.get("Last Name", "")))

        # DOB exact match
        if pd.notna(row1.get("Date of Birth")) and pd.notna(row2.get("Date of Birth")):
            if row1["Date of Birth"] == row2["Date of Birth"]:
                score += 50

        # ZIP match
        if pd.notna(row1.get("ZIP")) and pd.notna(row2.get("ZIP")):
            if row1["ZIP"] == row2["ZIP"]:
                score += 20


    normalized_score = (score / max_possible) * 100
    return normalized_score

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



# ---------------------------
# Main script
# ---------------------------
if __name__== "__main__":
    df = pd.read_csv("demographics_data.csv")

    df = df.sample(n = 500, random_state = 42).reset_index(drop = True)

    # Normalize columns
    df.columns = df.columns.str.strip()
    df.rename(columns = {"Zip": "ZIP"}, inplace = True)

      # Normalize string fields
    df["First Name"] = df["First Name"].str.upper().str.strip()
    df["Last Name"] = df["Last Name"].str.upper().str.strip()
    df["ZIP"] = df["ZIP"].astype(str).str.zfill(5)
    df["Date of Birth"] = pd.to_datetime(df["Date of Birth"], errors="coerce")

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

