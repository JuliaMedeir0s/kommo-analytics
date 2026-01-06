import requests

class TelegramMessenger:
    def __init__(self, bot_token):
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, chat_id, text):
        endpoint = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown" # Permite negrito e itálico
        }
        response = requests.post(endpoint, json=payload)
        return response.json()
    
    def send_document(self, chat_id, file_path, caption=None):
        """Envia um arquivo (documento) para o chat"""
        endpoint = f"{self.base_url}/sendDocument"
        
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': chat_id}
            
            if caption:
                data['caption'] = caption
            
            response = requests.post(endpoint, data=data, files=files)
            return response.json()
    
    def health_check(self):
        endpoint = f"{self.base_url}/getMe"
        response = requests.get(endpoint)
        return response.status_code == 200
    