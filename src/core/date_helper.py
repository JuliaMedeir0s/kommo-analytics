from datetime import datetime, timedelta, time
import calendar

class DateHelper:
    @staticmethod
    def get_timestamps_for_report(report_type="weekly"):
        now = datetime.now()

        if report_type == "weekly":
            # Domingo desta semana (início)
            days_to_subtract = (now.weekday() + 1) % 7
            current_sunday = now - timedelta(days=days_to_subtract)
            start_current = current_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
            return int(start_current.timestamp()), int(now.timestamp())

        if report_type == "last_week":
            days_to_subtract = (now.weekday() + 1) % 7
            current_sunday = now - timedelta(days=days_to_subtract)
            start_last_week = current_sunday - timedelta(days=7)
            end_last_week = current_sunday - timedelta(seconds=1)
            return int(start_last_week.timestamp()), int(end_last_week.timestamp())

        if report_type in ("monthly", "last_month"):
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(seconds=1)
            first_day_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return int(first_day_last_month.timestamp()), int(last_day_last_month.timestamp())

        if report_type in ("current_month", "month_to_date"):
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return int(first_day_this_month.timestamp()), int(now.timestamp())

        if report_type == "last_month":
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(seconds=1)
            first_day_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return int(first_day_last_month.timestamp()), int(last_day_last_month.timestamp())

        if report_type in ("yearly", "year_to_date"):
            start_year = datetime(now.year, 1, 1, 0, 0, 0)
            return int(start_year.timestamp()), int(now.timestamp())

        if report_type in ("last_year", "annual"):
            last_year = now.year - 1
            start_year = datetime(last_year, 1, 1, 0, 0, 0)
            end_year = datetime(last_year, 12, 31, 23, 59, 59)
            return int(start_year.timestamp()), int(end_year.timestamp())

        return None