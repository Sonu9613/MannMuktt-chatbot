from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import requests
import uuid
import os

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv('API_KEY')
ENDPOINT = os.getenv('ENDPOINT')
if not API_KEY or not ENDPOINT:
    raise ValueError("API_KEY and ENDPOINT must be set in the environment variables.")

# Initialize Flask app
app = Flask(__name__)
session_id = uuid.uuid4()  # Unique session identifier

# Helper Functions
def process_user_message(user_input):
    """Prepare the user message for the API payload."""
    return {
        "role": "user",
        "content": user_input
    }

def get_base_payload():
    """Create the base payload with system instructions."""
    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Act as a psychologist. Your goal is to understand and evaluate the patient through observation, "
                    "active listening, and subtle guidance rather than direct questioning. Your approach should be "
                    "gentle, empathetic, and patient-centered, aligning with the principles of Cognitive Behavioral "
                    "Therapy (CBT). Begin each session with a warm and polite greeting to set a comfortable tone.\n\n"
                    "Guidelines:\n"
                    "1. Start with Context: Reflect briefly on previous discussions or observations.\n"
                    "2. Pay attention to shifts in language or recurring patterns.\n"
                    "3. Encourage Expression: Respond minimally to allow the patient to lead. Use prompts like:\n"
                    '   "That seems significant. Could you share more about how it\'s affecting you?"\n'
                    '   "It\'s okay to take your time. I\'m here to listen."\n'
                    "4. Offer Subtle Reflections: Encourage introspection without being intrusive:\n"
                    '   "You mentioned feeling [emotion]. Do you notice any patterns connected to that?"\n'
                    '   "Sometimes, experiences like this bring up mixed feelings. Does that align with what you\'re feeling?"\n'
                    "5. Transparency: If unsure, acknowledge honestly:\n"
                    '   "I\'m not aware of the full context there, but we can explore it together."\n'
                    "6. Maintain a calm, supportive tone, and create a safe, non-judgmental space for the patient to share at their comfort level."
                )
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 200
    }

def update_history(payload, user_message):
    """Append the user message to the conversation history."""
    payload["messages"].append(user_message)
    return payload

def get_system_response(payload):
    """Send the payload to the API and return the response."""
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raise error for HTTP issues
        return response.json()  # Return JSON response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500

# Flask Routes
@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests from the client."""
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Prepare the payload
    payload = get_base_payload()
    user_message = process_user_message(user_input)
    payload = update_history(payload, user_message)

    # Get system response
    system_response = get_system_response(payload)
    if isinstance(system_response, tuple):  # Handle errors
        return system_response

    # Extract the chatbot's response
    try:
        response_content = system_response["choices"][0]["message"]["content"]
        return jsonify({"response": response_content})
    except (KeyError, IndexError) as e:
        return jsonify({"error": "Invalid response format from the API", "details": str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
