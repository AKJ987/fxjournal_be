from rest_framework import serializers
from django.db import transaction
from datetime import datetime

from tradejournal.models import (
    Trade,
    TradeSetup,
    PsychologyJournal,
    TradeScreenshot
)


class TradeSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeSetup
        exclude = ["trade"]
        extra_kwargs = {
            "strategy": {"required": True},
            "timeframe": {"required": True},
            "market_session": {"required": True},
            "market_condition": {"required": True},
        }


class PsychologyJournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PsychologyJournal
        exclude = ["trade"]
        extra_kwargs = {
            "confidence_level": {"required": True},
            "emotional_state": {"required": True},
            "stress_level": {"required": True},
            "followed_trading_plan": {"required": True},
        }


class TradeCreateUpdateSerializer(serializers.ModelSerializer):
    setup = TradeSetupSerializer(required=True)
    psychology = PsychologyJournalSerializer(required=True)
    screenshots = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
    )
    deleted_screenshots = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )

    class Meta:
        model = Trade
        exclude = ["trade_id", "user"]
        extra_kwargs = {
            "entry_date": {"required": True},
            "entry_time": {"required": True},
            "broker": {"required": True},
            "instrument": {"required": True},
            "exchange_rate": {"required": True},
            "direction": {"required": True},
            "lot_size": {"required": True},
            "leverage": {"required": True},
            "entry_price": {"required": True},
            "status": {"required": True},
            "stop_loss": {"required": True},
            "take_profit": {"required": True},
        }

    def validate(self, attrs):
        entry_date = attrs.get("entry_date")
        entry_time = attrs.get("entry_time")
        exit_date = attrs.get("exit_date")
        exit_time = attrs.get("exit_time")
        entry_price = attrs.get("entry_price")
        stop_loss = attrs.get("stop_loss")
        take_profit = attrs.get("take_profit")
        direction = attrs.get("direction")
        status = attrs.get("status")
        exit_price = attrs.get("exit_price")

        # Closed trade validations
        if status == "CLOSED":
            if not exit_date:
                raise serializers.ValidationError(
                    {"error": "Exit date is required for closed trades."}
                )

            if not exit_time:
                raise serializers.ValidationError(
                    {"error": "Exit time is required for closed trades."}
                )

            if exit_price is None:
                raise serializers.ValidationError(
                    {"error": "Exit price is required for closed trades."}
                )

        # Exit datetime >= Entry datetime
        if entry_date and entry_time and exit_date and exit_time:
            entry_dt = datetime.combine(entry_date, entry_time)
            exit_dt = datetime.combine(exit_date, exit_time)

            if exit_dt < entry_dt:
                raise serializers.ValidationError(
                    {"error": (
                        "Exit date and time must be greater than or equal "
                        "to entry date and time."
                    )}
                )

        # BUY validations
        if direction == "BUY" and entry_price is not None:
            if take_profit is not None and take_profit <= entry_price:
                raise serializers.ValidationError(
                    {"error": (
                        "For BUY trades, take profit must be greater than "
                        "entry price."
                    )}
                )

            if stop_loss is not None and stop_loss >= entry_price:
                raise serializers.ValidationError(
                    {"error": (
                        "For BUY trades, stop loss must be less than "
                        "entry price."
                    )}
                )

        # SELL validations
        if direction == "SELL" and entry_price is not None:
            if take_profit is not None and take_profit >= entry_price:
                raise serializers.ValidationError(
                    {"error": (
                        "For SELL trades, take profit must be less than "
                        "entry price."
                    )}
                )

            if stop_loss is not None and stop_loss <= entry_price:
                raise serializers.ValidationError(
                    {"error": (
                        "For SELL trades, stop loss must be greater than "
                        "entry price."
                    )}
                )
        return attrs

    def _handle_open_trade_cleanup(self, validated_data, psychology_data):
        """
        Clears exit + psychology fields when trade status is OPEN.
        """
        if validated_data.get("status") == "OPEN":
            validated_data.update({
                "exit_date": None,
                "exit_time": None,
                "exit_price": None,
                "total_fees": None,
            })

            if psychology_data:
                psychology_data.update({
                    "emotion_after_trade": None,
                    "mistakes_made": None,
                    "lessons_learned": None,
                    "what_went_well": None,
                    "improvement_plan": None,
                })

    @transaction.atomic
    def create(self, validated_data):
        setup_data = validated_data.pop("setup", None)
        psychology_data = validated_data.pop("psychology", None)
        screenshots_data = validated_data.pop("screenshots", [])

        self._handle_open_trade_cleanup(validated_data, psychology_data)

        trade = Trade.objects.create(
            user=self.context["request"].user,
            **validated_data
        )

        if setup_data:
            TradeSetup.objects.create(
                trade=trade,
                **setup_data
            )

        if psychology_data:
            PsychologyJournal.objects.create(
                trade=trade,
                **psychology_data
            )

        for screenshot in screenshots_data:
            TradeScreenshot.objects.create(
                trade=trade,
                file_name=screenshot.name,
                image=screenshot
            )

        self.response_data = {"id": trade.id}
        return trade

    @transaction.atomic
    def update(self, instance, validated_data):
        setup_data = validated_data.pop("setup", None)
        psychology_data = validated_data.pop("psychology", None)
        screenshots_data = validated_data.pop("screenshots", [])
        deleted_screenshots = validated_data.pop("deleted_screenshots", [])

        self._handle_open_trade_cleanup(validated_data, psychology_data)

        # Update Trade fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update/Create Trade Setup
        if setup_data:
            TradeSetup.objects.update_or_create(
                trade=instance,
                defaults=setup_data,
            )

        # Update/Create Psychology Journal
        if psychology_data:
            PsychologyJournal.objects.update_or_create(
                trade=instance,
                defaults=psychology_data,
            )

        if deleted_screenshots:
            screenshots_to_delete = TradeScreenshot.objects.filter(
                id__in=deleted_screenshots,
                trade=instance
            )
            for screenshot in screenshots_to_delete:
                screenshot.image.delete(save=False)
                screenshot.delete()

        # Create new screenshots
        for screenshot in screenshots_data:
            TradeScreenshot.objects.create(
                trade=instance,
                file_name=screenshot.name,
                image=screenshot
            )

        self.response_data = {"id": instance.id}
        return instance

    def to_representation(self, instance):
        # Return the custom response data
        return getattr(self, "response_data", {})


