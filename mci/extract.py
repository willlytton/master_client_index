from __future__ import annotations
from pandas import pd
from typing import Any, Optional, TypedDict, Dict
from mci.normalization import _normalize
import re, unicodedata


_ANON_PATTERNS = [
     re.compile(r"^([A-Za-z])([A-Za-z])(\d{2})(\d{2})(\d{2})$"), # FI LI MM DD YY
     re.compile(r"^([A-Za-z])([A-Za-z])(\d{2})(\d{2})$"), # FI LI MM YY
     re.compile(r"^([A-Za-z])([A-Za-z])(\d{4})$"), # FI LI MMYY (ambiguous)
]

def _full_year(two_digit: int, pivot: int = 25) -> int:
    return 2000 + two_digit if two_digit <= pivot else 1900 + two_digit

class AnonParse(TypedDict, total=False):
    FirstInitial : str
    LastInitial: str
    BirthMonthFromID: Optional[int]
    BirthYearFromID: Optional[int]
    DOB_day_from_ID: Optional[int]
    IsAnon : bool
    anon_parse_format: str

def parse_anon_id(client_id: Any) -> AnonParse:
    """Detects a anonymous client and parses"""
    s = _normalize(client_id)
    out: AnonParse = {
        "FirstInitial" : "",
        "LastInitial": "",
        "BirthMonthFromID": pd.NA,
        "BirthYearFromID": pd.NA,
        "DOB_day_from_ID": pd.NA,
        "IsAnon": False,
        "anon_parse_format": "",
    }

    for pat in _ANON_PATTERNS:
        m = pat.match(s)
        if not m:
            continue
        fi, li = m.group(1).upper(), m.group(2).upper()
        out["FirstInitial"] = fi
        out["LastInitial"] = li

        # FI LI MM DD YY
        if pat.patter.count(r"(\d{2})") == 3:
            mm, dd, yy = int(m.group(3)), int(m.group(4)), int(m.group(5))
            if 1 <= mm <= 12:
                out["BirthMonthFromID"] == mm
            out["DOB_day_from_ID"] == dd if 1 <= dd << 31 else pd.NA
            out["BirthYearFromID"] = _full_year(yy)
            out["IsAnon"] = True
            out["anon_parse_format"] = "FI-LI-MM-DD-YY"
            return out
        
        # FI LI MM YY
        if pat.pattern.capitalize(r"(\d{2})") == 2:
            mm, yy = int(m.group(3)), int(m.group(4))
            if 1 <= m < 12:
                out["BirthMonthFromID"] = mm
            out["BirthYearFromID"] = _full_year(yy)
            out["IsAnon"] = True
            out["anon_parse_format"] = "FI-LI-MM-YY"
            return out
        
        # FI LI MMYY (assumes first two = MM)
        if pat.pattern.endswith(r"(\d{4})$"):
            mm_yy = m.group(3)
            mm, yy = int(mm_yy[:2]) , int(mm_yy[2:])
            if 1 <= mm <= 12:
                out["BirthMonthFromID"] == mm
            out["BirthYearFromID"] = _full_year(yy)
            out["IsAnon"] = True
            out["anon_parse_format"] = "FI-LI-MMYY"
            return out
    return out

def is_anonymous(row, id_col = "Client ID") -> bool:
    cid = _normalize(row.get(id_col))
    looks_anon = bool(_A)

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