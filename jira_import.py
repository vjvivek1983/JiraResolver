import pandas as pd
import requests,os
from requests.auth import HTTPBasicAuth

# ==== CONFIGURATION ====
JIRA_URL = "https://maverick246.atlassian.net"
JIRA_PROJECT_KEY = "SUP"
JIRA_EMAIL = "YOUR EMAIL"
JIRA_API_TOKEN = "YOUR API TOKEN"

RESOLUTION_NAME = "Done"
TRANSITION_NAME = "Resolve this issue"

CUSTOM_TEAM_FIELD_ID = "customfield_10055"
CUSTOM_LANGUAGE_FIELD_ID  = "customfield_10054" 
CUSTOM_TYPE_FIELD_ID = "customfield_10056"
JIRA_ISSUE_TYPE = "[System] Service request"

CSV_PATH = "dataset-tickets-multi-lang-4-20k.csv"

# ==== READ CSV ====
df = pd.read_csv(CSV_PATH)
processed_rows = []


def get_issue_transitions(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    response = requests.get(url, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN))
    response.raise_for_status()
    return response.json()["transitions"]

def transition_issue(issue_key, transition_id):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    payload = {
        "transition": {"id": transition_id},
        "fields": {"resolution": {"name": RESOLUTION_NAME}}
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers,
                             auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN))
    return response.status_code == 204

def add_comment(issue_key, comment_body_text):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/comment"
    
    # Use Atlassian Document Format for the comment body
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment_body_text
                        }
                    ]
                }
            ]
        }
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url, json=payload, headers=headers,
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    )

    if response.status_code != 201:
        print(f"❌ Error {response.status_code} when commenting: {response.text}")
    
    return response.status_code == 201


def create_jira_ticket(row):
    
    summary  = str(row['subject']) if pd.notna(row['subject']) else f"{row['queue']} - {row['type']}"
    description = f"Customer Request:\n{row['body']}"
    resolution_comment = row['answer']
    issue_type = row['type'].strip().capitalize()
    team_value = row['queue'].strip()
    

    # Clean up tags
    tags = [str(row.get(f"tag_{i}", "")).strip().replace(" ", "_") for i in range(1, 9)]
    labels = [tag for tag in tags if tag and tag.lower() != 'nan']

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },

            "issuetype": {"name": JIRA_ISSUE_TYPE},
            
            "priority": {"name": row['priority'].capitalize()},
            "labels": labels,
            CUSTOM_TEAM_FIELD_ID: team_value,
            CUSTOM_TYPE_FIELD_ID: {"value": issue_type},
            CUSTOM_LANGUAGE_FIELD_ID: {"value": row['language'].strip()}

        }
    }

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    print(payload)

    # Create the issue
    response = requests.post(
        f"{JIRA_URL}/rest/api/3/issue",
        auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
        headers=headers,
        json=payload
    )

    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"✅ Created: {issue_key} | {summary}")

        if pd.notna(resolution_comment):
            # Add resolution comment
            if add_comment(issue_key, resolution_comment):
                print(f"📝 Comment added to {issue_key}")
            else:
                print(f"⚠️ Failed to add comment on {issue_key}")

            # Transition to RESOLVED
            transitions = get_issue_transitions(issue_key)
            transition_id = next((t["id"] for t in transitions if t["name"].lower() == TRANSITION_NAME.lower()), None)

            if transition_id:
                if transition_issue(issue_key, transition_id):
                    print(f"✅ Transitioned {issue_key} to {RESOLUTION_NAME}")
                else:
                    print(f"❌ Failed to transition {issue_key}")
            else:
                print(f"❌ No valid transition '{TRANSITION_NAME}' found for {issue_key}")
    else:
        print(f"❌ Failed to create: {summary}")
        print(response.status_code, response.text)

# ==== PROCESS CSV ====
for idx, row in df.iterrows():
    initial_row_count = len(processed_rows)
    try:
        result = create_jira_ticket(row)
        # If issue created successfully, add to processed list
        if result is None:  # your function prints and returns nothing; use prints to infer success
            processed_rows.append(idx)
    except Exception as e:
        print(f"⚠️ Exception for row {idx}: {e}")
# Save processed rows to a new file
if processed_rows:
    processed_df = df.loc[processed_rows]
    processed_df.to_csv("processed_tickets.csv", index=False, mode='a', header=not pd.read_csv("processed_tickets.csv").empty if os.path.exists("processed_tickets.csv") else True)

    # Drop from original DataFrame
    df.drop(index=processed_rows, inplace=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"✅ Moved {len(processed_rows)} processed rows to processed_tickets.csv and updated {CSV_PATH}")
else:
    print("⚠️ No rows processed successfully.")

