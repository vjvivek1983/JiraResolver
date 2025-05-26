import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
from config import JIRA_URL, JIRA_PROJECT_KEY, JIRA_EMAIL, JIRA_API_TOKEN




def get_similar_tickets(query):
    import faiss
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain.schema import Document
    from sentence_transformers import SentenceTransformer

    # Load index and metadata
    index = faiss.read_index("my_faiss.index")
    df = pd.read_csv("my_faiss_metadata.csv")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    # Embed your query
    query_vector = model.encode([query])

    # Search
    k = 3
    D, I = index.search(query_vector, k)

    # Show results
    return "\n\n".join(df.iloc[idx]["answer"] for idx in I[0])


def generate_llm_response(description, context):
    prompt = f"""You are a helpful IT support agent. A customer has submitted the following request:

### Ticket Description:
{description}

### Similar Past Ticket Summaries:
{context}

Write a helpful and professional response as a comment.
"""
    from openai import OpenAI
    
    client = OpenAI(api_key="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")
    response = client.chat.completions.create(model="gpt-4o",
    messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()

def post_jira_comment(issue_key, text):
    url = f"https://maverick246.atlassian.net/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": text}]
            }]
        }
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers,
                             auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN))



def transition_ticket(issue_key, target_status):
    transitions_url = f"https://maverick246.atlassian.net/rest/api/3/issue/{issue_key}/transitions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Get available transitions
    res = requests.get(transitions_url, headers=headers, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)).json()
    transitions = res.get("transitions", [])

    transition_id = next(
        (t["id"] for t in transitions if t["name"].lower() == target_status.lower()), None
    )

    if transition_id:
        requests.post(transitions_url, headers=headers, json={"transition": {"id": transition_id}})
