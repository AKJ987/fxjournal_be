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


class TableListAPIView(ListAPIView, ExportMixin):
    """
    A reusable core table list view that provides advanced features like search, filtering, 
    sorting and pagination for API endpoints.
    Designed to be extended by child views.

    ### Features
    - **Search**: Perform searches across specified fields.
    - **Filtering**: Filter records using dynamic operators based on field configurations.
    - **Sorting**: Order results by specified fields.
    - **Pagination**: Support for limit-offset pagination with customizable limits.
    - **Ownership Filtering**: Optionally restrict results to objects owned by the current user.
    - **Export**: Export data in CSV or Excel format with optional permissions and custom serializers.

    ### Attributes to Override in Child Views
    - **search_fields** (`list`): Fields to enable full-text search. Example: `["name", "email"]`.
    - **filterset_fields** (`dict`): Fields and their operators to enable filtering.
      Example: `{"date_joined": ["gte", "lte", "exact"]}`.
    - **ordering_fields** (`list`): Fields that support sorting. Example: `["id", "name"]`.
    - **columns** (`dict`): Define metadata for each field, including label, filter operators, and sortable flag.
      Example:
      ```python
      columns = {
          "username": {
              "label": "User Name",
              "param_key": "username",
              "filter_operators": ["exact", "icontains"],
              "sortable": True,
          },
      }
      ```

    - **filter_by_owner** (`bool`, optional): Enable filtering by owner (default: False).
    - **owner_field** (`string`, optional): Field to use for ownership-based filtering (default: "owner").
    - **enable_export** (`bool`, optional): Enable export functionality (default: False).

    ### Query Parameters
    - **search** (`string`, optional): Search across the fields defined in `search_fields`.
      Example: `?search=example`.

    - **filter fields** (`string`, optional): Apply filters based on `filterset_fields`.
      Example: `?date_joined__gte=2024-12-31`.

    - **ordering** (`string`, optional): Specify sorting order. Prefix a field name with `-` for descending order.
      Example: `?ordering=-date_joined`.

    - **limit** (`integer`, optional): Number of records to retrieve per page (default: 10).
      Example: `?limit=5`.

    - **offset** (`integer`, optional): Starting point for pagination (default: 0).
      Example: `?offset=10`.

    ### Methods to Override in Child Views
    - **get_queryset**: Extend the base query to apply additional filtering logic.
    - **get_filterset_fields**: Dynamically set the `filterset_fields` from the `columns` configuration.
    - **get_ordering_fields**: Dynamically set the `ordering_fields` from the `columns` configuration.

    ### Response Format
    The API response includes the following:
    - **count**: Total number of matching records.
    - **next**: URL for the next page (if available).
    - **previous**: URL for the previous page (if available).
    - **results**: List of retrieved objects.
    - **columns**: Metadata about the columns available for filtering and sorting.

    #### Example Response
    ```json
    {
        "count": 100,
        "next": "http://example.com/api/items/?limit=10&offset=10",
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "Item 1",
                "date_created": "2025-01-01T10:00:00Z",
                "status": "Active"
            },
            ...
        ],
        "columns": {
            "name": {
                "label": "Item Name",
                "param_key": "name",
                "filter_operators": ["exact", "icontains"],
                "sortable": True,
            },
            "date_created": {
                "label": "Date Created",
                "param_key": "date_created",
                "filter_operators": ["gte", "lte", "exact"],
                "sortable": True,
            },
        }
    }
    ```

    ### Example Requests
    #### Basic Request:
    ```
    GET /items/list/
    ```

    #### Filter and Search:
    ```
    GET /items/list/?date_created__gte=2025-01-01&search=example
    ```

    #### Sorting with Pagination:
    ```
    GET /items/list/?ordering=-date_created&limit=5&offset=10
    ```

    #### Combining Filters, Sorting, and Search:
    ```
    GET /items/list/?search=item&date_created__lte=2025-01-01&ordering=name
    ```

    ### Usage Notes
    - Ensure `columns` are properly defined in child views for seamless filtering and sorting.
    - Override the `filter_by_owner` and `owner_field` attributes if ownership-based filtering is required.
    """

    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    pagination_class = LimitOffsetPagination
    search_fields = []  # Override in child views
    filterset_fields = {}  # Override in child views
    ordering_fields = []  # Override in child views
    ordering = ['id']  # Default ordering; override in child views
    
    # Filter by owner if True: only show objects owned by the current user
    filter_by_owner = False
    owner_field = "owner"

    # Default to False if not explicitly set in columns
    default_sortable = False

    # Define columns for the table
    columns = {}  # Override in child views

    enable_export = False  # Enable/disable export functionality

    def get_queryset(self):
        """
        Add optional filtering by owner if `filter_by_owner` is True.
        """

        # Dynamically set filterset_fields and ordering_fields
        child_filterset_fields = self.filterset_fields
        self.filterset_fields = {** self.get_filterset_fields(), **child_filterset_fields}
        self.ordering_fields = self.get_ordering_fields()

        base_queryset = super().get_queryset()
        if self.filter_by_owner and hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return base_queryset.filter(**{self.owner_field: self.request.user})
        
        return base_queryset
    
    def filter_queryset(self, queryset):
        """
        Override DRF ordering to apply case-insensitive sorting using Lower().
        Works for all table list views.
        """
        queryset = super().filter_queryset(queryset)

        ordering_param = self.request.query_params.get("ordering")
        if not ordering_param:
            return queryset

        # Support multiple ordering fields: ?ordering=name,-email
        ordering_fields = [f.strip() for f in ordering_param.split(",")]

        processed = []

        for field in ordering_fields:
            is_desc = field.startswith("-")
            clean_field = field.lstrip("-")

            # Only apply case-insensitive sort for configured ordering_fields
            if clean_field in self.ordering_fields:
                expr = Lower(clean_field)
                processed.append(expr.desc() if is_desc else expr)
            else:
                # fallback to normal ordering
                processed.append(field)

        return queryset.order_by(*processed)

    def get_filterset_fields(self):
        """
        Extract filterable fields and their operators from `columns`.
        """
        return {
            config.get("param_key"): config["filter_operators"]
            for config in self.columns.values()
            if "filter_operators" in config and config.get("param_key")
        }

    def get_ordering_fields(self):
        """
        Extract sortable fields from `columns`.
        """
        return [
            config.get("param_key")
            # Iterate over the values of the columns
            for config in self.columns.values()
            if config.get("sortable", self.default_sortable)
        ]

    def list(self, request, *args, **kwargs):
        """
        Override the list method to include `columns` data in the response.
        """
        # Check if export is enabled and the export format is provided
        export_format = request.query_params.get(self.export_format_param)
        if self.enable_export and export_format:
            # Handle export if the `export_format` parameter is present
            return self.export(request, *args, **kwargs)

        # Proceed with the regular list operation
        response = super().list(request, *args, **kwargs)

        # Inject `row_actions` into each result
        results = response.data.get('results', [])

        # Row actions are optional and can be dynamically defined
        row_actions_exists = False
        for row in results:
            row_actions = self.get_row_actions(row)
            if row_actions:
                row['row_actions'] = self.get_row_actions(row)
                if not row_actions_exists:
                    row_actions_exists = True

        # Add `columns` to the response
        response.data['columns'] = self.columns

        # if row_actions_exists set Action column
        if row_actions_exists:
            response.data['columns']["row_actions"] = {
                "label": _("Actions"),
            }

        response.data['export_enabled'] = self.enable_export
        response.data['export_formats'] = self.export_formats

        # Return the modified response
        return Response(response.data)
    
    def get_row_actions(self, row):
        """Dynamically define row actions based on row data."""
        actions = []
        return actions
