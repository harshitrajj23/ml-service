from utils.logger import logger
from models.request_models import FeedbackRequest, UserProfile
from typing import Dict, List
from services.db_service import supabase

class BehaviorEngine:
    def process_feedback(self, feedback: FeedbackRequest) -> Dict[str, int]:
        """
        Feedback is stored directly in Supabase by the API handler.
        This method can optionally return current scores by fetching from DB.
        """
        # For compatibility with app.py return expectation, we compute scores from DB
        return self.get_user_scores(feedback.user_id)

    def get_user_scores(self, user_id: str) -> Dict[str, int]:
        """
        Fetches history from Supabase and computes current scores.
        """
        try:
            data = supabase.table("interactions").select("*").eq("user_id", user_id).execute()
            records = data.data

            scores = {
                "code": 0,
                "short": 0,
                "explanation": 0
            }

            for row in records:
                # Map response_type to internal keys
                if row["response_type"] == "code-heavy":
                    key = "code"
                elif row["response_type"] == "short":
                    key = "short"
                else:
                    key = "explanation"

                if row["liked"]:
                    scores[key] += 1
                else:
                    scores[key] -= 1
            
            return scores
        except Exception as e:
            logger.error(f"Error fetching scores from Supabase: {str(e)}")
            return {"code": 0, "short": 0, "explanation": 0}

    def get_user_preferences(self, user_id: str) -> List[str]:
        """
        Derives preferences array dynamically from Supabase interaction history.
        """
        scores = self.get_user_scores(user_id)
        preferences = []

        # Logic per user requirements: threshold > 1
        if scores["code"] > 1:
            preferences.append("code")

        if scores["short"] > 1:
            preferences.append("short")

        logger.info(f"Derived preferences for {user_id} from DB: {preferences}")
        return preferences

behavior_engine = BehaviorEngine()
