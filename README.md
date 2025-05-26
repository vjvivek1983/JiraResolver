This is a simple tool to create autoresolution to the tickets in JIRA. It uses a RAG database that is created using the existing solutions to tickets. Everytime a new ticket is created, it searches the content of the new ticket against the existing tickets. Passes on best 3 matching tickets to the LLM and LLM then generates an auto response. This response is posted as comment in the ticket and ticket is moved to the "Waiting for customer feedback" status. 

Possible enhancements:
1. Filter on the severity of the ticket. Only provide auto response to the low severity tickets.
2. Create named tags like <name>, <phone number> etc which are filled before the response is posted.
3. Create a full stateful solution where LLM can determine the right queue to move ticket to. Users can just create the tickets without the corresponding queues and LLM automatically detects the right queue for faster resolution.
4. Add organization specific MCP servers to provide right information which might be PII constrained.
5. Create fix templates with mandatory information. Checks for all the required information can be done using LLM.
6. Other automated actions (org specific) can be taken as directed by LLM (such as crash log collection, database permission grant, policy document sharing etc.)
