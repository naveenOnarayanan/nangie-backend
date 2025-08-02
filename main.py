# Your existing imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from contextlib import contextmanager
import os
import uvicorn
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import json

# Additional imports for game
import time
import qrcode
import io
import base64
import socket
from datetime import datetime

# Load environment variables
load_dotenv()

# CREATE THE APP INSTANCE FIRST
app = FastAPI()

# Your existing headers and middleware
HEADERS = [
    "accessCode",
    "maxGuests",
    "partyName",
    "confirmedGuests",
    "phoneNumber",
    "emailAddress",
    "rsvpAsk",
    "dietaryRestrictions",
    "hotelAccommodations",
    "questions",
    "rawNames",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game templates setup
game_templates = Jinja2Templates(directory="game/templates")

# ==================== TRIVIA GAME STATE ====================
game_state = {
    'current_question': 0,
    'game_active': False,
    'question_start_time': None,
    'question_time_limit': 30,
    'intermission_start_time': None,
    'intermission_time_limit': 30,
    'teams': {},
    'scores': {},
    'answers_locked': False,
    'in_intermission': False,
    'show_answer': False
}

# Complete trivia questions with all 15 questions
trivia_questions = [
    # Round 1: Culture Club
    {
        'category': 'Culture Club - Vietnam',
        'question': 'What is the name of the traditional Vietnamese dress worn at weddings and formal events?',
        'options': ['Kimono', 'Ao Dai', 'Hanbok', 'Sari'],
        'correct': 1,
        'points': 100
    },
    {
        'category': 'Culture Club - India',
        'question': 'What spice is commonly used in Indian chai?',
        'options': ['Cumin', 'Paprika', 'Cardamom', 'Ginger'],
        'correct': 2,
        'points': 100
    },
    {
        'category': 'Culture Club - Canada',
        'question': 'What sweet treat is made from snow and maple syrup in Canada?',
        'options': ['Beaver Tail', 'Maple Taffy', 'Sugar Pancake', 'Frozen Syrup Pop'],
        'correct': 1,
        'points': 100
    },
    {
        'category': 'Culture Club - USA',
        'question': 'Which U.S. state has the largest Vietnamese population?',
        'options': ['Texas', 'New York', 'Washington', 'California'],
        'correct': 3,
        'points': 100
    },
    {
        'category': 'Culture Club - Geography',
        'question': 'Put these in order of population (most to least): India, Vietnam, Canada',
        'options': ['India > Canada > Vietnam', 'Vietnam > India > Canada', 'India > Vietnam > Canada', 'Canada > India > Vietnam'],
        'correct': 2,
        'points': 150
    },
    # Round 2: Nangie or Nah?
    {
        'category': 'Nangie or Nah?',
        'question': 'Who had a pet dog named Sushi growing up?',
        'options': ['Navneet', 'Angie', 'Both', 'Neither'],
        'correct': 1,
        'points': 150
    },
    {
        'category': 'Nangie or Nah?',
        'question': 'Who was once part of a competitive dance team?',
        'options': ['Navneet', 'Angie', 'Both', 'Neither'],
        'correct': 3,
        'points': 150
    },
    {
        'category': 'Nangie or Nah?',
        'question': 'Who owns more tech gadgets?',
        'options': ['Navneet', 'Angie', 'Both', 'Sushi'],
        'correct': 0,
        'points': 150
    },
    {
        'category': 'Nangie or Nah?',
        'question': 'Who is more likely to cry during a Disney movie?',
        'options': ['Navneet', 'Angie', 'Both', 'Neither'],
        'correct': 1,
        'points': 150
    },
    {
        'category': 'Nangie or Nah?',
        'question': 'Who said "I love you" first?',
        'options': ['Navneet', 'Angie', 'Both at the same time', 'No one remembers'],
        'correct': 1,  # Update with real answer
        'points': 200
    },
    # Round 3: Wedding Whirlwind
    {
        'category': 'Wedding Whirlwind',
        'question': 'What flower is traditionally thrown at Indian weddings for blessings?',
        'options': ['Lotus', 'Jasmine', 'Marigold', 'Rose'],
        'correct': 3,
        'points': 200
    },
    {
        'category': 'Wedding Whirlwind',
        'question': 'Which of these fruits is commonly found in Vietnamese wedding baskets?',
        'options': ['Apple', 'Mango', 'Blueberry', 'Kiwi'],
        'correct': 1,
        'points': 200
    },
    {
        'category': 'Wedding Whirlwind',
        'question': 'In which language is "I love you" said as "Anh yêu em"?',
        'options': ['Tagalog', 'Thai', 'Vietnamese', 'Lao'],
        'correct': 2,
        'points': 200
    },
    {
        'category': 'Wedding Whirlwind',
        'question': 'Which Bollywood movie is famously about a big Indian wedding?',
        'options': ['Lagaan', 'Monsoon Wedding', 'Slumdog Millionaire', 'Chennai Express'],
        'correct': 1,
        'points': 250
    },
    {
        'category': 'Wedding Whirlwind',
        'question': 'What does "Namaste" literally mean?',
        'options': ['Hello', 'I respect you', 'I bow to you', 'Let\'s eat'],
        'correct': 2,
        'points': 250
    }
]

# ==================== YOUR EXISTING RSVP MODELS ====================
class UserUpdate(BaseModel):
    """Model for user update data"""
    model_config = ConfigDict(extra="allow")
    data: Dict[str, str]

# ==================== GAME MODELS ====================
class TeamRegistration(BaseModel):
    team_name: str

class AnswerSubmission(BaseModel):
    team_name: str
    answer: int

# ==================== YOUR EXISTING RSVP CODE ====================
# (Keep all your existing Google Sheets functions here)
_sheets_service = None

@contextmanager
def get_sheets_service():
    # Your existing implementation
    pass

def find_user_row(service, spreadsheet_id: str, user_id: str) -> Optional[int]:
    # Your existing implementation
    pass

# ==================== YOUR EXISTING RSVP ROUTES ====================
@app.get("/user/{user_id}")
async def get_user(user_id: str) -> Dict[str, str]:
    # Your existing implementation
    pass

@app.post("/update/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate) -> Dict[str, str]:
    # Your existing implementation
    pass

# ==================== NEW GAME ROUTES ====================
@app.get("/game", response_class=HTMLResponse)
async def game_home(request: Request):
    """Game home page"""
    return game_templates.TemplateResponse("index.html", {"request": request})

@app.get("/game/play", response_class=HTMLResponse)
async def game_play(request: Request):
    """Team game interface"""
    return game_templates.TemplateResponse("game.html", {"request": request})

@app.get("/game/admin", response_class=HTMLResponse)
async def game_admin(request: Request):
    """Game admin interface"""
    return game_templates.TemplateResponse("admin.html", {"request": request})

@app.get("/game/qr", response_class=HTMLResponse)
async def game_qr(request: Request):
    """QR code for teams to join"""
    # Use request info to build URL
    host = request.headers.get("host", "localhost:8000")
    qr_url = f"http://{host}/game/play"
    
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return game_templates.TemplateResponse("qr.html", {
            "request": request, 
            "qr_image": img_str, 
            "qr_url": qr_url
        })
    except ImportError:
        return game_templates.TemplateResponse("qr.html", {
            "request": request, 
            "qr_image": None, 
            "qr_url": qr_url
        })

# ==================== GAME API ROUTES ====================
@app.post("/game/api/register_team")
async def register_team(team_data: TeamRegistration):
    """Register a new team"""
    team_name = team_data.team_name.strip()
    
    if not team_name:
        raise HTTPException(status_code=400, detail="Team name required")
    
    if team_name in game_state['teams']:
        raise HTTPException(status_code=400, detail="Team name already taken")
    
    team_id = len(game_state['teams']) + 1
    game_state['teams'][team_name] = {
        'id': team_id,
        'name': team_name,
        'joined_at': datetime.now().isoformat()
    }
    game_state['scores'][team_name] = 0
    
    return {'success': True, 'team_id': team_id, 'team_name': team_name}

@app.get("/game/api/game_status")
async def game_status():
    """Get current game status with auto score reveal"""
    current_q = None
    time_remaining = 0
    intermission_time = 0
    
    if game_state['in_intermission']:
        if game_state['intermission_start_time']:
            elapsed = time.time() - game_state['intermission_start_time']
            intermission_time = max(0, game_state['intermission_time_limit'] - elapsed)
            
            if intermission_time <= 0:
                game_state['in_intermission'] = False
                game_state['show_answer'] = False
                game_state['current_question'] += 1
                if game_state['current_question'] >= len(trivia_questions):
                    game_state['game_active'] = False
    
    elif game_state['game_active'] and game_state['current_question'] < len(trivia_questions):
        current_q = trivia_questions[game_state['current_question']].copy()
        
        if game_state['question_start_time']:
            elapsed = time.time() - game_state['question_start_time']
            time_remaining = max(0, game_state['question_time_limit'] - elapsed)
            
            # AUTO-SHOW ANSWER WHEN TIME HITS ZERO
            if time_remaining <= 0 and not game_state['answers_locked']:
                game_state['answers_locked'] = True
                game_state['show_answer'] = True
                
                # Auto-calculate scores when time expires
                if 'current_answers' in game_state:
                    correct_answer = trivia_questions[game_state['current_question']]['correct']
                    points = trivia_questions[game_state['current_question']]['points']
                    
                    for team_name, answer_data in game_state['current_answers'].items():
                        if answer_data['answer'] == correct_answer:
                            game_state['scores'][team_name] += points
        
        # Include correct answer if showing answer
        if not game_state['show_answer']:
            current_q.pop('correct', None)
    
    # Get current scores for chart display
    sorted_scores = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)
    
    return {
        'game_active': game_state['game_active'],
        'current_question': game_state['current_question'],
        'total_questions': len(trivia_questions),
        'question': current_q,
        'time_remaining': time_remaining,
        'intermission_time': intermission_time,
        'in_intermission': game_state['in_intermission'],
        'show_answer': game_state['show_answer'],
        'answers_locked': game_state['answers_locked'],
        'teams_count': len(game_state['teams']),
        'current_scores': sorted_scores  # Add scores to every status response
    }

@app.get("/game/papa", response_class=HTMLResponse)
async def game_projector(request: Request):
    """Projector display for questions"""
    return game_templates.TemplateResponse("planes.html", {"request": request})

@app.post("/game/api/submit_answer")
async def submit_answer(answer_data: AnswerSubmission):
    """Submit team answer"""
    if not game_state['game_active'] or game_state['answers_locked']:
        raise HTTPException(status_code=400, detail="Answers are locked")
    
    team_name = answer_data.team_name
    answer = answer_data.answer
    
    if team_name not in game_state['teams']:
        raise HTTPException(status_code=400, detail="Team not registered")
    
    if 'current_answers' not in game_state:
        game_state['current_answers'] = {}
    
    game_state['current_answers'][team_name] = {
        'answer': answer,
        'timestamp': time.time()
    }
    
    return {'success': True, 'message': 'Answer submitted'}

@app.post("/game/api/start_question")
async def start_question():
    """Start the current question"""
    if game_state['current_question'] >= len(trivia_questions):
        raise HTTPException(status_code=400, detail="No more questions")
    
    # Start the current question
    game_state['game_active'] = True
    game_state['question_start_time'] = time.time()
    game_state['answers_locked'] = False
    game_state['in_intermission'] = False
    game_state['show_answer'] = False
    game_state['current_answers'] = {}
    
    return {
        'success': True, 
        'current_question': game_state['current_question'],
        'message': f"Question {game_state['current_question'] + 1} started!"
    }

@app.post("/game/api/show_answer")
async def show_answer():
    """Show correct answer and calculate scores"""
    correct_teams = []
    
    if 'current_answers' in game_state and game_state['current_question'] < len(trivia_questions):
        correct_answer = trivia_questions[game_state['current_question']]['correct']
        points = trivia_questions[game_state['current_question']]['points']
        
        # Calculate scores
        for team_name, answer_data in game_state['current_answers'].items():
            if answer_data['answer'] == correct_answer:
                game_state['scores'][team_name] += points
                correct_teams.append(team_name)
    
    # Lock answers and show correct answer
    game_state['answers_locked'] = True
    game_state['show_answer'] = True
    
    # Get current scores for response
    sorted_scores = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)
    
    return {
        'success': True, 
        'correct_teams': correct_teams,
        'current_scores': sorted_scores[:5]  # Top 5 scores
    }

@app.post("/game/api/next_question")
async def next_question():
    """Move to next question"""
    # Move to next question
    game_state['current_question'] += 1
    
    # Reset states
    game_state['game_active'] = False
    game_state['answers_locked'] = False
    game_state['in_intermission'] = False
    game_state['show_answer'] = False
    
    # Check if game is complete
    if game_state['current_question'] >= len(trivia_questions):
        game_state['game_active'] = False
        return {
            'success': True, 
            'current_question': game_state['current_question'],
            'game_complete': True,
            'message': 'Game completed!'
        }
    
    return {
        'success': True, 
        'current_question': game_state['current_question'],
        'game_complete': False,
        'message': f'Ready for question {game_state["current_question"] + 1}'
    }

@app.get("/game/projector", response_class=HTMLResponse)
async def game_projector(request: Request):
    """Projector display for questions"""
    return game_templates.TemplateResponse("projector.html", {"request": request})

@app.get("/game/api/scores")
async def get_scores():
    """Get current scores"""
    sorted_scores = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)
    return {'scores': sorted_scores}

@app.post("/game/api/reset_game")
async def reset_game():
    """Reset entire game"""
    game_state.update({
        'current_question': 0,
        'game_active': False,
        'question_start_time': None,
        'intermission_start_time': None,
        'teams': {},
        'scores': {},
        'answers_locked': False,
        'in_intermission': False,
        'show_answer': False,
        'current_answers': {}
    })
    return {'success': True}

# ==================== YOUR EXISTING CLEANUP AND SERVER START ====================
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    global _sheets_service
    if _sheets_service:
        _sheets_service.close()
        _sheets_service = None

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)