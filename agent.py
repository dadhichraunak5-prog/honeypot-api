from typing import List, Dict

class HoneyPotAgent:
    def __init__(self):
        self.personas = {
            "initial": ["Oh no! What's happening?", "I don't understand. Can you explain?", "Is there a problem with my account?"],
            "concerned": ["This sounds serious. What should I do?", "I'm worried. How do I fix this?", "Please help me understand."],
            "compliant": ["Okay, I want to help. What do you need?", "Should I click the link?", "Where do I send the information?"],
            "questioning": ["Is this the official website?", "Can I call the bank instead?", "How do I know this is real?"]
        }
    
    def generate_response(self, current_message: str, conversation_history: List, session_state: Dict, metadata: Dict) -> str:
        turn = session_state["turn_count"]
        text_lower = current_message.lower()
        
        # Early stage - confusion
        if turn <= 2:
            if "blocked" in text_lower or "suspended" in text_lower:
                return "Oh no! Why is my account being blocked? I haven't done anything wrong."
            elif "verify" in text_lower:
                return "Verify? What do I need to verify? Is there a problem?"
            return "I don't understand. What's this about?"
        
        # Middle stage - compliance
        elif turn <= 6:
            if "share" in text_lower or "send" in text_lower:
                return "Okay, but how do I share it? Should I reply here or go to a website?"
            elif "link" in text_lower or "click" in text_lower:
                return "I see a link. Is this the official bank website? It looks different from usual."
            elif "otp" in text_lower or "code" in text_lower:
                return "I got a code on my phone. Where should I enter it?"
            return "I want to help. What exactly do I need to do?"
        
        # Later stage - extract info
        elif turn <= 10:
            if "account" in text_lower:
                return "Which account? I have savings and current. Should I share both numbers?"
            elif "payment" in text_lower:
                return "How much do I need to pay? Can I pay through UPI or net banking?"
            elif "upi" in text_lower:
                return "My UPI ID? Let me check. Do you need my phone number too?"
            return "I'm trying my best. Can you send me your contact number so I can call?"
        
        # Final stage - slight suspicion
        else:
            return "I've been trying for a while. Are you sure this is legitimate? Maybe I should visit the bank branch."
    
    def get_persona_state(self, turn_count: int) -> str:
        if turn_count <= 2:
            return "initial"
        elif turn_count <= 6:
            return "concerned"
        elif turn_count <= 10:
            return "compliant"
        else:
            return "questioning"