import os
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
    def _leads_to_dataframe(leads: list) -> pd.DataFrame:
        """Converte lista de leads em DataFrame com colunas principais"""
        if not leads:
            return pd.DataFrame(columns=["ID", "Nome", "Valor", "Status", "Responsável", "Criado em", "Atualizado em"])
        
        rows = []
        for lead in leads:
            rows.append({
                "ID": lead.get('id'),
                "Nome": lead.get('name', 'Sem nome'),
                "Valor": lead.get('price', 0),
                "Status": lead.get('status_id'),
                "Responsável": lead.get('responsible_user_id'),
                "Criado em": datetime.fromtimestamp(lead.get('created_at', 0)).strftime("%Y-%m-%d %H:%M:%S") if lead.get('created_at') else "",
                "Atualizado em": datetime.fromtimestamp(lead.get('updated_at', 0)).strftime("%Y-%m-%d %H:%M:%S") if lead.get('updated_at') else "",
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
