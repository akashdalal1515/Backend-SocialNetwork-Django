from django.urls import path
from .views import SignupView, LoginView, UserSearchView, FriendRequestView, FriendsListView, PendingRequestsView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('friend-request/', FriendRequestView.as_view(), name='send_friend_request'),
    path('friend-request/<int:pk>/', FriendRequestView.as_view(), name='manage_friend_request'),
    path('friends/', FriendsListView.as_view(), name='friends-list'),
    path('pending-requests/', PendingRequestsView.as_view(), name='pending-requests'),
]
