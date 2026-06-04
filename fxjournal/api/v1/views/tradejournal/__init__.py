from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from utils.generic_views import DropdownListAPIView
from utils.mixins import SuccessMessageMixin, ExportMixin
from tradejournal.models import (
    Instrument,
    Strategy,
    Timeframe,
    Session,
    MarketCondition,
    Trade,
)
from .serializers import (
    TradeCreateUpdateSerializer,
    TradeListSerializer
)
from .functions import annotate_trade_performance

class InstrumentDropdownAPIView(DropdownListAPIView):
    """
    API view for listing instruments in a dropdown.
    """
    permission_classes = [AllowAny]
    queryset = Instrument.objects.all()
    search_fields = ['name']
    ordering = ['id']


class StrategyDropdownAPIView(DropdownListAPIView):
    """
    API view for listing strategy in a dropdown.
    """
    queryset = Strategy.objects.all()
    search_fields = ['name']
    ordering = ['name']


class TimeframeDropdownAPIView(DropdownListAPIView):
    """
    API view for listing timeframe in a dropdown.
    """
    queryset = Timeframe.objects.all()
    search_fields = ['name']
    ordering = ['id']


class SessionDropdownAPIView(DropdownListAPIView):
    """
    API view for listing session in a dropdown.
    """
    queryset = Session.objects.all()
    search_fields = ['name']
    ordering = ['name']


class MarketConditionDropdownAPIView(DropdownListAPIView):
    """
    API view for listing market condition in a dropdown.
    """
    queryset = MarketCondition.objects.all()
    search_fields = ['name']
    ordering = ['name']


class TradeCreateAPIView(SuccessMessageMixin, CreateAPIView):
    """
    Create Trade + Setup + Psychology + Screenshots
    """
    serializer_class = TradeCreateUpdateSerializer
    queryset = Trade.objects.all()
    success_message = "Trade entry created successfully."


class TradeUpdateAPIView(SuccessMessageMixin, UpdateAPIView):
    """
    Update Trade + Setup + Psychology + Screenshots
    """
    serializer_class = TradeCreateUpdateSerializer
    queryset = Trade.objects.all()
    success_message = "Trade entry updated successfully."
    lookup_field = "object_id"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


class TradeListAPIView(ExportMixin, ListAPIView):
    """
    API to list and export Trades.
    """
    serializer_class = TradeListSerializer

    enable_export = True
    export_filename = "TradeData"
    export_serializer_class = TradeListSerializer
    columns = {
        "trade_id": {"label": "Trade ID"},
        "entry_date": {"label": "Entry Date"},
        "instrument": {"label": "Instrument"},
        "direction": {"label": "Direction"},
        "status": {"label": "Status"},
        "net_pnl": {"label": "P&L"},
        "result": {"label": "Result"},
    }

    def get_queryset(self):
        queryset = (
            Trade.objects
            .select_related("instrument")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )

        queryset = annotate_trade_performance(queryset)
        params = self.request.GET

        # Filters
        if entry_date_gte := params.get("entry_date__gte"):
            queryset = queryset.filter(entry_date__gte=entry_date_gte)

        if entry_date_lte := params.get("entry_date__lte"):
            queryset = queryset.filter(entry_date__lte=entry_date_lte)

        if instrument := params.get("instrument__name"):
            queryset = queryset.filter(instrument__name=instrument)

        if direction := params.get("direction"):
            queryset = queryset.filter(direction=direction)

        if status := params.get("status"):
            queryset = queryset.filter(status=status)

        if result := params.get("result"):
            queryset = queryset.filter(result=result)

        if search := params.get("search"):
            queryset = queryset.filter(instrument__name__icontains=search)

        # Sorting
        if sorting := params.get("sorting"):
            queryset = queryset.order_by(sorting, "-created_at")

        return queryset

    def get(self, request, *args, **kwargs):
        export_format = request.query_params.get(self.export_format_param)

        if export_format:
            return self.export(request, *args, **kwargs)

        return super().get(request, *args, **kwargs)
