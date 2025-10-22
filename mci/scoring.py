import pandas as pd
from rapidfuzz import fuzz

def score_initials(row1, row2):
    score = 0

    # Compare initials
    if pd.notna(row1.get("FirstInitial")) and pd.notna(row2.get("FirstInitial")):
        if row1["FirstInitial"] == row2["FirstInitial"]:
            score += 20

    if pd.notna(row1.get("LastInitial")) and pd.notna(row2.get("LastInitial")):
        if row1["LastInitial"] == row2["LastInitial"]:
            score += 20

    if pd.notna(row1.get("FirstInitial")) == pd.notna(row2.get("LastInitial")) and pd.notna(row1.get("LastInitial")) == pd.notna(row2.get("FirstInitial")):
        score += 15
    
    return score

def score_birthdate(row1, row2):
    score = 0

    # Compare full DOB if it exists
    if pd.notna(row1.get("Date of Birth")) and pd.notna(row2.get("Date of Birth")):
        dob1, dob2 = row1["Date of Birth"], row2["Date of Birth"]

        if dob1 == dob2:
            score += 40

    # Compare month identifier (if available)
    if pd.notna(row1.get("BirthMonthFromID")) and pd.notna(row2.get("BirthMonthFromID")):
        if row1["BirthMonthFromID"] == row2["BirthMonthFromID"]:
            score += 20

    if pd.notna(row1.get("BirthMonthFromID")) == pd.notna(row2.get("BirthYearFromID")) and (
        pd.notna(row1.get("BirthYearFromID")) == pd.notna(row2.get("BirthMonthFromID"))
    ):
        score += 15

    return score

def score_birthyear(row1, row2):
    score = 0
    
    y1, y2 = pd.notna(row1.get("BirthYearFromID")), pd.notna(row2.get("BirthYearFromID"))
    m1, m2 = pd.notna(row1.get("BirthMonthFromID")), pd.notna(row2.get("BirthMonthFromID"))

    if y1 and y2:
        if y1 == y2:
            score += 20
        elif abs(int(y1) - int(y2)) == 1:
            score += 10

        if m1 and y1 and m2 and y2:
            if m1 == y2 and y1 == m2:
                score += 10
    
        return score





# scoring function
def compute_score(row1, row2):
# threshold system (e.g. >= 85 definite, 65-84 possible, < 65 unlikely)
# Compute similarity score between two clients (anon or non-anon)
# Returns a score scaled from 0 to 100

    score = 0

    if row1["IsAnon"] or row2["IsAnon"]:
        max_possible = 120

    else:
        max_possible = 270
    
    score += score_initials(row1, row2)
    score += score_birthdate(row1, row2)
    score += score_birthyear(row1, row2)

    # Non-anonymous client logic (fuzzy full name + DOB + ZIP)
    score += fuzz.partial_ratio(str(row1.get("First Name", "")), str(row2.get("FirstName", "")))
    score += fuzz.partial_ratio(str(row1.get("Last Name", "")), str(row2.get("Last Name", "")))

    # ZIP match
    if pd.notna(row1.get("ZIP")) and pd.notna(row2.get("ZIP")):
        if row1["ZIP"] == row2["ZIP"]:
            score += 20

    return  (score / max_possible) * 100

