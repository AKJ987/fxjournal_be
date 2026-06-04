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

        errors = {}

        # Closed trade validations
        if status == "CLOSED":
            if not exit_date:
                errors["exit_date"] = "Exit date is required for closed trades."

            if not exit_time:
                errors["exit_time"] = "Exit time is required for closed trades."

            if exit_price is None:
                errors["exit_price"] = "Exit price is required for closed trades."

        # Exit datetime >= Entry datetime
        if (entry_date and entry_time and exit_date and exit_time):
            # Combine date and time
            entry_dt = datetime.combine(entry_date, entry_time)
            exit_dt = datetime.combine(exit_date, exit_time)

            if exit_dt < entry_dt:
                errors["exit_date"] = (
                    "Exit date and time must be greater than or equal to entry date and time."
                )

        # BUY validations
        if (direction == "BUY" and entry_price is not None):
            if (
                take_profit is not None
                and take_profit <= entry_price
            ):
                errors["take_profit"] = (
                    "For BUY trades, take profit must be greater than entry price."
                )
            if (
                stop_loss is not None
                and stop_loss >= entry_price
            ):
                errors["stop_loss"] = (
                    "For BUY trades, stop loss must be less than entry price."
                )

        # SELL validations
        if (direction == "SELL" and entry_price is not None):
            if (
                take_profit is not None
                and take_profit >= entry_price
            ):
                errors["take_profit"] = (
                    "For SELL trades, take profit must be less than entry price."
                )
            if (
                stop_loss is not None
                and stop_loss <= entry_price
            ):
                errors["stop_loss"] = (
                    "For SELL trades, stop loss must be greater than entry price."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        setup_data = validated_data.pop("setup", None)
        psychology_data = validated_data.pop("psychology", None)
        screenshots_data = validated_data.pop("screenshots", [])

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
            "result"
        ]
