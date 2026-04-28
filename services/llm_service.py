import os
import re
from mistralai import Mistral
from dotenv import load_dotenv
from utils.logger import logger
from models.request_models import UserProfile
import services.style_engine as style_engine

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = "mistral-small-latest"

class LLMService:
    def __init__(self):
        if not MISTRAL_API_KEY:
            logger.error("MISTRAL_API_KEY not found in environment variables.")
        self.client = Mistral(api_key=MISTRAL_API_KEY)

    def generate_response(self, system_prompt: str, user_query: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        try:
            chat_response = self.client.chat.complete(
                model=MODEL,
                messages=messages,
            )
            return chat_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            raise e

    def enforce_style(self, response: str, config: dict) -> str:
        """
        Deterministic enforcement layer to ensure the output matches strict requirements.
        """
        processed_response = response.strip()

        # 1. CODE-FIRST ENFORCEMENT
        if config.get("require_code_first"):
            if not processed_response.startswith("```"):
                # extract code block
                code_blocks = re.findall(r"```[\s\S]*?```", processed_response)
                if code_blocks:
                    # Prepend first code block to the top
                    processed_response = code_blocks[0] + "\n\n" + processed_response
                else:
                    logger.warning("Code-first required but no code block found in response.")

        # 2. SHORT ENFORCEMENT
        if "max_lines" in config:
            lines = processed_response.split("\n")
            if len(lines) > config["max_lines"]:
                processed_response = "\n".join(lines[:config["max_lines"]])
                logger.info(f"Response truncated to {config['max_lines']} lines.")

        return processed_response

    async def get_answer(self, query: str, user_profile: UserProfile):
        # Using the new signature as requested
        style_config = style_engine.get_style_config(
            user_profile.preferences,
            user_profile.level
        )
        
        # DEBUG LOGS (as requested)
        print("PREFERENCES:", user_profile.preferences)
        print("STYLE CONFIG:", style_config)
        
        system_prompt = f"""
You MUST follow ALL rules strictly. If you violate them, the response is invalid.

### SYSTEM RULES:
- If 'short' is active → limit response to maximum {style_config.get('max_lines', 15)} lines.
- If 'code' is active → output code block FIRST before any explanation.
- If 'beginner' is active → use very simple words, no jargon.

### TASK:
- User Level: {user_profile.level}
- Target Type: {style_config['type']}
- Preferences: {", ".join(user_profile.preferences)}

Answer the query accordingly using Markdown.
        """
        
        try:
            logger.info(f"Sending request to Mistral for style: {style_config['type']}")
            raw_answer = self.generate_response(system_prompt, query)
            
            # Apply deterministic enforcement layer
            final_answer = self.enforce_style(raw_answer, style_config)
            
            return final_answer, style_config['type']
            
        except Exception as e:
            logger.error(f"Error calling Mistral API: {str(e)}")
            fallback_text = "I'm currently having trouble connecting to my brain. Here is a simplified answer: " + query
            return fallback_text, "explanation"

    def get_static_recommendations(self) -> list:
        return [
            "Explore documentation for advanced patterns",
            "Try implementing a retry mechanism",
            "Check out our vector search guide"
        ]
