from django.core.management.base import BaseCommand
from tradejournal.models import Strategy, Timeframe, Session, MarketCondition


class Command(BaseCommand):
    help = "Seed Strategy, Timeframe, Session, and MarketCondition tables"

    def handle(self, *args, **kwargs):

        STRATEGIES = [
            ("BREAKOUT", "Breakout"),
            ("PULLBACK", "Pullback"),
            ("TREND", "Trend Following"),
            ("RANGE", "Range Trading"),
            ("ICT", "ICT"),
            ("SMC", "Smart Money Concepts"),
            ("SCALPING", "Scalping"),
            ("SUPPLY_DEMAND", "Supply Demand"),
            ("PRICE_ACTION", "Price Action"),
        ]

        TIMEFRAMES = [
            ("M1", "M1"),
            ("M5", "M5"),
            ("M15", "M15"),
            ("M30", "M30"),
            ("H1", "H1"),
            ("H4", "H4"),
            ("D1", "D1"),
        ]

        SESSIONS = [
            ("SYDNEY", "Sydney"),
            ("TOKYO", "Tokyo"),
            ("LONDON", "London"),
            ("NEWYORK", "New York"),
            ("OVERLAP", "London-New York Overlap"),
        ]

        MARKET_CONDITIONS = [
            ("TRENDING", "Trending"),
            ("RANGING", "Ranging"),
            ("VOLATILE", "Volatile"),
            ("NEWS", "News Driven"),
        ]

        def seed(model, data, model_name):
            created_count = 0

            for code, name in data:
                obj, created = model.objects.get_or_create(
                    code=code,
                    defaults={"name": name}
                )
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f"{model_name}: {created_count} created")
            )

        seed(Strategy, STRATEGIES, "Strategy")
        seed(Timeframe, TIMEFRAMES, "Timeframe")
        seed(Session, SESSIONS, "Session")
        seed(MarketCondition, MARKET_CONDITIONS, "MarketCondition")

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully!"))