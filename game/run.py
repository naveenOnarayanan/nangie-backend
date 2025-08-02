from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import time
import threading
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

# Game state
game_state = {
    'current_question': 0,
    'game_active': False,
    'question_start_time': None,
    'question_time_limit': 30,  # seconds
    'intermission_start_time': None,
    'intermission_time_limit': 30,  # seconds between questions
    'teams': {},
    'scores': {},
    'answers_locked': False,
    'in_intermission': False,
    'show_answer': False
}

# Trivia questions - Custom wedding questions for Navneet & Angie
# Total: 15 questions × 30 seconds each + 14 intermissions × 30 seconds = 14.5 minutes
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
        'correct': 1,  # You can update this with the real answer
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
    },
    {
        'category': 'Vietnamese Language',
        'question': 'How do you say "Thank you" in Vietnamese?',
        'options': ['Xin chào', 'Cảm ơn', 'Tạm biệt', 'Xin lỗi'],
        'correct': 1,
        'points': 200
    },
    {
        'category': 'Indian Traditions',
        'question': 'In traditional Indian weddings, what do couples walk around during the ceremony?',
        'options': ['A tree', 'Sacred fire', 'Temple', 'Altar'],
        'correct': 1,
        'points': 200
    },
    {
        'category': 'Canadian Geography',
        'question': 'Which province is known for its maple syrup production?',
        'options': ['Ontario', 'Quebec', 'British Columbia', 'Alberta'],
        'correct': 1,
        'points': 200
    },
    {
        'category': 'About the Couple',
        'question': 'Based on the ceremony schedule, who is officiating Navneet and Angie\'s wedding?',
        'options': ['Navneet', 'Naveen', 'Edward', 'Xavier'],
        'correct': 1,
        'points': 250
    },
    {
        'category': 'Love & Marriage',
        'question': 'According to the wedding schedule, what ceremony happens BEFORE the vows on July 30th?',
        'options': ['Tea Ceremony', 'Mallu Ceremony', 'Ring Exchange', 'Photo Session'],
        'correct': 1,
        'points': 300
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/admin')
def admin():
    return render_template('admin.html')

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/api/register_team', methods=['POST'])
def register_team():
    data = request.json
    team_name = data.get('team_name', '').strip()
    
    if not team_name:
        return jsonify({'success': False, 'message': 'Team name required'})
    
    if team_name in game_state['teams']:
        return jsonify({'success': False, 'message': 'Team name already taken'})
    
    team_id = len(game_state['teams']) + 1
    game_state['teams'][team_name] = {
        'id': team_id,
        'name': team_name,
        'joined_at': datetime.now().isoformat()
    }
    game_state['scores'][team_name] = 0
    
    return jsonify({'success': True, 'team_id': team_id, 'team_name': team_name})

@app.route('/api/game_status')
def game_status():
    current_q = None
    time_remaining = 0
    intermission_time = 0
    
    if game_state['in_intermission']:
        # During intermission between questions
        if game_state['intermission_start_time']:
            elapsed = time.time() - game_state['intermission_start_time']
            intermission_time = max(0, game_state['intermission_time_limit'] - elapsed)
            
            # Auto-advance to next question when intermission ends
            if intermission_time <= 0:
                game_state['in_intermission'] = False
                game_state['show_answer'] = False
                game_state['current_question'] += 1
                if game_state['current_question'] >= len(trivia_questions):
                    game_state['game_active'] = False
    
    elif game_state['game_active'] and game_state['current_question'] < len(trivia_questions):
        current_q = trivia_questions[game_state['current_question']].copy()
        
        # Include correct answer if we're showing the answer
        if not game_state['show_answer']:
            current_q.pop('correct', None)
        
        if game_state['question_start_time']:
            elapsed = time.time() - game_state['question_start_time']
            time_remaining = max(0, game_state['question_time_limit'] - elapsed)
            
            # Auto-lock answers when time runs out
            if time_remaining <= 0 and not game_state['answers_locked']:
                game_state['answers_locked'] = True
    
    return jsonify({
        'game_active': game_state['game_active'],
        'current_question': game_state['current_question'],
        'total_questions': len(trivia_questions),
        'question': current_q,
        'time_remaining': time_remaining,
        'intermission_time': intermission_time,
        'in_intermission': game_state['in_intermission'],
        'show_answer': game_state['show_answer'],
        'answers_locked': game_state['answers_locked'],
        'teams_count': len(game_state['teams'])
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    if not game_state['game_active'] or game_state['answers_locked']:
        return jsonify({'success': False, 'message': 'Answers are locked'})
    
    data = request.json
    team_name = data.get('team_name')
    answer = data.get('answer')
    
    if team_name not in game_state['teams']:
        return jsonify({'success': False, 'message': 'Team not registered'})
    
    # Store answer (you might want to store these for review)
    if 'current_answers' not in game_state:
        game_state['current_answers'] = {}
    
    game_state['current_answers'][team_name] = {
        'answer': answer,
        'timestamp': time.time()
    }
    
    return jsonify({'success': True, 'message': 'Answer submitted'})

@app.route('/api/start_question', methods=['POST'])
def start_question():
    if game_state['current_question'] >= len(trivia_questions):
        return jsonify({'success': False, 'message': 'No more questions'})
    
    game_state['game_active'] = True
    game_state['question_start_time'] = time.time()
    game_state['answers_locked'] = False
    game_state['in_intermission'] = False
    game_state['show_answer'] = False
    game_state['current_answers'] = {}
    
    return jsonify({'success': True})

@app.route('/api/show_answer', methods=['POST'])
def show_answer():
    """Show the correct answer and calculate scores"""
    if 'current_answers' in game_state and game_state['current_question'] < len(trivia_questions):
        correct_answer = trivia_questions[game_state['current_question']]['correct']
        points = trivia_questions[game_state['current_question']]['points']
        
        # Calculate scores for current question
        correct_teams = []
        for team_name, answer_data in game_state['current_answers'].items():
            if answer_data['answer'] == correct_answer:
                game_state['scores'][team_name] += points
                correct_teams.append(team_name)
    
    game_state['answers_locked'] = True
    game_state['show_answer'] = True
    
    return jsonify({'success': True, 'correct_teams': correct_teams if 'correct_teams' in locals() else []})

@app.route('/api/start_intermission', methods=['POST'])
def start_intermission():
    """Start the 30-second intermission before next question"""
    game_state['in_intermission'] = True
    game_state['intermission_start_time'] = time.time()
    
    return jsonify({'success': True})

@app.route('/api/next_question', methods=['POST'])
def next_question():
    """Move to next question immediately (skip intermission)"""
    game_state['current_question'] += 1
    game_state['answers_locked'] = True
    game_state['in_intermission'] = False
    game_state['show_answer'] = False
    
    if game_state['current_question'] >= len(trivia_questions):
        game_state['game_active'] = False
    
    return jsonify({'success': True})

@app.route('/api/scores')
def get_scores():
    sorted_scores = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)
    return jsonify({'scores': sorted_scores})

@app.route('/api/reset_game', methods=['POST'])
def reset_game():
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
    return jsonify({'success': True})

@app.route('/game/qr')
def generate_qr():
    # Get the local IP address for the QR code
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Create QR code pointing to the game interface
    qr_url = f"http://{local_ip}:8090/game"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('qr.html', qr_image=img_str, qr_url=qr_url)

if __name__ == '__main__':
    # Create templates directory and files
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # We'll create the HTML templates in separate artifacts
    print("Starting Wedding Trivia Server...")
    print("Visit http://localhost:8090/qr to get the QR code for teams")
    print("Visit http://localhost:8090/admin to control the game")
    
    app.run(host='0.0.0.0', port=8090, debug=True)