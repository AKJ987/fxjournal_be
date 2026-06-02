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