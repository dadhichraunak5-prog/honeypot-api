import re
from typing import Dict, List

class IntelligenceExtractor:
    # Common UPI handle suffixes used to distinguish UPI IDs from plain emails
    UPI_SUFFIXES = (
        "@upi", "@ybl", "@paytm", "@ibl", "@axl", "@okaxis",
        "@okhdfcbank", "@okicici", "@oksbi", "@apl", "@icici", "@sbi"
    )

    def extract_from_message(self, text: str) -> Dict[str, List[str]]:
        intelligence = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        }

        # Extract phone numbers first, so we can exclude them from bank accounts
        phones = re.findall(r'\+?\d{10,13}', text)
        intelligence["phoneNumbers"] = phones

        # Extract bank account numbers (9-18 digits), excluding anything
        # already identified as a phone number to avoid double-counting.
        # Also require length >= 11 to reduce false positives on shorter
        # generic numbers (order IDs, OTPs, etc.)
        banks_raw = re.findall(r'\b\d{9,18}\b', text)
        intelligence["bankAccounts"] = [
            b for b in banks_raw if b not in phones and len(b) >= 11
        ]

        # Extract email-like strings, then split into UPI IDs vs plain emails
        # based on known UPI handle suffixes
        email_like = re.findall(r'[\w.-]+@[\w.-]+', text)
        upis = [e for e in email_like if e.lower().endswith(self.UPI_SUFFIXES)]
        intelligence["upiIds"] = upis

        # Extract URLs
        urls = re.findall(r'http[s]?://[^\s]+', text)
        intelligence["phishingLinks"] = urls

        # Extract suspicious keywords
        keywords = ["urgent", "verify", "blocked", "suspended", "otp", "bank", "account", "password"]
        found = [kw for kw in keywords if kw in text.lower()]
        intelligence["suspiciousKeywords"] = found

        return intelligence
