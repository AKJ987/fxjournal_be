from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny
from utils.generic_views import DropdownListAPIView, TableListAPIView
from utils.mixins import SuccessMessageMixin
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


class TradeListAPIView(TableListAPIView):
    """
    API view for listing and exporting trades.
    """

    serializer_class = TradeListSerializer
    queryset = Trade.objects.select_related("instrument").all()
    ordering = ["-created_at"]
    search_fields = ["instrument__name"]
    columns = {
        "entry_date": {
            "label": "Date",
            "param_key": "entry_date",
            "filter_operators": ["gte", "lte"],
            "sortable": True,
        },
        "instrument": {
            "label": "Pair",
            "param_key": "instrument__name",
            "filter_operators": ["exact"],
            "sortable": True,
        },
        "direction": {
            "label": "Side",
            "param_key": "direction",
            "filter_operators": ["exact"],
            "sortable": True,
        },
        "status": {
            "label": "Status",
            "param_key": "status",
            "filter_operators": ["exact"],
            "sortable": True,
        },
    }

    filter_by_owner = True
    owner_field = "user"

    enable_export = True
    export_filename = "TradeList"
