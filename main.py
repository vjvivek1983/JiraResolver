from flask import Flask, request, jsonify
import requests

from jira_helpers import (
    get_similar_tickets, generate_llm_response, post_jira_comment, transition_ticket
)

app = Flask(__name__)

@app.route("/jira-webhook", methods=["POST"])
def handle_ticket_creation():
    data = request.json
    issue = data.get("issue", {})
    issue_key = issue.get("key")
    #description = issue["fields"].get("description", {}).get("content", [])

    description_raw = issue["fields"].get("description")
    
    print(str(description_raw))

    if isinstance(description_raw, dict):
        description = description_raw.get("content", [])
    elif isinstance(description_raw, str):
        description = [{"type": "paragraph", "text": description_raw}]
    else:
        description = []

    # Extract raw description text
    desc_text = "\n".join([
        part["text"]
        for block in description for part in block.get("content", [])
        if part.get("type") == "text"
    ])
    
    if desc_text == "":
        desc_text = str(description)

    print("Description text:" + desc_text)
    
    # Step 1: Retrieve relevant historical tickets
    similar_context = get_similar_tickets(desc_text)
    
    print("Similar Context:" + similar_context)

    # Step 2: Generate response with LLM
    auto_response = generate_llm_response(desc_text, similar_context)
    
    print("Auto Response: " + auto_response)

    # Step 3: Post response as comment
    post_jira_comment(issue_key, auto_response)

    # Step 4: Transition issue to "Waiting for Customer Feedback"
    transition_ticket(issue_key, target_status="Waiting for Customer Feedback")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=5001)