class TradeListSerializer(serializers.ModelSerializer):
    instrument = serializers.CharField(source="instrument.name")
    net_pnl = serializers.DecimalField(max_digits=20, decimal_places=2)
    result = serializers.CharField()

    class Meta:
        model = Trade
        fields = [
            "id",
            "trade_id",
            "entry_date",
            "instrument",
            "direction",
            "status",
            "net_pnl",
            "result",
            "object_id"
        ]


class TradeDetailSerializer(serializers.ModelSerializer):
    instrument = serializers.CharField(source="instrument.name", default=None)
    strategy = serializers.CharField(source="setup.strategy.name", default=None)
    timeframe = serializers.CharField(source="setup.timeframe.name", default=None)
    market_session = serializers.CharField(source="setup.market_session.name", default=None)
    market_condition = serializers.CharField(source="setup.market_condition.name", default=None)
    entry_reason = serializers.CharField(source="setup.entry_reason", default=None)
    confidence_level = serializers.IntegerField(source="psychology.confidence_level", default=None)
    emotional_state = serializers.CharField(source="psychology.emotional_state", default=None)
    stress_level = serializers.CharField(source="psychology.stress_level", default=None)
    followed_trading_plan = serializers.BooleanField(source="psychology.followed_trading_plan", default=None)
    emotion_after_trade = serializers.CharField(source="psychology.emotion_after_trade", default=None)
    mistakes_made = serializers.CharField(source="psychology.mistakes_made", default=None)
    lessons_learned = serializers.CharField(source="psychology.lessons_learned", default=None)
    what_went_well = serializers.CharField(source="psychology.what_went_well", default=None)
    improvement_plan = serializers.CharField(source="psychology.improvement_plan", default=None)
    screenshots = serializers.SerializerMethodField()
    pips = serializers.DecimalField(max_digits=20, decimal_places=2)
    net_pnl = serializers.DecimalField(max_digits=20, decimal_places=2)
    result = serializers.CharField()
    risk = serializers.SerializerMethodField()
    reward = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = [
            "id", "object_id", "trade_id", "status", "direction", "broker",
            "instrument", "entry_date", "entry_time", "exit_date", "exit_time",
            "entry_price", "exit_price", "stop_loss", "take_profit",
            "lot_size", "leverage", "exchange_rate", "total_fees",
            "strategy", "timeframe", "market_session",
            "market_condition", "entry_reason",
            "confidence_level", "emotional_state", "stress_level",
            "followed_trading_plan", "emotion_after_trade", "mistakes_made",
            "lessons_learned", "what_went_well", "improvement_plan",
            "screenshots",
            "risk", "reward",
            "pips", "net_pnl", "result",
            "created_at", "updated_at"
        ]

    def get_screenshots(self, obj):
        return [
            {
                "id": s.id,
                "file_name": s.file_name,
                "image": s.image.url,
            }
            for s in obj.screenshots.all()
        ]
    
    def get_risk(self, obj):
        if not obj.entry_price:
            return None
        return round(abs(obj.entry_price - obj.stop_loss) / obj.instrument.pip_size, 2)

    def get_reward(self, obj):
        if not obj.entry_price:
            return None
        return round(abs(obj.take_profit - obj.entry_price) / obj.instrument.pip_size, 2)


