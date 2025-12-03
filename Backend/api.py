





from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
from supabase import create_client


from genetic_algorithm import run_timetable_generation



app = FastAPI(title="Timetable Generation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://nep-timetable.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



generation_status = {
    "is_running": False,
    "last_generated": None,
    "message": ""
}

@app.get("/")
def read_root():
    return {"message": "Timetable Generation API is running"}

@app.post("/generate-timetable")
async def generate_timetable():
    global generation_status
    
    if generation_status["is_running"]:
        raise HTTPException(
            status_code=409, 
            detail="Timetable generation is already in progress"
        )
    
    try:
        generation_status["is_running"] = True
        generation_status["message"] = "Generation started..."
        
 
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, run_timetable_generation)
        
        if result == "SUCCESS":
            generation_status["is_running"] = False
            generation_status["last_generated"] = datetime.now().isoformat()
            generation_status["message"] = "Timetable generated successfully"
            
            return {
                "status": "success", 
                "message": "Timetable generated successfully",
                "timestamp": generation_status["last_generated"]
            }
        else:
            generation_status["is_running"] = False
            generation_status["message"] = "Generation failed"
            raise HTTPException(status_code=500, detail="Timetable generation failed")
            
    except Exception as e:
        generation_status["is_running"] = False
        generation_status["message"] = f"Error: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generation-status")
def get_generation_status():
    return generation_status

@app.get("/timetable")
async def get_timetable():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = supabase.table('final_timetable').select('*').order('Day').order('Time').execute()

        
        return {
            "status": "success",
            "data": result.data,
            "count": len(result.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timetable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
