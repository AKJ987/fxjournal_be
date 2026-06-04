from io import BytesIO
from rest_framework.views import APIView, Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from django.utils import timezone
import pandas as pd


class SuccessMessageMixin:
    """
    Mixin to add a success message to the response after a successful creation.
    """
    success_message = "Object created successfully."

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create method to add a success message.
        """
        response = super().create(request, *args, **kwargs)
        response.data = {
            'data': response.data,
            'message': self.success_message,
        }
        return response
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {
            "data": response.data,
            "message": self.success_message,
        }
        return response

    def destroy(self, request, *args, **kwargs):
        """
        Overrides the default destroy method to add a success message after object deletion.
        """
        super().destroy(request, *args, **kwargs)
        message = self.success_message

        return Response({
            'message': message
        }, status=status.HTTP_200_OK)


class ExportMixin(APIView):
    """
    A mixin to provide CSV and Excel export functionality with optional permissions and custom serializers.
    """
    enable_export = False  # Default: export is disabled
    export_permission_classes = []  # Optional: Permissions for exporting
    export_formats = ["csv", "excel"]  # Supported export formats
    export_serializer_class = None  # Serializer to define exported data
    # Query parameter to specify export format
    export_format_param = "export_format"
    export_filename = "export"  # Default export filename
    export_filename_includes_timestamp = False  # Include timestamp in filename

    def check_export_permissions(self, request):
        """
        Check permissions for export operation if `export_permission_classes` is set.
        """
        if self.export_permission_classes:
            for permission in self.export_permission_classes:
                permission_instance = permission()
                if not permission_instance.has_permission(request, self):
                    return False
        return True

    def get_export_data(self):
        """
        Fetch data to export using the appropriate serializer class.
        Falls back to `serializer_class` if `export_serializer_class` is not defined.
        """
        serializer_class = self.export_serializer_class or self.serializer_class
        if not serializer_class:
            raise NotImplementedError(
                _("A serializer class must be defined for export.")
            )

        queryset = self.get_queryset()

        # Manually apply each filter backend in filter_backends
        for backend in self.filter_backends:
            # Initialize the filter backend
            filter_backend = backend()

            # Apply the filter to the queryset
            queryset = filter_backend.filter_queryset(self.request, queryset, self)

        serializer = serializer_class(queryset, many=True)
        for item in serializer.data:
            for key in item:
                value = item[key]
                if isinstance(value, list):
                    item[key] = ", ".join(map(str, value)) if value else "-"
        return serializer.data

    def make_dataframe(self, data):
        """
        Convert data to a pandas DataFrame, including only the fields from columns.
        """
        # Rename the DataFrame columns to match the dynamic headers
        columns_to_export = {
            column: str(config.get("label"))
            for column, config in self.columns.items()
            if column != "row_actions"  # Skip the 'row_actions' column
        }

        # Get requested columns from query params (comma-separated)
        requested_columns = self.request.query_params.get("export_columns")
        if requested_columns:
            requested_columns = [
                col.strip() for col in requested_columns.split(",") if col.strip() in columns_to_export
            ]
        else:
            # If not specified, export all
            requested_columns = list(columns_to_export.keys())

        # Create DataFrame with only requested columns
        df = pd.DataFrame(data, columns=requested_columns)

        # Rename columns to labels
        rename_map = {col: columns_to_export[col] for col in requested_columns}
        df.rename(columns=rename_map, errors="raise", inplace=True)
        # Fill NaN values with "-"
        df.fillna("-", inplace=True)
        return df

    def generate_csv(self, data):
        """
        Generate CSV content from the data.
        """
        # Convert data to pandas DataFrame
        df = self.make_dataframe(data)
        return df.to_csv(index=False)

    def generate_excel(self, data):
        """
        Generate Excel content from the data.
        """
        # Check if data is not empty
        if not data:
            raise ValueError("Data cannot be empty")

        # Convert data to pandas DataFrame
        df = self.make_dataframe(data)

        # Create an in-memory buffer
        buffer = BytesIO()

        # Use pandas to write the DataFrame directly to the buffer as an Excel file
        df.to_excel(
            buffer,
            index=False,
            engine='openpyxl',
            sheet_name=self.export_filename
        )

        # Seek to the beginning of the buffer
        buffer.seek(0)

        return buffer

    def get_export_filename(self):
        """
        Get the export filename with an optional timestamp.
        """
        filename = self.export_filename
        if self.export_filename_includes_timestamp:
            filename += f"_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        return filename

    def export(self, request, *args, **kwargs):
        """
        Handle export requests.
        """
        if not self.enable_export:
            return Response(
                {
                    "message": _("Export is not enabled for this view."),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check permissions
        if not self.check_export_permissions(request):
            return Response(
                {
                    "message": _("You do not have permission to export data."),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get export format
        export_format = request.query_params.get(self.export_format_param, "csv").lower()
        if export_format not in self.export_formats:
            return Response(
                {
                    "message": _("Unsupported export format. Supported formats: %(formats)s.") % {
                        "formats": ", ".join(self.export_formats)
                    },
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get export data
        data = self.get_export_data()
        if not data:
            return Response(
                {
                    "message": _("No data available for export."),
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate the export file
        export_filename = self.get_export_filename()
        if export_format == "csv":
            content = self.generate_csv(data)
            content_type = "text/csv"
            filename = f"{export_filename}.csv"
        elif export_format == "excel":
            content = self.generate_excel(data)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{export_filename}.xlsx"

        # Return the file response
        response = FileResponse(content, content_type=content_type)
        # Set file name for download
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = "Content-Disposition"

        return response

