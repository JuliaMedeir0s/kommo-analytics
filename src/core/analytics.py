class AnalyticsEngine:
    @staticmethod
    def calculate_efficiency(leads, won_status_id):
        total_leads = len(leads)
        # Filtra leads que estão no status de "Ganho"
        won_leads = [l for l in leads if str(l.get('status_id')) == str(won_status_id)]
        total_won = len(won_leads)
        
        # Evita divisão por zero (ZeroDivisionError)
        ratio = round(total_leads / total_won, 2) if total_won > 0 else float('inf')
        
        return {
            "total_leads": total_leads,
            "total_won": total_won,
            "ratio": ratio
        }

    @staticmethod
    def group_by_origin(leads, origin_field_id):
        origins = {}
        for lead in leads:
            origin_value = "Desconhecido"
            # Navega pelos campos customizados do Kommo
            custom_fields = lead.get('custom_fields_values', [])
            if custom_fields:
                for field in custom_fields:
                    if field.get('field_id') == origin_field_id:
                        # Pega o valor do campo (geralmente na primeira posição da lista)
                        origin_value = field['values'][0]['value']
            
            origins[origin_value] = origins.get(origin_value, 0) + 1
            
        return dict(sorted(origins.items(), key=lambda item: item[1], reverse=True))

    @staticmethod
    def get_first_messages(leads, message_field_id):
        messages = []
        for lead in leads:
            custom_fields = lead.get('custom_fields_values', [])
            if custom_fields:
                for field in custom_fields:
                    if field.get('field_id') == message_field_id:
                        msg = field['values'][0]['value']
                        messages.append(msg[:50] + "...") # Pega só o começo para não ficar gigante
        return messages
    
    @staticmethod
    def calculate_metrics(leads_created, leads_won_in_period, won_status_id):
        # 1. Métrica de Coorte (Eficiência dos novos)
        total_created = len(leads_created)
        new_leads_already_won = [l for l in leads_created if str(l.get('status_id')) == str(won_status_id)]
        
        # 2. Métrica de Volume (Batida de meta real)
        total_closed_won = len(leads_won_in_period)
        
        # 3. O Norte: Quantos leads preciso para 1 venda?
        # Usamos o volume total de fechamento vs o volume total de entrada
        ratio = round(total_created / total_closed_won, 2) if total_closed_won > 0 else float('inf')
        
        return {
            "total_created": total_created,
            "cohort_won": len(new_leads_already_won),
            "total_closed_won": total_closed_won,
            "ratio": ratio
        }
    
    @staticmethod
    def get_origin_value(lead: dict, origin_field_id: int) -> str:
        """
        Extrai o valor do campo de origem de um lead.
        Se não encontrar o campo, retorna "Desconhecido".
        """
        custom_fields = lead.get('custom_fields_values', [])
        if custom_fields:
            for field in custom_fields:
                if field.get('field_id') == origin_field_id:
                    values = field.get('values', [])
                    if values:
                        return values[0].get('value', 'Desconhecido')
        return "Desconhecido"
    
    @staticmethod
    def calculate_efficiency_by_origin(leads_created, leads_won_period, origin_field_id):
        # 1. Conta leads criados por origem
        created_by_origin = {}
        for l in leads_created:
            origin = AnalyticsEngine.get_origin_value(l, origin_field_id)
            created_by_origin[origin] = created_by_origin.get(origin, 0) + 1
            
        # 2. Conta leads ganhos por origem (mesmo que tenham sido criados antes)
        won_by_origin = {}
        for l in leads_won_period:
            origin = AnalyticsEngine.get_origin_value(l, origin_field_id)
            won_by_origin[origin] = won_by_origin.get(origin, 0) + 1
            
        # 3. Calcula o ratio por origem
        efficiency = {}
        for origin, count in created_by_origin.items():
            won = won_by_origin.get(origin, 0)
            ratio = round(count / won, 2) if won > 0 else "N/A"
            efficiency[origin] = {"leads": count, "ratio": ratio}
            
        return efficiency