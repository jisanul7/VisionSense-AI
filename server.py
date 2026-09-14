import io
import json
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from PIL import Image

app = FastAPI(title="VisionSense AI Core Cortex")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_KEY = os.getenv("SERVER_GEMINI_KEY")
client = genai.Client(api_key=SERVER_KEY) if SERVER_KEY else None

FUTURISTIC_PROMPT = """
You are the visual cortex of VisionSense AI, an advanced visual intelligence system.
Analyze the provided image with open-world visual recognition. Do not limit yourself to predefined categories.
Identify key focal elements: specific vehicles (exact make/model), apparel (garments, regional ethnic attire, formal wear), landmarks/architecture, gadgets, and food items.
Accurately identify true surface colors despite low light, shadows, or headlight glare.

For every primary entity identified, generate:
1. "label": Specific entity name (e.g. "Green Royal Enfield Classic 350", "Traditional Silk Kurta & Dhoti", "Victorian Architecture Façade").
2. "category": One of ["AUTOMOTIVE", "FASHION", "LOCATION", "PRODUCT", "FOOD"].
3. "color": Dominant visual color/hue.
4. "palette": Array of 3 dominant hex color codes [e.g. "#2E4F4F", "#0E8388", "#CBE4DE"].
5. "search_query": Clean shopping or web lookup query.
6. "box_2d": Normalized bounding box [ymin, xmin, ymax, xmax] scaled from 0 to 1000.
7. "insights": A short, intriguing 1-sentence analytical trivia or technical spec about this object.

Return strictly a valid JSON object matching:
{
  "summary": "Futuristic, concise 1-2 sentence executive summary of the scene.",
  "items": [
    {
      "label": "...",
      "category": "...",
      "color": "...",
      "palette": ["#...", "#...", "#..."],
      "search_query": "...",
      "box_2d": [ymin, xmin, ymax, xmax],
      "insights": "..."
    }
  ]
}
"""


@app.get("/")
def health_check():
    return {"status": "online", "cortex": "operational"}


@app.post("/analyze")
async def analyze_visual_stream(file: UploadFile = File(...)):
    global client
    if not client:
        key = os.getenv("SERVER_GEMINI_KEY")
        if key:
            client = genai.Client(api_key=key)
        else:
            raise HTTPException(
                status_code=500,
                detail="SERVER_GEMINI_KEY secret is not configured on the server."
            )

    try:
        data = await file.read()
        image = Image.open(io.BytesIO(data)).convert("RGB")

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[image, FUTURISTIC_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.15,
            ),
        )

        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))