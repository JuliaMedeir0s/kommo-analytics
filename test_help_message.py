"""
Script para testar o envio da mensagem de help do Telegram
"""
import os
from dotenv import load_dotenv
from src.handlers.telegram_commands import help_message
from src.integrations.messenger import TelegramMessenger

load_dotenv()

def test_help_message():
    print("=" * 50)
    print("TESTE DE MENSAGEM DE HELP")
    print("=" * 50)
    
    # Mostrar a mensagem que será enviada
    msg = help_message()
    print("\n📝 MENSAGEM QUE SERÁ ENVIADA:\n")
    print(msg)
    print("\n" + "=" * 50)
    
    # Verificar token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN não configurado no .env")
        return
    
    print(f"\n✅ Token encontrado: {bot_token[:10]}...")
    
    # Pedir chat_id
    chat_id = input("\n📱 Digite o chat_id para enviar a mensagem de teste: ")
    
    if not chat_id:
        print("❌ Chat ID não fornecido")
        return
    
    try:
        chat_id = int(chat_id)
    except ValueError:
        print("❌ Chat ID inválido (deve ser um número)")
        return
    
    # Criar messenger e enviar
    print(f"\n📤 Enviando mensagem para chat {chat_id}...")
    messenger = TelegramMessenger(bot_token)
    
    # Health check primeiro
    if messenger.health_check():
        print("✅ Bot está online e acessível")
    else:
        print("❌ Bot parece estar offline ou inacessível")
        return
    
    # Enviar mensagem
    result = messenger.send_message(chat_id, msg)
    
    print("\n📋 RESULTADO DO ENVIO:")
    print(result)
    
    if result.get("ok"):
        print("\n✅ MENSAGEM ENVIADA COM SUCESSO!")
    else:
        print("\n❌ FALHA AO ENVIAR MENSAGEM")
        if "description" in result:
            print(f"Descrição do erro: {result['description']}")

if __name__ == "__main__":
    test_help_message()
