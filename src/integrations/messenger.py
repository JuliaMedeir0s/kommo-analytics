import requests
from core.logger import logger


class TelegramMessenger:
    def __init__(self, bot_token):
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, chat_id, text):
        try:
            endpoint = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown" # Permite negrito e itálico
            }
            logger.info(f"📤 [MESSENGER] Enviando mensagem para chat {chat_id}")
            response = requests.post(endpoint, json=payload, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"✅ [MESSENGER] Mensagem enviada com sucesso para chat {chat_id}")
            else:
                logger.error(f"❌ [MESSENGER] Falha ao enviar mensagem para chat {chat_id}: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [MESSENGER] Exceção ao enviar mensagem para chat {chat_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
    
    def send_document(self, chat_id, file_path, caption=None):
        """Envia um arquivo (documento) para o chat"""
        try:
            endpoint = f"{self.base_url}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {'chat_id': chat_id}
                
                if caption:
                    data['caption'] = caption
                
                logger.info(f"📤 [MESSENGER] Enviando documento para chat {chat_id}: {file_path}")
                response = requests.post(endpoint, data=data, files=files, timeout=30)
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"✅ [MESSENGER] Documento enviado com sucesso para chat {chat_id}")
                else:
                    logger.error(f"❌ [MESSENGER] Falha ao enviar documento para chat {chat_id}: {result}")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [MESSENGER] Exceção ao enviar documento para chat {chat_id}: {e}", exc_info=True)
            return {"ok": False, "error": str(e)}
    
    def health_check(self):
        try:
            endpoint = f"{self.base_url}/getMe"
            response = requests.get(endpoint, timeout=5)
            is_ok = response.status_code == 200
            logger.info(f"🏥 [MESSENGER] Health check: {'✅ OK' if is_ok else '❌ FALHOU'}")
            return is_ok
        except Exception as e:
            logger.error(f"❌ [MESSENGER] Exceção no health check: {e}")
            return False
    