from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import requests
import uuid
import os

# Configuration
API_KEY = os.getenv('api_key')
session_id = uuid.uuid4()

ENDPOINT = os.getenv("ENDPOINT")

app = Flask(__name__)

def processUserMessage(input):
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": input
            }
        ]
    }

def getBasePayload():
    return {
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text":"""Act as a psychologist, your goal is to understand and evaluate the patient through observation, active listening, and subtle guidance rather than direct questioning. Your approach should be gentle, empathetic, and patient-centered, aligning with the principles of Cognitive Behavioral Therapy (CBT). Begin each session with a warm and polite greeting to set a comfortable tone.Do not output any nonreadable characters and responses should be in first person format. 
                  
                  Guidelines:
                  1. Start with Context: Reflect briefly on previous discussions or observations.
                  2. Pay attention to shifts in language or recurring patterns.
                  3. Encourage Expression: Respond minimally to allow the patient to lead. Use prompts like:
                  "That seems significant. Could you share more about how it's affecting you?"
                  "It's okay to take your time. I'm here to listen."
                  4. Offer Subtle Reflections: Encourage introspection without being intrusive:
                  "You mentioned feeling [emotion]. Do you notice any patterns connected to that?"
                  "Sometimes, experiences like this bring up mixed feelings. Does that align with what you're feeling?"
                  5. Transparency: If unsure, acknowledge honestly:
                  "I'm not aware of the full context there, but we can explore it together."
                  6. Maintain a calm, supportive tone, and create a safe, non-judgmental space for the patient to share at their comfort level.
                """
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 200
    }

def updateHistory(payload, processedUserMessage):
    payload['messages'].append(processedUserMessage) 
    return payload

def getSystemResponse(payload):
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.HTTPError as errh:
        return jsonify({"error": "HTTP Error occurred", "details": str(errh)}), 500
    except requests.exceptions.ConnectionError as errc:
        return jsonify({"error": "Connection Error occurred", "details": str(errc)}), 500
    except requests.exceptions.Timeout as errt:
        return jsonify({"error": "Timeout Error occurred", "details": str(errt)}), 500
    except requests.exceptions.RequestException as err:
        return jsonify({"error": "An unknown error occurred", "details": str(err)}), 500

    return response

def response_gen(payload):
    sysresponse = getSystemResponse(payload)
    if isinstance(sysresponse, tuple):  # If there's an error response
        return sysresponse
    response = sysresponse.json()
    return response['choices'][0]['message']['content']

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    payload = getBasePayload()
    processed_message = processUserMessage(user_input)
    payload = updateHistory(payload, processed_message)
    
    response = response_gen(payload)
    
    if isinstance(response, tuple):  # If there's an error response
        return response
    
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
