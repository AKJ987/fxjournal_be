from api.v1 import views
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('user/register/', views.UserRegisterAPI.as_view(), name='user-register'),

    path('instrument/dropdown/', views.InstrumentDropdownAPIView.as_view(), name='instrument-dropdown'),
    path('strategy/dropdown/', views.StrategyDropdownAPIView.as_view(), name='strategy-dropdown'),
    path('timeframe/dropdown/', views.TimeframeDropdownAPIView.as_view(), name='timeframe-dropdown'),
    path('session/dropdown/', views.SessionDropdownAPIView.as_view(), name='session-dropdown'),
    path('market/condition/dropdown/', views.MarketConditionDropdownAPIView.as_view(), name='market-condition-dropdown'),
    path('trade/create/', views.TradeCreateAPIView.as_view(), name='trade-create'),
    path('trade/update/<uuid:object_id>/', views.TradeUpdateAPIView.as_view(), name='trade-update'),
    path('trade/list/', views.TradeListAPIView.as_view(), name='trade-list'),
    path('trade/detail/<uuid:object_id>/', views.TradeDetailAPIView.as_view(), name='trade-details'),
    path('trade/delete/<uuid:object_id>/', views.TradeDeleteAPIView.as_view(), name='trade-delete'),
    path('screenshot/delete/<int:id>/', views.TradeScreenshotDeleteAPIView.as_view(), name='screenshot-delete'),
]
