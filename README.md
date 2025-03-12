# Recursive AI Talking

This application allows two AI models to have a conversation with each other using the Google AI Studio API (Gemini 2.0 Flash). You provide an initial prompt, and the two AI models will take turns responding to each other.

## Features

- Two AI models with different personalities selected from a customizable list
- Colored terminal output to distinguish between the models
- Configurable number of conversation turns
- Secure API key storage using environment variables
- Save conversations to JSON files
- Token usage tracking
- Web UI for easy interaction

## Setup

1. Make sure you have Python 3.7+ installed on your system.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file with your Google AI API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

   You can obtain an API key from the [Google AI Studio](https://makersuite.google.com/app/apikey).

## Usage

### Command Line Version

Run the command line application:
```
python ai_conversation_simplified.py
```

The application will guide you through the following steps:

1. Select the first AI personality from the available options
2. Select the second AI personality from the remaining options
3. Enter an initial prompt to start the conversation
4. Specify how many turns you want the conversation to continue (default is 5)
5. Watch as the two AI models converse with each other!
6. View token usage statistics at the end of the conversation
7. Choose whether to save the conversation to a file

### Web UI Version

Run the web application:
```
python ai_conversation_web.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

The web interface provides:

1. A configuration panel to select AI personalities and set parameters
2. A conversation display area to view the AI conversation
3. Real-time token usage tracking
4. Status updates on the conversation progress
5. Automatic saving of conversations

## Customizing AI Personalities

You can customize the AI personalities by editing the `personalities.json` file. Each personality has the following properties:

- `name`: The display name of the AI
- `color`: The color of the AI's messages (red, green, blue, yellow, magenta, cyan, white)
- `system_instruction`: The personality and behavior instructions for the AI
- `temperature`: Controls the randomness of the AI's responses (0.0 to 1.0)

Example personality configuration:
```json
{
  "philosopher": {
    "name": "Socrates",
    "color": "cyan",
    "system_instruction": "You are Socrates, a philosophical AI that loves to ask probing questions...",
    "temperature": 0.8
  }
}
```

## Troubleshooting

- If you encounter API errors, make sure your API key is correct and has access to the Gemini 2.0 Flash model.
- If you see rate limit errors, you may need to wait a bit before trying again.
- For web UI issues, check the browser console and server logs for error messages.

## License

This project is open source and available under the MIT License. 