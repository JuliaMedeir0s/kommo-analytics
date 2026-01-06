import requests
import os
from datetime import datetime

class KommoClient:
    def __init__(self, subdomain, api_token):
        self.base_url = f"https://{subdomain}.kommo.com/api/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_leads(self, start_ts: int = None, end_ts: int = None, pipeline_id: int = None):
        """
        Busca leads criados em um período e em uma pipeline específica.
        Se start_ts/end_ts forem None, busca todos os leads.
        """
        endpoint = f"{self.base_url}/leads"
        params = {}
        
        if start_ts is not None:
            params["filter[created_at][from]"] = start_ts
        if end_ts is not None:
            params["filter[created_at][to]"] = end_ts
        if pipeline_id is not None:
            params["filter[pipeline_id][0]"] = pipeline_id
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('_embedded', {}).get('leads', [])
        return []
    
    def get_unsorted_leads(self, filter_date_from: int, filter_date_to: int):
        """
        Busca leads que estão na 'Entrada' (Unsorted).
        """
        endpoint = f"{self.base_url}/leads/unsorted"
        params = {
            "filter[created_at][from]": filter_date_from,
            "filter[created_at][to]": filter_date_to
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            # O retorno do unsorted é um pouco diferente do leads comum
            return response.json().get('_embedded', {}).get('unsorted', [])
        return []

    def get_won_leads(self, filter_date_from: int, filter_date_to: int, pipeline_id: int):
        """
        Busca leads que foram ganhos em um período e em uma pipeline específica.
        """
        endpoint = f"{self.base_url}/leads"
        params = {
            "filter[pipeline_id][0]": pipeline_id,
            "filter[status][0]": 142,
            "filter[closed_at][from]": filter_date_from,
            "filter[closed_at][to]": filter_date_to
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('_embedded', {}).get('leads', [])
        return []

    def get_lost_leads(self, filter_date_from: int, filter_date_to: int, pipeline_id: int):
        """
        Busca leads que foram perdidos em um período e em uma pipeline específica.
        Status 143 representa 'Lost' no Kommo.
        """
        endpoint = f"{self.base_url}/leads"
        params = {
            "filter[pipeline_id][0]": pipeline_id,
            "filter[status][0]": 143,
            "filter[closed_at][from]": filter_date_from,
            "filter[closed_at][to]": filter_date_to
        }

        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json().get('_embedded', {}).get('leads', [])
        return []
    
    def get_lead_custom_fields(self):
        """
        Identifica o ID do campo 'Origem'
        """
        endpoint = f"{self.base_url}/leads/custom_fields"
        response = requests.get(endpoint, headers=self.headers)
        return response.json()
    
    def health_check(self):
        """
        Verifica se o token e o subdomínio estão válidos.
        """
        endpoint = f"{self.base_url}/account"
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return True, f"Conectado à conta: {data.get('name')}"
            return False, f"Erro na conexão: Status {response.status_code}"
        except Exception as e:
            return False, str(e)