import pandas as pd
from mci.scoring import compute_score

# Small test dataset
test_data = [
    {"Client ID": 1, "First Name": "JS01", "Last Name": "", 
     "Date of Birth": pd.to_datetime("1985-03-12"),
     "IsAnon": True, "FirstInitial": "J", "LastInitial": "S", 
     "BirthMonthFromID": "03", "BirthYearFromID": "85",
     "Race": "White", "GenderIdentity": "Male", "ZIP": "10001"},
    
    {"Client ID": 2, "First Name": "SJ01", "Last Name": "", 
     "Date of Birth": pd.to_datetime("1985-03-12"),
     "IsAnon": True, "FirstInitial": "S", "LastInitial": "J", 
     "BirthMonthFromID": "03", "BirthYearFromID": "85",
     "Race": "White", "GenderIdentity": "Male", "ZIP": "10001"},

    {"Client ID": 3, "First Name": "John", "Last Name": "Smith", 
     "Date of Birth": pd.to_datetime("1986-12-03"),
     "IsAnon": False, "FirstInitial": "J", "LastInitial": "S", 
     "BirthMonthFromID": None, "BirthYearFromID": None,
     "Race": "White", "GenderIdentity": "Male", "ZIP": "10001"},
]

df = pd.DataFrame(test_data)

# Run tests
print("Row1 vs Row2 (flipped initials):", compute_score(df.iloc[0], df.iloc[1]))
print("Row1 vs Row3 (off by one year):", compute_score(df.iloc[0], df.iloc[2]))
print("Row2 vs Row3:", compute_score(df.iloc[1], df.iloc[2]))