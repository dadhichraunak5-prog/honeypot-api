from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
from datetime import datetime
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Honeypot API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("API_KEY", "honeypot-secret-key-2024")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Import components (after app is created)
try:
    from agent import HoneyPotAgent
    from detector import ScamDetector
    from intelligence import IntelligenceExtractor

    scam_detector = ScamDetector()
    intelligence_extractor = IntelligenceExtractor()
    agent = HoneyPotAgent()
    logger.info("✅ All components loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading components: {e}")
    scam_detector = None
    intelligence_extractor = None
    agent = None

# Store sessions
sessions = {}

# Models
class Message(BaseModel):
    sender: str
    text: str
    timestamp: int

class IncomingRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Dict] = {}

class AgentResponse(BaseModel):
    status: str
    reply: str

# Helper functions
def create_session(session_id):
    return {
        "session_id": session_id,
        "scam_detected": False,
        "agent_activated": False,
        "ended": False,
        "history": [],
        "turn_count": 0,
        "intelligence": {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": []
        },
        "agent_notes": "",
        "created_at": datetime.now().isoformat()
    }

def should_end(session_data):
    turns = session_data["turn_count"]
    intel = session_data["intelligence"]
    intel_count = sum(len(v) for k, v in intel.items() if isinstance(v, list) and k != "suspiciousKeywords")

    if turns >= 20:
        return True
    if turns >= 8 and intel_count >= 3:
        return True
    if turns >= 12 and intel_count >= 2:
        return True
    return False

def send_callback(session_data):
    payload = {
        "sessionId": session_data["session_id"],
        "scamDetected": session_data["scam_detected"],
        "totalMessagesExchanged": session_data["turn_count"],
        "extractedIntelligence": session_data["intelligence"],
        "agentNotes": session_data["agent_notes"]
    }

    try:
        response = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=10)
        logger.info(f"✅ Callback sent: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"❌ Callback failed: {e}")
        return False

# API Endpoints
@app.get("/")
def home():
    return {
        "service": "Honeypot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "message": "/api/message"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sessions": len(sessions),
        "components": {
            "detector": scam_detector is not None,
            "intelligence": intelligence_extractor is not None,
            "agent": agent is not None
        }
    }

@app.post("/api/message", response_model=AgentResponse)
async def handle_message(request: IncomingRequest, x_api_key: str = Header(..., alias="x-api-key")):
    try:
        # Validate API key
        if x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check if components are loaded
        if not all([scam_detector, intelligence_extractor, agent]):
            raise HTTPException(status_code=500, detail="Components not loaded properly")

        session_id = request.sessionId

        # Create session if new
        if session_id not in sessions:
            sessions[session_id] = create_session(session_id)
            logger.info(f"🆕 New session: {session_id}")

        session = sessions[session_id]

        # If the session already ended, don't process further and don't
        # fire another callback
        if session["ended"]:
            return AgentResponse(status="ended", reply="This conversation has ended.")

        # Update history
        all_messages = request.conversationHistory + [request.message]
        session["history"] = all_messages
        session["turn_count"] = len([m for m in all_messages if m.sender == "scammer"])

        # Detect scam
        is_scam, confidence, scam_type = scam_detector.detect(
            request.message.text,
            request.conversationHistory,
            request.metadata
        )

        # Activate agent
        if is_scam and not session["scam_detected"]:
            session["scam_detected"] = True
            session["agent_activated"] = True
            session["agent_notes"] = f"Scam type: {scam_type}, Confidence: {confidence:.0%}"
            logger.info(f"🚨 Scam detected: {scam_type}")

        # Extract intelligence
        extracted = intelligence_extractor.extract_from_message(request.message.text)
        for key, values in extracted.items():
            if key in session["intelligence"]:
                session["intelligence"][key].extend(values)
                session["intelligence"][key] = list(set(session["intelligence"][key]))

        # Generate response
        if session["agent_activated"]:
            reply = agent.generate_response(
                request.message.text,
                request.conversationHistory,
                session,
                request.metadata
            )

            # Check if should end (fix: guard so we only fire the callback
            # once, then mark session ended so future messages short-circuit
            # above)
            if should_end(session):
                session["ended"] = True
                logger.info(f"🏁 Ending session: {session_id}")
                send_callback(session)
        else:
            reply = "I'm sorry, I don't understand."

        return AgentResponse(status="success", reply=reply)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn app:app --reload
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
