from typing import Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger
from app.ml.preprocessing import combine_ticket_text


class Predictor:
    def __init__(self, vectorizer=None, category_model=None, subcategory_model=None, priority_model=None):
        self.vectorizer = vectorizer
        self.category_model = category_model
        self.subcategory_model = subcategory_model
        self.priority_model = priority_model

    @property
    def is_ready(self) -> bool:
        return all([
            self.vectorizer is not None,
            self.category_model is not None,
            self.subcategory_model is not None,
            self.priority_model is not None,
        ])

    def predict(self, title: str, description: str) -> Dict[str, Any]:
        """
        Run in-memory prediction.
        Returns prediction dictionary with confidence score and review flag.
        """
        if not self.is_ready:
            logger.warning("ML models are not loaded. Returning heuristic fallback.")
            return self._heuristic_fallback(title, description)

        text = combine_ticket_text(title, description)
        vec = self.vectorizer.transform([text])

        # 1. Category Prediction + Confidence
        cat_probs = self.category_model.predict_proba(vec)[0]
        cat_idx = np.argmax(cat_probs)
        category = self.category_model.classes_[cat_idx]
        cat_confidence = float(cat_probs[cat_idx])

        # 2. Subcategory Prediction
        sub_probs = self.subcategory_model.predict_proba(vec)[0]
        sub_idx = np.argmax(sub_probs)
        subcategory = self.subcategory_model.classes_[sub_idx]

        # 3. Priority Prediction
        prio_probs = self.priority_model.predict_proba(vec)[0]
        prio_idx = np.argmax(prio_probs)
        priority = self.priority_model.classes_[prio_idx]

        # Department routing
        department = settings.CATEGORY_DEPARTMENT_MAP.get(category, "IT Helpdesk")

        # Confidence threshold check
        needs_review = cat_confidence < settings.CONFIDENCE_THRESHOLD

        return {
            "category": str(category),
            "subcategory": str(subcategory),
            "priority": str(priority).upper(),
            "department": str(department),
            "confidence": round(cat_confidence, 4),
            "needs_review": bool(needs_review),
        }

    def _heuristic_fallback(self, title: str, description: str) -> Dict[str, Any]:
        text = f"{title} {description}".lower()

        if any(w in text for w in ["vpn", "wifi", "internet", "network", "dns", "lan"]):
            cat = "Network"
            sub = "VPN" if "vpn" in text else ("WiFi" if "wifi" in text else "Connectivity")
            prio = "HIGH" if "vpn" in text else "MEDIUM"
        elif any(w in text for w in ["password", "login", "account", "mfa", "otp", "locked"]):
            cat = "Account & Access"
            sub = "Password Reset" if "password" in text else "Login Problem"
            prio = "MEDIUM"
        elif any(w in text for w in ["laptop", "screen", "keyboard", "mouse", "monitor", "printer"]):
            cat = "Hardware"
            sub = "Laptop" if "laptop" in text else "Peripherals"
            prio = "MEDIUM"
        elif any(w in text for w in ["server", "database", "down", "outage", "production", "crash"]):
            cat = "Server / Infrastructure"
            sub = "Server Down"
            prio = "CRITICAL"
        elif any(w in text for w in ["phishing", "virus", "malware", "ransomware", "hacked"]):
            cat = "Security"
            sub = "Malware" if "malware" in text else "Phishing"
            prio = "CRITICAL"
        elif any(w in text for w in ["outlook", "email", "mail", "mailbox"]):
            cat = "Email"
            sub = "Outlook Problem" if "outlook" in text else "Email Not Sending"
            prio = "MEDIUM"
        else:
            cat = "Software"
            sub = "Application Error"
            prio = "LOW"

        dept = settings.CATEGORY_DEPARTMENT_MAP.get(cat, "IT Helpdesk")
        return {
            "category": cat,
            "subcategory": sub,
            "priority": prio,
            "department": dept,
            "confidence": 0.50,
            "needs_review": True,
        }
