from __future__ import annotations
from typing import Any, Optional, TypedDict, Dict
from datetime import date
import unicodedata, re
import pandas as pd


def _normalize(s: Any) -> str:
    """Unicide NFKC + trim + collapse whitespace. Always return str.
    """
    if s is None or pd.isna(s): return ""
    s = unicodedata.normalize("NFKC", str(s))
    return re.sub(r"\s+", " ", s, flags=re.UNICODE).strip()
    

def _initial(s: Any) -> str:
    """
    First alphabet letter (UNICIDE-aware), ASCII-folded, uppercase; "" if none."""
    text = _normalize(s)
    for ch in text:
        if ch.isalpha():
            # strips diacritics (NFD) and fold to ASCII where possible
            base = unicodedata.normalize("NFD", ch)
            base = "".join(c for c in base if unicodedata.category(c) != "Mn")
            # handle special multi-letter cases via casefold
            cf = base.casefold()
            return (cf[0].upper() if cf else "")
    return ""

# def to_initial(first_name, last_name) -> dict[str, str]:
#     return {
#         "FirstInitial" : _initial(first_name),
#         "LastInitial" : _initial(last_name),
#     }



def _to_int(x: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safe integer parse; None on NA/invalid.
    """
    s = _normalize(x)
    if not s: return default
    
    s = re.sub(r"[^\d\-]+", "", s) # strip everything but digits/minus
    if s in {"", "-", "--"}: return default
    try: return int(s)
    except Exception: return default
    
    
def _to_date(y: Any, m: Any, d: Any) -> Optional[date]:
    """
    Build a real date when possible. Handles obvious MM/DD flips and '00 day.
    Returns datetime.date or None (if partial/invalid)
    """
    Y, M, D = _to_int(y), _to_int(m), _to_int(d)
    if Y is None: return None
    # flip if month > 12 but day <= 12 (e.g., entered DD/MM)
    if M is not None and D is not None and M > 12 and D <= 12: M, D = D, M
    # unkwown day
    if D == 0:
        D = None
    if M and D:
        try: return date(Y, M, D)
        except Exception: return None
    return None # keep partials as separate fields (year/month)
        

