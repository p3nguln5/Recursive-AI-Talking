import os
import time
import json
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

# Load environment variables
load_dotenv()

# Configure the Google AI API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Set up the model configuration
MODEL = "gemini-2.0-flash"  # Using Gemini 2.0 Flash as specified

# Track token usage
token_usage = {
    "total_input_tokens": 0,
    "total_output_tokens": 0
}

def setup_model(name, color, system_instruction, temperature=0.7):
    """Set up an AI model with a specific name and personality."""
    return {
        "name": name,
        "color": color,
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

def generate_response(ai, prompt, conversation_history):
    """Generate a response from the AI model."""
    try:
        # Create a chat session
        chat = ai["model"].start_chat(history=[])
        
        # Add system instruction
        full_prompt = f"{ai['system_instruction']}\n\nConversation history:\n{conversation_history}\n\nYour response to: {prompt}"
        
        # Generate response
        response = chat.send_message(full_prompt)
        
        # Track token usage
        if hasattr(response, 'usage_metadata'):
            token_usage["total_input_tokens"] += response.usage_metadata.prompt_token_count
            token_usage["total_output_tokens"] += response.usage_metadata.candidates_token_count
        
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"Sorry, I encountered an error: {e}"

def display_message(ai, message):
    """Display a message with the AI's name and color."""
    print(f"{ai['color']}[{ai['name']}]: {message}{Style.RESET_ALL}")
    print()  # Add a blank line for readability

def save_conversation(conversation_data, initial_prompt, ai1_name, ai2_name):
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

def get_color_code(color_name):
    """Convert a color name to a colorama color code."""
    color_map = {
        "red": Fore.RED,
        "green": Fore.GREEN,
        "blue": Fore.BLUE,
        "yellow": Fore.YELLOW,
        "magenta": Fore.MAGENTA,
        "cyan": Fore.CYAN,
        "white": Fore.WHITE
    }
    return color_map.get(color_name.lower(), Fore.WHITE)

def select_personality(personalities, prompt_text):
    """Let the user select a personality from the available options."""
    print(f"{Fore.YELLOW}{prompt_text}{Style.RESET_ALL}")
    
    # Display available personalities with descriptions
    options = list(personalities.keys())
    for i, key in enumerate(options):
        personality = personalities[key]
        name = personality["name"]
        description = personality["system_instruction"][:100] + "..." if len(personality["system_instruction"]) > 100 else personality["system_instruction"]
        print(f"{i+1}. {Fore.CYAN}{name}{Style.RESET_ALL} - {description}")
    
    # Get user selection
    while True:
        try:
            selection = int(input("> ")) - 1
            if 0 <= selection < len(options):
                return options[selection]
            else:
                print(f"{Fore.RED}Invalid selection. Please try again.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a number.{Style.RESET_ALL}")

def main():
    # Display welcome message
    print(f"{Fore.CYAN}=== AI Conversation Generator ==={Style.RESET_ALL}")
    print(f"{Fore.CYAN}This program allows two AI personalities to have a conversation with each other.{Style.RESET_ALL}")
    print()
    
    # Load AI personalities
    personalities = load_personalities()
    
    # Let the user select personalities for the conversation
    print(f"{Fore.CYAN}First, let's select the two AI personalities that will converse with each other:{Style.RESET_ALL}")
    print()
    
    # Select first AI
    ai1_key = select_personality(personalities, "Select the first AI personality:")
    ai1_config = personalities[ai1_key]
    
    # Select second AI (excluding the first one)
    remaining_personalities = {k: v for k, v in personalities.items() if k != ai1_key}
    ai2_key = select_personality(remaining_personalities, "Select the second AI personality:")
    ai2_config = personalities[ai2_key]
    
    # Set up the two AI models with their personalities
    ai1 = setup_model(
        ai1_config["name"],
        get_color_code(ai1_config["color"]),
        ai1_config["system_instruction"],
        float(ai1_config["temperature"])
    )
    
    ai2 = setup_model(
        ai2_config["name"],
        get_color_code(ai2_config["color"]),
        ai2_config["system_instruction"],
        float(ai2_config["temperature"])
    )
    
    # Get the initial prompt from the user
    print(f"{Fore.YELLOW}Enter an initial prompt to start the conversation:{Style.RESET_ALL}")
    initial_prompt = input("> ")
    
    # Set the number of conversation turns
    print(f"{Fore.YELLOW}How many turns should the conversation continue? (default: 5){Style.RESET_ALL}")
    try:
        num_turns = int(input("> ") or "5")
    except ValueError:
        num_turns = 5
        print(f"{Fore.YELLOW}Using default value: 5 turns{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Starting conversation between {ai1['name']} and {ai2['name']}...{Style.RESET_ALL}\n")
    
    # Initialize conversation history and data for saving
    conversation_history = ""
    conversation_data = []
    current_prompt = initial_prompt
    
    # Start the conversation loop
    for i in range(num_turns):
        # First AI's turn
        print(f"{Fore.YELLOW}Turn {i+1}/{num_turns}{Style.RESET_ALL}")
        response1 = generate_response(ai1, current_prompt, conversation_history)
        display_message(ai1, response1)
        conversation_history += f"{ai1['name']}: {response1}\n"
        conversation_data.append({"speaker": ai1["name"], "message": response1})
        time.sleep(1)  # Add a small delay for readability
        
        # Second AI's turn
        response2 = generate_response(ai2, response1, conversation_history)
        display_message(ai2, response2)
        conversation_history += f"{ai2['name']}: {response2}\n"
        conversation_data.append({"speaker": ai2["name"], "message": response2})
        time.sleep(1)  # Add a small delay for readability
        
        # Update the prompt for the next turn
        current_prompt = response2
    
    print(f"\n{Fore.YELLOW}Conversation ended after {num_turns} turns.{Style.RESET_ALL}")
    
    # Display token usage
    print(f"\n{Fore.CYAN}Token Usage:{Style.RESET_ALL}")
    print(f"Input tokens: {token_usage['total_input_tokens']}")
    print(f"Output tokens: {token_usage['total_output_tokens']}")
    print(f"Total tokens: {token_usage['total_input_tokens'] + token_usage['total_output_tokens']}")
    
    # Ask if the user wants to save the conversation
    print(f"\n{Fore.YELLOW}Do you want to save this conversation? (y/n){Style.RESET_ALL}")
    if input("> ").lower().startswith("y"):
        saved_file = save_conversation(conversation_data, initial_prompt, ai1["name"], ai2["name"])
        print(f"{Fore.YELLOW}Conversation saved to: {saved_file}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 