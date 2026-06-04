from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Lower
from .mixins import ExportMixin


class DropdownListAPIView(ListAPIView):
    """
    Generic API view for listing model records in dropdowns without a serializer.

    Child classes must define:
    - `queryset`: The model queryset.
    - `dropdown_fields`: The fields to return in the response (default: `object_id` and `name`).
    - `search_fields`: Fields for search functionality.
    - `ordering_fields`: Fields allowed for ordering.
    - `filterset_fields`: Fields allowed for filtering (e.g., `organization__uuid`).
    
    Example usage:
        - GET department/list/dropdown/?search=Finance
        - GET department/list/dropdown/?ordering=name
        - GET department/list/dropdown/?organization__uuid=<uuid>
    """

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = []  # Must be overridden in child classes
    ordering_fields = []  # Must be overridden in child classes
    ordering = ['name']  # Default ordering by ID descending
    filterset_fields = []  # Allow filtering on specific fields

    dropdown_fields = ['id', 'code', 'name']  # Default fields to return

    def list(self, request, *args, **kwargs):
        """Override the response to return a simple JSON list."""
        queryset = self.filter_queryset(self.get_queryset())
        data = list(queryset.values(*self.dropdown_fields))  # Convert queryset to list of dicts
        return Response(data)
