import os
import json
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# Load environment variables
load_dotenv()

# Configure the Google AI API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Set up the model configuration
MODEL = "gemini-2.0-flash"  # Using Gemini 2.0 Flash as specified

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-conversation-secret-key'
socketio = SocketIO(app)

def setup_model(name, system_instruction, temperature=0.7):
    """Set up an AI model with a specific name and personality."""
    return {
        "name": name,
        "system_instruction": system_instruction,
        "model": genai.GenerativeModel(
            model_name=MODEL,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ],
        )
    }

def count_tokens(text):
    """Count tokens in a text using the model's count_tokens method."""
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.count_tokens(text)
        return response.total_tokens
    except Exception as e:
        print(f"Error counting tokens: {e}")
        return 0

def generate_response(ai, prompt, conversation_history):
    """Generate a response from the AI model."""
    try:
        # Create a chat session
        chat = ai["model"].start_chat(history=[])
        
        # Add system instruction
        full_prompt = f"{ai['system_instruction']}\n\nConversation history:\n{conversation_history}\n\nYour response to: {prompt}"
        
        # Count prompt tokens
        prompt_tokens = count_tokens(full_prompt)
        
        # Generate response
        response = chat.send_message(full_prompt)
        
        # Get token usage
        usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
        
        token_usage = {
            "prompt_tokens": prompt_tokens,
            "response_tokens": usage_metadata.candidates_token_count if usage_metadata else 0,
            "total_tokens": prompt_tokens + (usage_metadata.candidates_token_count if usage_metadata else 0)
        }
        
        return response.text, token_usage
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"Sorry, I encountered an error: {e}", {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}

def load_personalities():
    """Load AI personalities from a JSON file if it exists, otherwise use defaults."""
    if os.path.exists("personalities.json"):
        try:
            with open("personalities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading personalities: {e}")
            return get_default_personalities()
    else:
        return get_default_personalities()

def get_default_personalities():
    """Return default personalities if the JSON file doesn't exist."""
    return {
        "ai1": {
            "name": "Alice",
            "color": "blue",
            "system_instruction": "You are Alice, a friendly and curious AI assistant. You have a positive outlook and enjoy discussing various topics. Keep your responses concise and engaging.",
            "temperature": 0.7
        },
        "ai2": {
            "name": "Bob",
            "color": "green",
            "system_instruction": "You are Bob, a thoughtful and analytical AI assistant. You like to consider different perspectives and ask insightful questions. Keep your responses concise and thought-provoking.",
            "temperature": 0.7
        }
    }

def save_conversation(conversation_data, initial_prompt, ai1_name, ai2_name, token_usage):
    """Save the conversation to a JSON file."""
    # Create conversations directory if it doesn't exist
    os.makedirs("conversations", exist_ok=True)
    
    # Generate a filename based on the current date and time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversations/conversation_{ai1_name}_and_{ai2_name}_{timestamp}.json"
    
    # Prepare the data to save
    data = {
        "timestamp": timestamp,
        "initial_prompt": initial_prompt,
        "participants": [ai1_name, ai2_name],
        "conversation": conversation_data,
        "token_usage": token_usage
    }
    
    # Save to file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    return filename

@app.route('/')
def index():
    """Render the main page."""
    personalities = load_personalities()
    return render_template('index.html', personalities=personalities)

@app.route('/api/personalities', methods=['GET'])
def get_personalities():
    """API endpoint to get all personalities."""
    personalities = load_personalities()
    return jsonify(personalities)

@app.route('/api/conversation', methods=['POST'])
def start_conversation():
    """API endpoint to start a conversation between two AIs."""
    data = request.json
    ai1_key = data.get('ai1')
    ai2_key = data.get('ai2')
    initial_prompt = data.get('prompt')
    num_turns = int(data.get('turns', 5))
    
    personalities = load_personalities()
    
    # Set up the two AI models
    ai1_config = personalities[ai1_key]
    ai2_config = personalities[ai2_key]
    
    ai1 = setup_model(
        ai1_config["name"],
        ai1_config["system_instruction"],
        float(ai1_config["temperature"])
    )
    
    ai2 = setup_model(
        ai2_config["name"],
        ai2_config["system_instruction"],
        float(ai2_config["temperature"])
    )
    
    # Initialize conversation
    conversation_history = ""
    conversation_data = []
    current_prompt = initial_prompt
    total_token_usage = {
        "prompt_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0
    }
    
    # Start the conversation loop
    for i in range(num_turns):
        # First AI's turn
        response1, token_usage1 = generate_response(ai1, current_prompt, conversation_history)
        conversation_history += f"{ai1['name']}: {response1}\n"
        conversation_data.append({
            "speaker": ai1["name"],
            "message": response1,
            "token_usage": token_usage1
        })
        
        # Update token usage
        total_token_usage["prompt_tokens"] += token_usage1["prompt_tokens"]
        total_token_usage["response_tokens"] += token_usage1["response_tokens"]
        total_token_usage["total_tokens"] += token_usage1["total_tokens"]
        
        # Second AI's turn
        response2, token_usage2 = generate_response(ai2, response1, conversation_history)
        conversation_history += f"{ai2['name']}: {response2}\n"
        conversation_data.append({
            "speaker": ai2["name"],
            "message": response2,
            "token_usage": token_usage2
        })
        
        # Update token usage
        total_token_usage["prompt_tokens"] += token_usage2["prompt_tokens"]
        total_token_usage["response_tokens"] += token_usage2["response_tokens"]
        total_token_usage["total_tokens"] += token_usage2["total_tokens"]
        
        # Update the prompt for the next turn
        current_prompt = response2
    
    # Save the conversation
    save_file = save_conversation(
        conversation_data, 
        initial_prompt, 
        ai1["name"], 
        ai2["name"], 
        total_token_usage
    )
    
    return jsonify({
        "conversation": conversation_data,
        "token_usage": total_token_usage,
        "saved_file": save_file
    })

# Create templates directory and HTML files
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

if __name__ == '__main__':
    socketio.run(app, debug=True) 