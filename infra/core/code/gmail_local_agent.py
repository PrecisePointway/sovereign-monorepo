'''
# Gmail Local Agent - Sovereign Infrastructure
# This script uses the standard Google API Python Client for local execution.

import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

class GmailLocalAgent:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = self._get_credentials(credentials_path, token_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _get_credentials(self, credentials_path, token_path):
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def search_emails(self, query="", max_results=10):
        """
        Searches for emails matching the given query.
        :param query: Gmail search query (e.g., 'from:user@example.com').
        :param max_results: Maximum number of results to return.
        :return: A list of messages.
        """
        try:
            result = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = result.get('messages', [])
            return messages
        except Exception as e:
            print(f"An error occurred during search: {e}")
            return None

    def read_message(self, message_id):
        """
        Reads a specific email by its ID.
        :param message_id: The ID of the message to read.
        :return: The message content.
        """
        try:
            message = self.service.users().messages().get(userId='me', id=message_id, format='full').execute()
            return message
        except Exception as e:
            print(f"An error occurred while reading message {message_id}: {e}")
            return None

    def send_email(self, to, subject, message_text):
        """
        Sends an email.
        :param to: Recipient's email address.
        :param subject: The subject of the email.
        :param message_text: The body of the email.
        :return: The sent message object.
        """
        try:
            from email.mime.text import MIMEText
            message = MIMEText(message_text)
            message['to'] = to
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'raw': raw_message}
            sent_message = self.service.users().messages().send(userId='me', body=body).execute()
            return sent_message
        except Exception as e:
            print(f"An error occurred while sending email: {e}")
            return None

if __name__ == '__main__':
    # Example Usage:
    # 1. Make sure your `credentials.json` from Google Cloud is in the same directory.
    # 2. The first time you run, it will open a browser window for you to authorize the app.
    # 3. A `token.json` file will be created to store your credentials for future runs.

    agent = GmailLocalAgent()

    # --- Search Example ---
    print("--- Searching for recent emails ---")
    search_results = agent.search_emails(query='is:unread', max_results=5)
    if search_results:
        for msg in search_results:
            print(f"Found message: {msg['id']}")
            full_message = agent.read_message(msg['id'])
            if full_message:
                # Extracting subject from headers
                subject_header = next((header for header in full_message['payload']['headers'] if header['name'] == 'Subject'), None)
                subject = subject_header['value'] if subject_header else 'No Subject'
                print(f"  Subject: {subject}")
                print(f"  Snippet: {full_message['snippet']}\n")

    # --- Send Example ---
    # print("\n--- Sending a test email ---")
    # sent = agent.send_email(
    #     to='your_email@example.com', 
    #     subject='Sovereign Agent Test', 
    #     message_text='This is a test message from the Gmail Local Agent.'
    # )
    # if sent:
    #     print(f"Email sent successfully! Message ID: {sent['id']}")
'''
