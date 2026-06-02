from django.db import models
from accounts.models import User


class Instrument(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    pip_size = models.DecimalField(
        max_digits=10,
        decimal_places=5
    )


class Strategy(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Timeframe(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Session(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MarketCondition(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Trade(models.Model):
    DIRECTION_CHOICES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="trades"
    )
    trade_id = models.CharField(
        max_length=30,
        unique=True
    )
    entry_date = models.DateField(
        null=True,
        blank=True
    )
    entry_time = models.TimeField(
        null=True,
        blank=True
    )
    exit_date = models.DateField(
        null=True,
        blank=True
    )
    exit_time = models.TimeField(
        null=True,
        blank=True
    )
    broker = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="trades",
        null=True,
        blank=True
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        null=True,
        blank=True
    )
    lot_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    leverage = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    entry_price = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True
    )
    exit_price = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True
    )
    stop_loss = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True
    )
    take_profit = models.DecimalField(
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="OPEN"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.trade_id:
            last_trade = Trade.objects.order_by("-id").only("trade_id").first()
            next_id = (
                int(last_trade.trade_id.split("-")[1]) + 1
                if last_trade and last_trade.trade_id
                else 1
            )
            self.trade_id = f"T-{next_id:03d}"

        super().save(*args, **kwargs)


class TradeSetup(models.Model):
    trade = models.OneToOneField(
        Trade,
        on_delete=models.CASCADE,
        related_name="setup"
    )
    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.CASCADE,
        related_name="setup",
        null=True,
        blank=True
    )
    timeframe = models.ForeignKey(
        Timeframe,
        on_delete=models.CASCADE,
        related_name="setup",
        null=True,
        blank=True
    )
    market_session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="setup",
        null=True,
        blank=True
    )
    entry_reason = models.TextField(
        null=True,
        blank=True
    )
    market_condition = models.ForeignKey(
        MarketCondition,
        on_delete=models.CASCADE,
        related_name="setup",
        null=True,
        blank=True
    )


class PsychologyJournal(models.Model):
    STRESS_LEVEL = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High")
    ]
    trade = models.OneToOneField(
        Trade,
        on_delete=models.CASCADE,
        related_name="psychology"
    )
    confidence_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )
    emotional_state = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    stress_level = models.CharField(
        max_length=10,
        choices=STRESS_LEVEL,
        null=True,
        blank=True
    )
    followed_trading_plan = models.BooleanField(
        default=False
    )
    emotion_after_trade = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    mistakes_made = models.TextField(
        null=True,
        blank=True
    )
    lessons_learned = models.TextField(
        null=True,
        blank=True
    )
    what_went_well = models.TextField(
        null=True,
        blank=True
    )
    improvement_plan = models.TextField(
        null=True,
        blank=True
    )


class TradeScreenshot(models.Model):
    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name="screenshots"
    )
    file_name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='documents/')
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )
