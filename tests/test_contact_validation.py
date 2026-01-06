#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testes para validação de contatos (email e telefone)
"""
import re


def is_valid_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone):
    """Valida formato de telefone (pode incluir números e alguns caracteres especiais)"""
    clean_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
    return bool(re.match(r'^\d{10,15}$', clean_phone)) and len(clean_phone) >= 10


def test_email_validation():
    """Teste de validação de emails"""
    print('📧 VALIDAÇÃO DE EMAILS:')
    print('=' * 50)
    
    valid_emails = [
        'joao@example.com',
        'maria.silva@company.co.uk', 
        'contato+tag@empresa.com.br',
    ]
    
    invalid_emails = [
        'invalid@',
        '@invalid.com',
        'sem-arroba.com'
    ]
    
    print('✅ E-mails válidos:')
    for email in valid_emails:
        assert is_valid_email(email), f"Email {email} deveria ser válido"
        print(f'  {email}')
    
    print('\n❌ E-mails inválidos:')
    for email in invalid_emails:
        assert not is_valid_email(email), f"Email {email} deveria ser inválido"
        print(f'  {email}')
    
    print('\n✅ Teste de e-mails passou!')


def test_phone_validation():
    """Teste de validação de telefones"""
    print('\n📱 VALIDAÇÃO DE TELEFONES:')
    print('=' * 50)
    
    valid_phones = [
        '11987654321',
        '(11) 9876-5432',
        '+55 11 98765-4321',
        '11 9 8765-4321',
        '5511987654321'
    ]
    
    invalid_phones = [
        '123',
        '11 9876',
    ]
    
    print('✅ Telefones válidos:')
    for phone in valid_phones:
        assert is_valid_phone(phone), f"Telefone {phone} deveria ser válido"
        print(f'  {phone}')
    
    print('\n❌ Telefones inválidos:')
    for phone in invalid_phones:
        assert not is_valid_phone(phone), f"Telefone {phone} deveria ser inválido"
        print(f'  {phone}')
    
    print('\n✅ Teste de telefones passou!')


if __name__ == '__main__':
    test_email_validation()
    test_phone_validation()
    print('\n✨ Todos os testes de validação foram aprovados!')
