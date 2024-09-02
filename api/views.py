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
from rest_framework.exceptions import ValidationError, NotFound
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import serializers

class SignupView(APIView):

    # View for user signup.

    def post(self, request):
        try:
            email = request.data.get('email').lower()
            username = request.data.get('username')
            password = request.data.get('password')
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')

            # Validate required fields
            if not email or not username or not password or not first_name or not last_name:
                raise ValidationError('Please provide all required fields')

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError('Email already in use')

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

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):

    # View for user login.

    def post(self, request):
        try:
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
            else:
                raise ValidationError('Invalid Credentials')

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSearchView(APIView):

    # View for searching users.

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            keyword = request.query_params.get('q')

            # Validate search keyword
            if keyword is None:
                raise ValidationError('No search keyword provided')

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

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FriendRequestView(APIView):

    # View for managing friend requests.

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            receiver_id = request.data.get('receiver_id')
            receiver = get_object_or_404(User, id=receiver_id)
            sender = request.user

            # Validate receiver and prevent self-requests
            if sender == receiver:
                raise ValidationError('Cannot send friend request to yourself')

            # Check for existing pending requests
            if FriendRequest.objects.filter(sender=sender, receiver=receiver, status='pending').exists():
                raise ValidationError('Friend request already sent')

            # Limit requests to 3 per minute
            if FriendRequest.objects.filter(sender=sender, created_at__gte=datetime.now() - timedelta(minutes=1)).count() >= 3:
                raise ValidationError('Cannot send more than 3 friend requests within a minute')

            # Create friend request
            friend_request = FriendRequest.objects.create(sender=sender, receiver=receiver)
            return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response({'error': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            friend_request = get_object_or_404(FriendRequest, id=pk)
            status = request.data.get('status')

            # Validate status
            if status not in ['accepted', 'rejected']:
                raise ValidationError('Invalid status')

            friend_request.status = status
            friend_request.save()
            return Response(
                {
                    'message': f'Friend request {status} successfully',
                    'status': 'success',
                    'data': FriendRequestSerializer(friend_request).data
                }
            )

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class FriendsListView(APIView):

    # View for listing friends.

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            friends = User.objects.filter(Q(sent_requests__status='accepted', sent_requests__receiver=request.user) | Q(received_requests__status='accepted', received_requests__sender=request.user))
            serializer = UserSerializer(friends, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PendingRequestsView(APIView):

    # View for listing pending friend requests.

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pending_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
            serializer = FriendRequestSerializer(pending_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
