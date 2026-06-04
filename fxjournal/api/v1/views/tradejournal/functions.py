from django.db.models import (
    Case, DecimalField, ExpressionWrapper, F, Value, When,
    CharField
)
from django.db.models.functions import Round


def annotate_trade_performance(queryset):
    """
    Annotates net_pnl and result directly on the queryset using DB expressions.
    Mirrors the logic in calculate_trade_performance().
    """

    # Pips: (exit - entry) / pip_size for BUY, (entry - exit) / pip_size for SELL
    pips_expr = Case(
        When(
            direction="BUY",
            then=(F("exit_price") - F("entry_price")) / F("instrument__pip_size"),
        ),
        default=(F("entry_price") - F("exit_price")) / F("instrument__pip_size"),
        output_field=DecimalField(),
    )

    # pip_value = (pip_size / exchange_rate) * contract_size
    pip_value_expr = ExpressionWrapper(
        (F("instrument__pip_size") / F("exchange_rate")) * F("instrument__contract_size"),
        output_field=DecimalField(),
    )

    # gross_pnl = pips * pip_value * lot_size
    gross_pnl_expr = ExpressionWrapper(
        pips_expr * pip_value_expr * F("lot_size"),
        output_field=DecimalField(),
    )

    # net_pnl = round(gross_pnl - total_fees, 2)
    net_pnl_expr = Round(
        ExpressionWrapper(
            gross_pnl_expr - F("total_fees"),
            output_field=DecimalField(),
        ),
        precision=2,
    )

    # result = WIN / LOSS / BREAKEVEN based on net_pnl
    result_expr = Case(
        When(net_pnl__gt=0, then=Value("WIN")),
        When(net_pnl__lt=0, then=Value("LOSS")),
        When(net_pnl=0, then=Value("BREAKEVEN")),
        default=Value(None),
        output_field=CharField(),
    )

    return (
        queryset
        .annotate(net_pnl=net_pnl_expr)
        .annotate(result=result_expr)
    )
