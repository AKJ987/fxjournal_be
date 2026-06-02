from django.core.management.base import BaseCommand
from tradejournal.models import Instrument


class Command(BaseCommand):
    help = "Seed forex instruments into Instrument table"

    def handle(self, *args, **kwargs):

        FOREX_INSTRUMENTS = [
            # Major pairs
            {"code": "EURUSD", "name": "EUR/USD", "pip_size": 0.0001},
            {"code": "GBPUSD", "name": "GBP/USD", "pip_size": 0.0001},
            {"code": "USDJPY", "name": "USD/JPY", "pip_size": 0.01},
            {"code": "USDCHF", "name": "USD/CHF", "pip_size": 0.0001},
            {"code": "AUDUSD", "name": "AUD/USD", "pip_size": 0.0001},
            {"code": "USDCAD", "name": "USD/CAD", "pip_size": 0.0001},
            {"code": "NZDUSD", "name": "NZD/USD", "pip_size": 0.0001},

            # Cross majors
            {"code": "EURGBP", "name": "EUR/GBP", "pip_size": 0.0001},
            {"code": "EURJPY", "name": "EUR/JPY", "pip_size": 0.01},
            {"code": "EURCHF", "name": "EUR/CHF", "pip_size": 0.0001},
            {"code": "EURAUD", "name": "EUR/AUD", "pip_size": 0.0001},
            {"code": "EURCAD", "name": "EUR/CAD", "pip_size": 0.0001},
            {"code": "EURNZD", "name": "EUR/NZD", "pip_size": 0.0001},

            {"code": "GBPJPY", "name": "GBP/JPY", "pip_size": 0.01},
            {"code": "GBPCHF", "name": "GBP/CHF", "pip_size": 0.0001},
            {"code": "GBPAUD", "name": "GBP/AUD", "pip_size": 0.0001},
            {"code": "GBPCAD", "name": "GBP/CAD", "pip_size": 0.0001},
            {"code": "GBPNZD", "name": "GBP/NZD", "pip_size": 0.0001},

            {"code": "AUDJPY", "name": "AUD/JPY", "pip_size": 0.01},
            {"code": "AUDCHF", "name": "AUD/CHF", "pip_size": 0.0001},
            {"code": "AUDCAD", "name": "AUD/CAD", "pip_size": 0.0001},
            {"code": "AUDNZD", "name": "AUD/NZD", "pip_size": 0.0001},

            {"code": "CADJPY", "name": "CAD/JPY", "pip_size": 0.01},
            {"code": "CHFJPY", "name": "CHF/JPY", "pip_size": 0.01},

            {"code": "NZDJPY", "name": "NZD/JPY", "pip_size": 0.01},
            {"code": "NZDCHF", "name": "NZD/CHF", "pip_size": 0.0001},
            {"code": "NZDCAD", "name": "NZD/CAD", "pip_size": 0.0001},
        ]

        created_count = 0

        for item in FOREX_INSTRUMENTS:
            obj, created = Instrument.objects.get_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "pip_size": item["pip_size"],
                }
            )

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Instrument: {created_count} created successfully!")
        )