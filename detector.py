import re
from typing import List, Tuple, Dict

class ScamDetector:
    def __init__(self):
        # Keywords that indicate scams
        self.scam_patterns = {
            "bank_fraud": {
                "keywords": ["bank", "account", "blocked", "suspended", "verify", "kyc"],
                "weight": 2.0
            },
            "upi_fraud": {
                "keywords": ["upi", "paytm", "phonepe", "gpay", "payment"],
                "weight": 2.5
            },
            "urgency": {
                "keywords": ["urgent", "immediately", "now", "today", "hurry"],
                "weight": 1.5
            },
            "threats": {
                "keywords": ["blocked", "suspended", "legal", "police", "action"],
                "weight": 2.0
            },
            "credentials": {
                "keywords": ["password", "otp", "cvv", "pin", "code"],
                "weight": 3.0
            }
        }
    
    def detect(self, message: str, history: List, metadata: Dict) -> Tuple[bool, float, str]:
        text_lower = message.lower()
        score = 0.0
        detected_types = []
        
        # Check for scam keywords
        for scam_type, pattern in self.scam_patterns.items():
            matches = sum(1 for keyword in pattern["keywords"] if keyword in text_lower)
            if matches > 0:
                score += matches * pattern["weight"]
                detected_types.append((scam_type, matches))
        
        # Check for URLs
        if re.findall(r'http[s]?://[^\s]+', message):
            score += 3.0
        
        # Check for phone numbers
        if re.findall(r'\+?\d{10,13}', message):
            score += 1.5
        
        # Check for email/UPI
        if re.findall(r'[\w.-]+@[\w.-]+', message):
            score += 2.0
        
        # Check conversation history
        if len(history) > 0:
            if any(word in text_lower for word in ["share", "send", "provide"]):
                score += 2.0
        
        # Calculate confidence
        confidence = min(score / 20.0, 1.0)
        
        # Determine scam type
        scam_type = "unknown"
        if detected_types:
            detected_types.sort(key=lambda x: x, reverse=True)
            scam_type = detected_types
        
        # Is it a scam?
        is_scam = confidence >= 0.3
        
        return is_scam, confidence, scam_type