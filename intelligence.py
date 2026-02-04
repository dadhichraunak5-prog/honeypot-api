import re
from typing import Dict, List

class IntelligenceExtractor:
    def extract_from_message(self, text: str) -> Dict[str, List[str]]:
        intelligence = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        }
        
        # Extract bank account numbers (9-18 digits)
        banks = re.findall(r'\b\d{9,18}\b', text)
        intelligence["bankAccounts"] = banks
        
        # Extract UPI IDs (something@something)
        upis = re.findall(r'[\w.-]+@[\w.-]+', text)
        intelligence["upiIds"] = upis
        
        # Extract URLs
        urls = re.findall(r'http[s]?://[^\s]+', text)
        intelligence["phishingLinks"] = urls
        
        # Extract phone numbers
        phones = re.findall(r'\+?\d{10,13}', text)
        intelligence["phoneNumbers"] = phones
        
        # Extract suspicious keywords
        keywords = ["urgent", "verify", "blocked", "suspended", "otp", "bank", "account", "password"]
        found = [kw for kw in keywords if kw in text.lower()]
        intelligence["suspiciousKeywords"] = found
        
        return intelligence