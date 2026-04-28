import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.request_models import AskRequest, AskResponse, FeedbackRequest
from services.llm_service import LLMService
from services.behavior_engine import behavior_engine
from services.db_service import supabase
from utils.logger import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Research Assistant ML Service",
    description="Production-ready ML microservice for self-evolving AI research assistant",
    version="1.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    # Optional: extract user_id from query or profile if available for behavior learning
    # For now, we assume user_profile might be passed as part of a session
    logger.info(f"Received query: {request.query}")
    
    try:
        # 1. Extract user_id
        user_id = request.user_id or "default_user"
        
        # 2. Get learned preferences from behavior engine
        learned_preferences = behavior_engine.get_user_preferences(user_id)
        incoming_preferences = request.user_profile.preferences
        
        # 3. Merge logic: Learned preferences OVERRIDE incoming ones if they exist
        if learned_preferences:
            final_preferences = learned_preferences
            logger.info(f"Learned preferences found for {user_id}. Overriding incoming preferences.")
        else:
            final_preferences = incoming_preferences
            logger.info(f"No learned preferences for {user_id}. Using incoming preferences.")
            
        # Update the profile with final preferences
        final_profile = request.user_profile.copy()
        final_profile.preferences = final_preferences
        
        # 4. Detailed Logging for debugging
        logger.info(f"--- PREFERENCE SUMMARY FOR {user_id} ---")
        logger.info(f"Incoming: {incoming_preferences}")
        logger.info(f"Learned:  {learned_preferences}")
        logger.info(f"Final:    {final_preferences}")
        logger.info(f"---------------------------------------")
        
        # 5. Generate answer using final profile
        answer, response_type = await llm_service.get_answer(
            request.query, 
            final_profile
        )
        
        recommendations = llm_service.get_static_recommendations()
        
        logger.info(f"Successfully generated response of type: {response_type}")
        
        return AskResponse(
            answer=answer,
            type=response_type,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Receives feedback on a response, stores it in Supabase, and updates behavior engine.
    """
    logger.info(f"Received feedback from {request.user_id} for type {request.type}: Liked={request.liked}")
    
    try:
        # 1. Store data in Supabase
        interaction_data = {
            "user_id": request.user_id,
            "query": request.query,
            "response_type": request.type,
            "liked": request.liked
        }
        supabase.table("interactions").insert(interaction_data).execute()
        
        # 2. Update behavior engine
        updated_scores = behavior_engine.process_feedback(request)
        updated_preferences = behavior_engine.get_user_preferences(request.user_id)
        
        return {
            "status": "saved",
            "updated_preferences": {
                "scores": updated_scores,
                "derived_preferences": updated_preferences
            }
        }
    except Exception as e:
        logger.error(f"Failed to record feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
