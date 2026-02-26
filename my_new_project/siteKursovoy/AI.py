from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

OPENROUTER_KEY = "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"

SYSTEM_PROMPT = """
    You are an AI assistant built into the StudentApp mobile application.
    You can answer general questions, explain how the app works,
    and assist users in a friendly and concise way.
    """


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"reply": "Message cannot be empty."})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://studentapp.example",
        "X-Title": "StudentApp AI Chatbot"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    try:
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        print("Error:", e)
        print("Response:", response.text)
        return jsonify({"reply": f"Error: {str(e)}"})


if __name__ == "__main__":  # ← ИСПРАВЛЕНО
    app.run(host="0.0.0.0", port=5050)
