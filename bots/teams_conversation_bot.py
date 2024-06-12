import os
import json
from botbuilder.core import CardFactory, TurnContext, MessageFactory
from botbuilder.core.teams import TeamsActivityHandler, TeamsInfo
from botbuilder.schema import Attachment, Activity
from botbuilder.schema.teams import TeamsChannelAccount
from config import DefaultConfig
import requests
import re
import json

CONFIG = DefaultConfig()

BLOG_CARD_TEMPLATE_PATH = "resources/BlogCardTemplate.json"

class TeamsConversationBot(TeamsActivityHandler):
    def __init__(self, app_id: str, app_password: str):
        self._app_id = app_id
        self._app_password = app_password

    async def on_message_activity(self, turn_context: TurnContext):
        TurnContext.remove_recipient_mention(turn_context.activity)
        text = turn_context.activity.text.strip().lower()


        def get_url_list(txt):
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, txt)
            return urls

        if "add" in text:
            user_id = turn_context.activity.from_property.id
            member = await TeamsInfo.get_member(turn_context, user_id)
            
            if isinstance(member, TeamsChannelAccount):
                name = member.name
                email = member.email

                endpoint = CONFIG.API_ENDPOINT 
                headers = {
                    "Content-Type": "application/json",
                    "user": json.dumps({"name": name, "email": email})
                }
                
                urls = get_url_list(text)

                print(headers)

                print(urls)

                response = requests.post(endpoint + '/add', json={"urls": urls}, headers=headers)
                
                print(response.status_code)

                if response.status_code == 201:
                    
                    response_data = response.json()
                    results = response_data.get("results", [])
                    data = []
                    for item in results:
                        if item.get("status") == "error":
                            data.append(item)
                        else:
                            data.append(item.get("data"))
                    # print(data)
                    # print(results)
                    await self._send_blog_cards(turn_context, blog_data=data)
                else:
                    response_data = response.json() 
                    print(response_data)
                    await turn_context.send_activity(f"Some error occurred during content addition: {response_data}")

                
            else:
                await turn_context.send_activity("Unable to retrieve user details.")
        elif "user info" in text:
            await self._get_user_info(turn_context)
        else:
            await turn_context.send_activity("Please use 'add' or 'user info'.")

    async def _get_user_info(self, turn_context: TurnContext):
        try:
            user_id = turn_context.activity.from_property.id
            member = await TeamsInfo.get_member(turn_context, user_id)
            
            if isinstance(member, TeamsChannelAccount):
                user_name = member.name
                user_email = member.email
                await turn_context.send_activity(f"User Name: {user_name}\nUser Email: {user_email}")
            else:
                await turn_context.send_activity("Unable to retrieve user details.")
        except Exception as e:
            await turn_context.send_activity(f"An error occurred: {str(e)}")

    async def _send_blog_cards(self, turn_context: TurnContext, blog_data = []):
        
        for item in blog_data:
            if item.get("status") == "error":
                await self._handle_error_message(turn_context, item)
            else:
                card_template = self._load_card_template(BLOG_CARD_TEMPLATE_PATH)
                populated_card = self._populate_card_template(card_template, item)
                await self._send_adaptive_card(turn_context, populated_card)

    def _load_card_template(self, template_path):
        with open(template_path, 'r') as template_file:
            return json.load(template_file)

    def _populate_card_template(self, template, data):
        if isinstance(template, dict):
            return {k: self._populate_card_template(v, data) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._populate_card_template(item, data) for item in template]
        elif isinstance(template, str) and template.startswith("${") and template.endswith("}"):
            key = template[2:-1]
            return self._get_value_from_data(data, key)
        else:
            return template

    def _get_value_from_data(self, data, key):
        keys = key.split(".")
        val = data
        try:
            for k in keys:
                if isinstance(val, dict):
                    val = val.get(k, "")
                else:
                    raise ValueError(f"Expected dict, got {type(val)} for key {k}")
            return val
        except Exception as e:
            print(f"Error getting value for key '{key}': {e}")
            return ""  # Return a default value in case of error

    async def _send_adaptive_card(self, turn_context: TurnContext, card_content):
        card = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card_content
        )

        response = Activity(
            type="message",
            attachments=[card]
        )

        await turn_context.send_activity(f'`{card_content["body"][0]["text"]}` added successfully.')
        await turn_context.send_activity(response)

    async def _handle_error_message(self, turn_context: TurnContext, error_item):
        url = error_item.get("url", "No URL provided")
        message = error_item.get("message", "No message provided")
        await turn_context.send_activity(f"Error: {message}\nURL: {url}")
