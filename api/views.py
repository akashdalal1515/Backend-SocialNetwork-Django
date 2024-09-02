from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import User, FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404


class SignupView(APIView):
    
    # View for user signup.
    
    def post(self, request):
        
        # Handles POST request for user signup.
    
        email = request.data.get('email').lower()
        username = request.data.get('username')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # Validate required fields
        if not email or not username or not password or not first_name or not last_name:
            return Response({'error': 'Please provide all required fields'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):

    # View for user login.
    
    def post(self, request):

        # Handles POST request for user login.
     
        email = request.data.get('email').lower()
        password = request.data.get('password')

        # Authenticate user
        user = authenticate(email=email, password=password)
        if user:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(APIView):

    # View for searching users.
   
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # Handles GET request for user search.
        
        keyword = request.query_params.get('q')

        # Validate search keyword
        if keyword is None:
            return Response({'error': 'No search keyword provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Paginate results
        paginator = PageNumberPagination()
        paginator.page_size = 10

        # Search by email or name
        if '@' in keyword:  # Search by email
            users = User.objects.filter(email__iexact=keyword)
        else:  # Search by name
            users = User.objects.filter(Q(first_name__icontains=keyword) | Q(last_name__icontains=keyword))

        # Paginate and serialize results
        result_page = paginator.paginate_queryset(users, request)
        serializer = UserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class FriendRequestView(APIView):
    
    # View for managing friend requests.
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        # Handles POST request for sending friend requests.
        
        receiver_id = request.data.get('receiver_id')
        receiver = get_object_or_404(User, id=receiver_id)
        sender = request.user

        # Validate receiver and prevent self-requests
        if sender == receiver:
            return Response({'error': 'Cannot send friend request to yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing pending requests
        if FriendRequest.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
            return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)

        # Limit requests to 3 per minute
        if FriendRequest.objects.filter(sender=sender, created_at__gte=datetime.now() - timedelta(minutes=1)).count() >= 3:
            return Response({'error': 'Cannot send more than 3 friend requests within a minute'}, status=status.HTTP_400_BAD_REQUEST)

        # Create friend request
        friend_request = FriendRequest.objects.create(sender=sender, receiver=receiver)
        return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)

    def patch(self, request, pk):
        
        # Handles PATCH request for accepting or rejecting friend requests.
        
        friend_request = get_object_or_404(FriendRequest, id=pk)
        status = request.data.get('status')

        # Validate status
        if status in ['accepted', 'rejected']:
            friend_request.status = status
            friend_request.save()
            return Response(
                {
                    'message': f'Friend request {status} successfully',
                    'status': 'success',
                    'data': FriendRequestSerializer(friend_request).data
                },
            )
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


class FriendsListView(APIView):
    
    # View for listing friends.
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # Handles GET request for listing friends.
        
        friends = User.objects.filter(Q(sent_requests__status='accepted', sent_requests__receiver=request.user) | Q(received_requests__status='accepted', received_requests__sender=request.user))
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PendingRequestsView(APIView):
    
    # View for listing pending friend requests.
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        # Handles GET request for listing pending friend requests.
        
        pending_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
        serializer = FriendRequestSerializer(pending_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
