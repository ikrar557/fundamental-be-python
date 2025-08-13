from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrSuperUser, IsOwnerOrAdminOrSuperUser, IsSuperUser
from .models import User
from .serializers import UserSerializer, GroupSerializer
from django.http import Http404
from loguru import logger

class UserListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return []

    def get(self, request):
        users = User.objects.all().order_by('username')[:10]
        serializer = UserSerializer(users, many=True)
        logger.info("GET /users - User list retrieved by admin {}", request.user)
        return Response({'users': serializer.data})

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info("POST /users - New user '{}' created successfully", user.username)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        user_identifier = request.data.get('username', 'N/A')
        logger.error("POST /users - Failed to create user '{}'. Errors: {}", user_identifier, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]

    def get_object(self, pk):
        try:
            user = User.objects.get(pk=pk)
            self.check_object_permissions(self.request, user)
            return user
        except User.DoesNotExist:
            logger.warning("User with pk={} not found, requested by {}", pk, self.request.user)
            raise Http404

    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        logger.info("GET /users/{} - Details for '{}' retrieved by {}", pk, user.username, request.user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            logger.info("PUT /users/{} - User '{}' updated by {}", pk, updated_user.username, request.user)
            return Response(serializer.data)

        logger.error("PUT /users/{} - Update for '{}' failed by {}. Errors: {}", pk, user.username, request.user,
                     serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        username = user.username
        user.delete()
        logger.info("DELETE /users/{} - User '{}' deleted by {}", pk, username, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        groups = Group.objects.all().order_by('name')[:10]
        serializer = GroupSerializer(groups, many=True)
        logger.info("GET /groups - Group list retrieved by admin {}", request.user)
        return Response({'groups': serializer.data})

    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            group = serializer.save()
            logger.info("POST /groups - New group '{}' created by admin {}", group.name, request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.error("POST /groups - Group creation failed by admin {}. Errors: {}", request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            logger.warning("Group with pk={} not found, requested by admin {}", pk, self.request.user)
            raise Http404

    def get(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupSerializer(group)
        logger.info("GET /groups/{} - Detail for group '{}' retrieved by admin {}", pk, group.name, request.user)
        return Response(serializer.data)

    def put(self, request, pk):
        group = self.get_object(pk)
        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            updated_group = serializer.save()
            logger.info("PUT /groups/{} - Group '{}' updated by admin {}", pk, updated_group.name, request.user)
            return Response(serializer.data)

        logger.error("PUT /groups/{} - Update for group '{}' failed by admin {}. Errors: {}", pk, group.name,
                     request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        group = self.get_object(pk)
        group_name = group.name
        group.delete()
        logger.info("DELETE /groups/{} - Group '{}' deleted by admin {}", pk, group_name, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignRoleView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperUser]

    def post(self, request):
        try:
            user_id = request.data['user_id']
            group_id = request.data['group_id']

            user = get_object_or_404(User, pk=user_id)
            group = get_object_or_404(Group, pk=group_id)

            user.groups.add(group)

            logger.info("POST /assign-role - User '{}' assigned to group '{}' by admin {}", user.username, group.name,
                        request.user)
            return Response({"message": "Role assigned successfully"}, status=status.HTTP_201_CREATED)

        except KeyError as e:
            logger.error("POST /assign-role - Missing key {} in request data from admin {}", str(e), request.user)
            return Response({"error": f"Missing required field: {e}"}, status=status.HTTP_400_BAD_REQUEST)