class TradeSetupDetailSerializer(serializers.Serializer):
    strategy = serializers.IntegerField(source="strategy.id")
    timeframe = serializers.IntegerField(source="timeframe.id")
    market_session = serializers.IntegerField(source="market_session.id")
    market_condition = serializers.IntegerField(source="market_condition.id")
    entry_reason = serializers.CharField(allow_null=True)


class PsychologyDetailSerializer(serializers.Serializer):
    confidence_level = serializers.IntegerField()
    emotional_state = serializers.CharField()
    stress_level = serializers.CharField()
    followed_trading_plan = serializers.SerializerMethodField()
    emotion_after_trade = serializers.CharField(allow_null=True)
    mistakes_made = serializers.CharField(allow_null=True)
    lessons_learned = serializers.CharField(allow_null=True)
    what_went_well = serializers.CharField(allow_null=True)
    improvement_plan = serializers.CharField(allow_null=True)

    def get_followed_trading_plan(self, obj):
        return "YES" if obj.followed_trading_plan else "NO"


class TradeUpdateDetailSerializer(serializers.ModelSerializer):
    instrument = serializers.IntegerField(source="instrument.id")
    setup = TradeSetupDetailSerializer(read_only=True)
    psychology = PsychologyDetailSerializer(read_only=True)
    screenshots = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = [
            "entry_date",
            "entry_time",
            "exit_date",
            "exit_time",
            "broker",
            "instrument",
            "exchange_rate",
            "direction",
            "lot_size",
            "leverage",
            "entry_price",
            "exit_price",
            "stop_loss",
            "take_profit",
            "total_fees",
            "status",
            "setup",
            "psychology",
            "screenshots"
        ]

    def get_screenshots(self, obj):
        return [
            {
                "id": screenshot.id,
                "name": screenshot.file_name,
                "image": screenshot.image.url,
                "size": screenshot.image.size,
            }
            for screenshot in obj.screenshots.all()
        ]
