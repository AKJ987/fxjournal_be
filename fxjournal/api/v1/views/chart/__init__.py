import math
from django.db.models import Count, Sum, Q, DecimalField, Avg, Max, Min
from django.db.models.functions import Round
from rest_framework.views import APIView
from rest_framework.response import Response
from decimal import Decimal
from utils.functions import annotate_trade_performance
from tradejournal.models import Trade


class TradeStatsListAPIView(APIView):
    """
    API view for listing card data in trade list page.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user)
        )

        stats = qs.aggregate(
            total_trades=Count("id"),
            win_count=Count("id", filter=Q(result="WIN")),
            non_breakeven_count=Count("id", filter=~Q(result="BREAKEVEN")),
            total_profit=Sum("net_pnl", filter=Q(result="WIN"), output_field=DecimalField()),
            total_loss=Sum("net_pnl", filter=Q(result="LOSS"), output_field=DecimalField()),
        )

        non_breakeven = stats["non_breakeven_count"] or 0
        win_rate = round((stats["win_count"] / non_breakeven) * 100, 1) if non_breakeven else 0

        return Response({
            "total_trades": stats["total_trades"],
            "win_rate": win_rate,
            "total_profit": round(stats["total_profit"] or 0, 2),
            "total_loss": round(stats["total_loss"] or 0, 2),
        })


class DashboardTradeStatsListAPIView(APIView):
    """
    API view for listing card data in dashboard.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user, status="CLOSED")
        )

        stats = qs.aggregate(
            total_trades=Count("id"),
            win_count=Count("id", filter=Q(result="WIN")),
            loss_count=Count("id", filter=Q(result="LOSS")),
            gross_wins=Sum("net_pnl", filter=Q(result="WIN"), output_field=DecimalField()),
            gross_losses=Sum("net_pnl", filter=Q(result="LOSS"), output_field=DecimalField()),
            avg_win=Avg("net_pnl", filter=Q(result="WIN"), output_field=DecimalField()),
            avg_loss=Avg("net_pnl", filter=Q(result="LOSS"), output_field=DecimalField()),
            largest_win=Max("net_pnl", filter=Q(result="WIN"), output_field=DecimalField()),
            largest_loss=Min("net_pnl", filter=Q(result="LOSS"), output_field=DecimalField()),
        )

        total = stats["total_trades"] or 0
        gross_wins = stats["gross_wins"] or 0
        gross_losses = abs(stats["gross_losses"] or 0)
        avg_win = stats["avg_win"] or 0
        avg_loss = stats["avg_loss"] or 0
        win_count = stats["win_count"] or 0
        loss_count = stats["loss_count"] or 0

        # Net P&L
        net_pnl = round(gross_wins - gross_losses, 2)

        # Expectancy = (win_rate × avg_win) + (loss_rate × avg_loss)
        if total:
            win_rate = Decimal(win_count) / Decimal(total)
            loss_rate = Decimal(loss_count) / Decimal(total)
            expectancy = round((win_rate * avg_win) + (loss_rate * avg_loss), 2)
        else:
            expectancy = None

        return Response({
            "net_pnl": net_pnl,
            "largest_win": round(stats["largest_win"] or 0, 2),
            "largest_loss": round(stats["largest_loss"] or 0, 2),
            "expectancy": expectancy,
        })


class TradePLChartAPIView(APIView):
    """
    API view for listing P&L chart data.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user, status="CLOSED")
            .order_by("exit_date", "exit_time")
        )

        trades = list(qs)
        total_trades = len(trades)

        if not total_trades:
            return Response({"chart_data": [], "y_axis": []})

        # Last 10 trades
        last_10 = trades[-10:]

        chart_data = []
        for trade in last_10:
            pl = float(round(trade.net_pnl, 2))
            sign = "+" if pl >= 0 else ""

            chart_data.append({
                "name": trade.trade_id.replace("-", "").replace("0", ""),
                "pl": pl,
                "display": f"{sign}${trade.net_pnl:,.2f} P&L",
            })

        return Response({"chart_data": chart_data})


class TradeWinLossRatioAPIView(APIView):
    """
    API view for listing Trade win and loss ratio.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user, status="CLOSED")
        )
        stats = qs.aggregate(
            total=Count("id"),
            wins=Count("id", filter=Q(result="WIN")),
            losses=Count("id", filter=Q(result="LOSS")),
        )
        total = stats["total"] or 0
        wins = stats["wins"] or 0
        losses = stats["losses"] or 0

        win_pct = round((wins / total) * 100, 1) if total else 0
        loss_pct = round((losses / total) * 100, 1) if total else 0

        return Response({
            "win_percentage": win_pct,
            "loss_percentage": loss_pct,
            "label": f"{win_pct}% Win",
        })
    

class TradeNetProfitByStrategyAPIView(APIView):
    """
    API view for listing net profit by strategy.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user, status="CLOSED")
            .select_related("setup__strategy")
        )

        strategy_data = (
            qs
            .values("setup__strategy__name")
            .annotate(net_pnl=Sum("net_pnl", output_field=DecimalField()))
            .order_by("setup__strategy__name")
        )

        chart_data = []
        for row in strategy_data:
            name = row["setup__strategy__name"] or "Unknown"
            pl = float(round(row["net_pnl"] or 0, 2))
            sign = "+" if pl >= 0 else ""
            chart_data.append({
                "strategy": name.upper(),
                "net_pnl": pl,
                "display": f"{sign}${pl:,.2f}",
            })

        return Response({"chart_data": chart_data})


class TradeWinRateBySessionAPIView(APIView):
    """
    API view for listing win rate by session.
    """
    def get(self, request):
        qs = annotate_trade_performance(
            Trade.objects.filter(user=request.user, status="CLOSED")
            .select_related("setup__market_session")
        )

        session_data = (
            qs
            .values("setup__market_session__name")
            .annotate(
                total=Count("id"),
                wins=Count("id", filter=Q(result="WIN")),
            )
            .order_by("-wins")
        )

        chart_data = []
        for row in session_data:
            name = row["setup__market_session__name"] or "Unknown"
            total = row["total"] or 0
            wins = row["wins"] or 0
            win_rate = round((wins / total) * 100, 1) if total else 0

            chart_data.append({
                "session": name,
                "win_rate": win_rate,
                "display": f"{win_rate}% Win Rate",
                "wins": wins,
                "total": total,
            })

        return Response({"chart_data": chart_data})
