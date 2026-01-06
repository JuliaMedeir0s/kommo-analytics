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
        
        # Buscar todos os leads da pipeline principal
        all_leads = kommo.get_leads(start_ts=start_ts, end_ts=end_ts, pipeline_id=pipeline_id)
        
        # 1. GANHOS (won_status_id)
        won_leads = [l for l in all_leads if str(l.get('status_id')) == str(won_status_id)]
        won_df = ExportEngine._leads_to_dataframe(won_leads)
        won_files = ExportEngine._save_both_formats(
            won_df, 
            client_dir, 
            f"{client_id}_ganhos_{timestamp}"
        )
        
        # 2. PERDIDOS da pipeline principal (lost_status_id)
        lost_leads = [l for l in all_leads if str(l.get('status_id')) == str(lost_status_id)]
        lost_df = ExportEngine._leads_to_dataframe(lost_leads)
        lost_files = ExportEngine._save_both_formats(
            lost_df, 
            client_dir, 
            f"{client_id}_perdidos_{timestamp}"
        )
        
        # 3. PERDIDOS FOLLOW-UP (todas as pipelines de follow-up com status perdido)
        lost_followup_leads = []
        for fup_id in followup_pipeline_ids:
            fup_leads = kommo.get_leads(start_ts=start_ts, end_ts=end_ts, pipeline_id=fup_id)
            lost_fup = [l for l in fup_leads if str(l.get('status_id')) == str(lost_status_id)]
            lost_followup_leads.extend(lost_fup)
        
        lost_fup_df = ExportEngine._leads_to_dataframe(lost_followup_leads)
        lost_fup_files = ExportEngine._save_both_formats(
            lost_fup_df, 
            client_dir, 
            f"{client_id}_perdidos_followup_{timestamp}"
        )
        
        # 4. ATIVOS (todos que não são ganhos nem perdidos na pipeline principal)
        active_leads = [
            l for l in all_leads 
            if str(l.get('status_id')) not in [str(won_status_id), str(lost_status_id)]
        ]
        active_df = ExportEngine._leads_to_dataframe(active_leads)
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
    def _leads_to_dataframe(leads: list) -> pd.DataFrame:
        """
        Converte lista de leads em DataFrame apenas com Nome e Contato validado.
        """
        if not leads:
            return pd.DataFrame(columns=["Nome", "Contato"])
        
        rows = []
        for lead in leads:
            name = lead.get('name', 'Sem nome').strip()
            contact = ExportEngine._extract_contact(lead)
            
            # Apenas inclui o lead se tiver nome e contato válido
            if name and contact:
                rows.append({
                    "Nome": name,
                    "Contato": contact,
                })
        
        return pd.DataFrame(rows)
    
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
