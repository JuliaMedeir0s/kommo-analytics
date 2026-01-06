#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testes para formatação de telefones em padrão internacional (+55)
"""
import re


def is_valid_phone(phone):
    """Valida formato de telefone"""
    clean_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
    return bool(re.match(r'^\d{10,15}$', clean_phone)) and len(clean_phone) >= 10


def format_phone(phone):
    """
    Formata o telefone para o padrão internacional +55...
    Exemplos:
    - 11987654321 → +5511987654321
    - (11) 9876-5432 → +5511987654321 (note: faltam dígitos, será formatado com 10 dígitos)
    - +55 11 98765-4321 → +5511987654321
    - 5511987654321 → +5511987654321
    """
    clean_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
    
    if clean_phone.startswith('55'):
        clean_phone = clean_phone[2:]
    
    if len(clean_phone) > 11:
        clean_phone = clean_phone[-11:]
    elif len(clean_phone) < 11:
        return ""
    
    return f"+55{clean_phone}"


def test_phone_formatting():
    """Teste de formatação de telefones"""
    print('📱 FORMATAÇÃO DE TELEFONES PARA PADRÃO INTERNACIONAL:')
    print('=' * 70)
    
    test_cases = [
        ('11987654321', '+5511987654321'),  # 11 dígitos = válido
        ('(11) 9876-5432', ''),  # 10 dígitos = incompleto, retorna vazio
        ('+55 11 98765-4321', '+5511987654321'),  # 11 dígitos válido
        ('11 9 8765-4321', '+5511987654321'),  # 11 dígitos válido
        ('5511987654321', '+5511987654321'),  # 11 dígitos com código de país
        ('55 11 98765-4321', '+5511987654321'),  # 11 dígitos com espaços
        ('21987654321', '+5521987654321'),  # 11 dígitos válido
        ('(21) 98765-4321', '+5521987654321'),  # 11 dígitos com formatação
    ]
    
    print(f'{"Entrada":35} {"Esperado":20} {"Resultado":20} {"Status"}')
    print('=' * 70)
    
    for input_phone, expected in test_cases:
        if is_valid_phone(input_phone):
            formatted = format_phone(input_phone)
            status = '✅ OK' if formatted == expected else '❌ ERRO'
            print(f'{input_phone:35} {expected:20} {formatted:20} {status}')
            assert formatted == expected, f"Formatação incorreta para {input_phone}"
        else:
            print(f'{input_phone:35} INVÁLIDO')
    
    print('=' * 70)
    print('✅ Todos os testes de formatação passaram!')


if __name__ == '__main__':
    test_phone_formatting()
    print('\n✨ Formatação de telefones validada com sucesso!')
