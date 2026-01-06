import os
import re
import pandas as pd
from datetime import datetime
from core.logger import logger
from integrations.kommo_client import KommoClient


class ExportEngine:
    """Gera arquivos de exportação de leads por categoria"""
    
    @staticmethod
    def generate_exports(client_id: str, config: dict, period_timestamps: tuple = None, output_dir: str = "./exports") -> dict:
        """
        Gera 4 arquivos por cliente: ganhos, perdidos, perdidos_followup, ativos
        
        Args:
            client_id: ID do cliente
            config: Configuração do cliente
            period_timestamps: Tupla (start_ts, end_ts) para filtrar período. Se None, busca tudo
            output_dir: Diretório de saída
            
        Retorna dict com paths dos arquivos gerados (Excel e CSV)
        """
        period_label = ""
        if period_timestamps:
            start_ts, end_ts = period_timestamps
            period_label = f" ({datetime.fromtimestamp(start_ts).strftime('%d/%m')} a {datetime.fromtimestamp(end_ts).strftime('%d/%m/%Y')})"
        
        logger.info(f"📁 Gerando exportações para {client_id}{period_label}")
        
        # Criar diretório de saída
        os.makedirs(output_dir, exist_ok=True)
        client_dir = os.path.join(output_dir, client_id)
        os.makedirs(client_dir, exist_ok=True)
        
        # Inicializar cliente Kommo
        kommo = KommoClient(config['kommo']['subdomain'], config['kommo']['api_token'])
        
        # IDs necessários
        pipeline_id = config['kommo']['pipeline_id']
        won_status_id = config['kommo']['won_status_id']
        lost_status_id = config['kommo']['lost_status_id']
        followup_pipeline_ids = config['kommo'].get('pipeline_followup_id', [])
        
        # Timestamp para nome dos arquivos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extrair timestamps se informado
        start_ts = period_timestamps[0] if period_timestamps else None
        end_ts = period_timestamps[1] if period_timestamps else None
        
        # 1. GANHOS - leads fechados como ganho no período
        endpoint_ganhos = f"{kommo.base_url}/leads"
        params_ganhos = {
            "filter[pipeline_id][0]": pipeline_id,
            "filter[status][0]": won_status_id,
            "with": "contacts"
        }
        # Filtra pela data de fechamento (quando virou ganho)
        if start_ts and end_ts:
            params_ganhos["filter[closed_at][from]"] = start_ts
            params_ganhos["filter[closed_at][to]"] = end_ts
        
        logger.info(f"🔍 Buscando ganhos: {endpoint_ganhos}")
        response_ganhos = kommo._request_get_all_pages(endpoint_ganhos, params_ganhos)
        logger.info(f"📦 Resposta ganhos: total {len(response_ganhos.get('_embedded', {}).get('leads', []))} leads")
        won_leads_raw = response_ganhos.get('_embedded', {}).get('leads', [])
        # Dedupe por ID para evitar duplicatas entre páginas
        seen_ids = set()
        won_leads = []
        for l in won_leads_raw:
            lid = l.get('id')
            if lid and lid not in seen_ids:
                seen_ids.add(lid)
                won_leads.append(l)
        logger.info(f"✅ Total de ganhos encontrados: {len(won_leads)}")
        won_df = ExportEngine._leads_to_dataframe(won_leads, kommo)
        won_files = ExportEngine._save_both_formats(
            won_df, 
            client_dir, 
            f"{client_id}_ganhos_{timestamp}"
        )
        
        # 2. PERDIDOS - apenas pipeline principal, filtrando por closed_at
        endpoint_perdidos = f"{kommo.base_url}/leads"
        params_perdidos = {
            "filter[pipeline_id][0]": pipeline_id,
            "filter[status][0]": lost_status_id,
            "with": "contacts"
        }
        if start_ts and end_ts:
            params_perdidos["filter[closed_at][from]"] = start_ts
            params_perdidos["filter[closed_at][to]"] = end_ts
        response_perdidos = kommo._request_get_all_pages(endpoint_perdidos, params_perdidos)
        lost_leads_raw = response_perdidos.get('_embedded', {}).get('leads', [])
        seen_ids = set()
        lost_leads = []
        for l in lost_leads_raw:
            lid = l.get('id')
            if lid and lid not in seen_ids:
                seen_ids.add(lid)
                lost_leads.append(l)
        lost_df = ExportEngine._leads_to_dataframe(lost_leads, kommo)
        lost_files = ExportEngine._save_both_formats(
            lost_df, 
            client_dir, 
            f"{client_id}_perdidos_{timestamp}"
        )
        
        # 3. PERDIDOS FOLLOW-UP (todas as pipelines de follow-up com status perdido)
        lost_followup_leads = []
        for fup_id in followup_pipeline_ids:
            endpoint_fup = f"{kommo.base_url}/leads"
            params_fup_closed = {
                "filter[pipeline_id][0]": fup_id,
                "filter[status][0]": lost_status_id,
                "with": "contacts"
            }
            params_fup_updated = params_fup_closed.copy()
            # Filtra pela data de fechamento (quando virou perdido) e fallback updated_at
            if start_ts and end_ts:
                params_fup_closed["filter[closed_at][from]"] = start_ts
                params_fup_closed["filter[closed_at][to]"] = end_ts
                params_fup_updated["filter[updated_at][from]"] = start_ts
                params_fup_updated["filter[updated_at][to]"] = end_ts
            
            response_fup_closed = kommo._request_get_all_pages(endpoint_fup, params_fup_closed)
            response_fup_updated = kommo._request_get_all_pages(endpoint_fup, params_fup_updated)
            lost_fup_raw = []
            lost_fup_raw.extend(response_fup_closed.get('_embedded', {}).get('leads', []))
            lost_fup_raw.extend(response_fup_updated.get('_embedded', {}).get('leads', []))
            # Dedupe incremental
            existing = {l.get('id') for l in lost_followup_leads}
            for l in lost_fup_raw:
                lid = l.get('id')
                if lid and lid not in existing:
                    lost_followup_leads.append(l)
                    existing.add(lid)
        
        lost_fup_df = ExportEngine._leads_to_dataframe(lost_followup_leads, kommo)
        lost_fup_files = ExportEngine._save_both_formats(
            lost_fup_df, 
            client_dir, 
            f"{client_id}_perdidos_followup_{timestamp}"
        )
        
        # 4. ATIVOS - pipeline principal exceto ganhos/perdidos
        endpoint_ativos = f"{kommo.base_url}/leads"
        params_ativos = {
            "filter[pipeline_id][0]": pipeline_id,
            "with": "contacts"
        }
        response_ativos = kommo._request_get_all_pages(endpoint_ativos, params_ativos)
        all_leads_raw = response_ativos.get('_embedded', {}).get('leads', [])
        seen_ids = set()
        all_leads = []
        for l in all_leads_raw:
            lid = l.get('id')
            if lid and lid not in seen_ids:
                seen_ids.add(lid)
                all_leads.append(l)
        active_leads = [
            l for l in all_leads 
            if str(l.get('status_id')) not in [str(won_status_id), str(lost_status_id)]
        ]
        active_df = ExportEngine._leads_to_dataframe(active_leads, kommo)
        active_files = ExportEngine._save_both_formats(
            active_df, 
            client_dir, 
            f"{client_id}_ativos_{timestamp}"
        )
        
        logger.info(f"✅ Exportações geradas: {len(won_leads)} ganhos, {len(lost_leads)} perdidos, {len(lost_followup_leads)} follow-up perdidos, {len(active_leads)} ativos")
        
        return {
            "ganhos": won_files,
            "perdidos": lost_files,
            "perdidos_followup": lost_fup_files,
            "ativos": active_files,
        }
    
    @staticmethod
    def _extract_contact(lead: dict) -> str:
        """
        Extrai o contato do lead a partir dos campos customizados.
        Busca por email ou telefone, validando o formato.
        Telefones são formatados para +55...
        Retorna string vazia se não encontrar contato válido.
        """
        custom_fields = lead.get('custom_fields_values', [])
        
        contacts = []
        
        if custom_fields:
            for field in custom_fields:
                values = field.get('values', [])
                if values:
                    contact_value = values[0].get('value', '').strip()
                    if contact_value:
                        contacts.append(contact_value)
        
        # Priorizar email sobre telefone
        for contact in contacts:
            if ExportEngine._is_valid_email(contact):
                return contact
        
        for contact in contacts:
            if ExportEngine._is_valid_phone(contact):
                return ExportEngine._format_phone(contact)
        
        return ""
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Valida formato de email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Valida formato de telefone (pode incluir números e alguns caracteres especiais)"""
        # Remove espaços e caracteres comuns em telefones
        clean_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
        # Verifica se tem entre 10 e 15 dígitos (padrão internacional)
        return bool(re.match(r'^\d{10,15}$', clean_phone)) and len(clean_phone) >= 10
    
    @staticmethod
    def _format_phone(phone: str) -> str:
        """
        Formata o telefone para o padrão internacional +55...
        Exemplos:
        - 11987654321 → +5511987654321
        - (11) 9876-5432 → +5511987654321
        - +55 11 98765-4321 → +5511987654321
        - 5511987654321 → +5511987654321
        """
        # Remove todos os caracteres especiais
        clean_phone = re.sub(r'[\s\-\(\)\.+]', '', phone)
        
        # Remove o código do país se já existir
        if clean_phone.startswith('55'):
            clean_phone = clean_phone[2:]
        
        # Garante que temos 11 dígitos (DDD + número)
        # Se tiver menos, assume que está incompleto
        # Se tiver mais, pega os últimos 11
        if len(clean_phone) > 11:
            clean_phone = clean_phone[-11:]
        elif len(clean_phone) < 11:
            # Se tiver menos de 11, não formata
            return ""
        
        # Formata com o código do país Brasil
        return f"+55{clean_phone}"
    
    @staticmethod
    def _leads_to_dataframe(leads: list, kommo_client=None) -> pd.DataFrame:
        """
        Converte lista de leads em DataFrame com Nome e Telefone do contato.
        """
        if not leads:
            return pd.DataFrame(columns=["Nome", "Telefone"])
        
        # Extrair todos os IDs de contatos únicos
        all_contact_ids = []
        lead_contact_map = {}  # Mapeia lead_id -> contact_id principal
        
        for lead in leads:
            contact_ids = ExportEngine._extract_contact_ids(lead)
            if contact_ids:
                lead_id = lead.get('id')
                lead_contact_map[lead_id] = contact_ids[0]  # Primeiro contato (principal)
                if contact_ids[0] not in all_contact_ids:
                    all_contact_ids.append(contact_ids[0])
        
        # Buscar todos os contatos em lotes de até 250 IDs
        contacts_data = {}
        if all_contact_ids and kommo_client:
            BATCH = 250
            for i in range(0, len(all_contact_ids), BATCH):
                chunk_ids = all_contact_ids[i:i+BATCH]
                contacts_list = kommo_client.get_contacts_batch(chunk_ids)
                if contacts_list:
                    for contact in contacts_list:
                        contact_id = contact.get('id')
                        if contact_id:
                            contacts_data[contact_id] = contact
        
        # Montar as linhas do DataFrame
        rows = []
        for lead in leads:
            lead_id = lead.get('id')
            nome = ""
            telefone = ""
            
            # Se tem contato vinculado, busca dados do contato
            if lead_id in lead_contact_map:
                contact_id = lead_contact_map[lead_id]
                contact = contacts_data.get(contact_id)
                if contact:
                    nome = contact.get('name', '')
                    telefone = ExportEngine._extract_phone_from_contact(contact)
            
            # Se não encontrou dados no contato, usa nome do lead
            if not nome:
                nome = lead.get('name', 'Sem nome').strip()
            
            rows.append({
                "Nome": nome,
                "Telefone": telefone,
            })
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def _extract_contact_ids(lead: dict) -> list:
        """
        Extrai os IDs dos contatos vinculados ao lead.
        """
        embedded = lead.get('_embedded', {})
        contacts = embedded.get('contacts', [])
        
        contact_ids = []
        for contact in contacts:
            contact_id = contact.get('id')
            if contact_id:
                contact_ids.append(contact_id)
        
        return contact_ids
    
    @staticmethod
    def _extract_phone_from_contact(contact: dict) -> str:
        """
        Extrai o telefone dos custom_fields_values do contato.
        Retorna exatamente como vem da API.
        """
        custom_fields = contact.get('custom_fields_values', [])
        
        if not custom_fields:
            return ""
        
        for field in custom_fields:
            field_code = field.get('field_code')
            # Telefone tem field_code 'PHONE'
            if field_code == 'PHONE':
                values = field.get('values', [])
                if values:
                    phone_value = values[0].get('value', '').strip()
                    if phone_value:
                        return phone_value
        
        return ""
    
    @staticmethod
    def _save_both_formats(df: pd.DataFrame, directory: str, filename: str) -> dict:
        """Salva DataFrame em Excel e CSV, retorna paths"""
        excel_path = os.path.join(directory, f"{filename}.xlsx")
        csv_path = os.path.join(directory, f"{filename}.csv")
        
        # Salvar Excel
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        # Salvar CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return {
            "excel": excel_path,
            "csv": csv_path
        }
