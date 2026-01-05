from datetime import datetime, timedelta, time
import calendar

class DateHelper:
    @staticmethod
    def get_timestamps_for_report(report_type="weekly"):
        now = datetime.now()
        
        if report_type == "weekly":
            # Domingo desta semana (início)
            # weekday(): Segunda=0, ..., Domingo=6
            # Se hoje é segunda(0), domingo foi ontem (-1)
            days_to_subtract = (now.weekday() + 1) % 7
            current_sunday = now - timedelta(days=days_to_subtract)
            start_current = current_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Semana Anterior (Domingo retrasado até o último sábado)
            start_last_week = start_current - timedelta(days=7)
            end_last_week = start_current - timedelta(seconds=1)
            
            return {
                "current": (int(start_current.timestamp()), int(now.timestamp())),
                "previous": (int(start_last_week.timestamp()), int(end_last_week.timestamp()))
            }

        elif report_type == "monthly":
            # Primeiro dia do mês passado
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(seconds=1)
            first_day_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            return {
                "previous_month": (int(first_day_last_month.timestamp()), int(last_day_last_month.timestamp()))
            }
        
        elif report_type == "annual":
            # 1º de Janeiro do ano passado até 31 de Dezembro do ano passado
            last_year = now.year - 1
            start_year = datetime(last_year, 1, 1, 0, 0, 0)
            end_year = datetime(last_year, 12, 31, 23, 59, 59)
            
            return {
                "previous_year": (int(start_year.timestamp()), int(end_year.timestamp()))
            }
    
        return None