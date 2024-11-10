from django.shortcuts import render
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from .models import *
from .serializers import *
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User,Group
from rest_framework import viewsets,status,generics

# Create your views here.
class CategoryView(generics.ListCreateAPIView):
    queryset=Category.objects.all()
    serializer_class=CategorySerialize
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
class MenuItemView(generics.ListCreateAPIView):
    queryset=MenuItem.objects.all()
    serializer_class=MenuItemSerialize
    search_fields=['category__title']
    ordering_fields=['price','inventory']
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
class SingleMenuitem(generics.RetrieveUpdateDestroyAPIView):
    queryset=MenuItem.objects.all()
    serializer_class=MenuItemSerialize
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
class CartView(generics.ListCreateAPIView):
    queryset=Cart.objects.all()
    serializer_class=CartSerializer
    permission_classes=[IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user) 
    
    def delete(self, request, *args, **kwargs):
        delete_c,_=self.queryset.filter(user=self.request.user).delete()
        if delete_c > 0:
            return Response({"detail": "All items deleted."}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "No items to delete."}, status=status.HTTP_404_NOT_FOUND)

class OrderView(generics.ListCreateAPIView):
    queryset=Order.objects.all()
    serializer_class=OrderSerializer
    permission_classes=[IsAuthenticated]
    
    def get_queryset(self):
        user=self.request.user
        if user.is_superuser:
            return Order.objects.all()
        
        if user.groups.count()==0:
            return Order.objects.filter(user=user)
        
        if user.groups.filter(name='Delivery Crew').exists:
            return Order.objects.filter(delivery_crew=user)
        
        return Order.objects.all()
    
    def get_total_price(self, user):
        total = 0
        items = Cart.objects.all().filter(user=user)
        for item in items.values():
            total += item['price']*item['quantity']
        return total
    
    def create(self, request, *args, **kwargs):
        menuitem_count=Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count==0:
            return Response({'message':'no item in cart'},status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        total=self.get_total_price(self.request.user)
        data['total']=total
        data['user']=self.request.user.id
        
        order_serializer=OrderSerializer(data=data)
        
        if (order_serializer.is_valid()):
            order=order_serializer.save()
            items=Cart.objects.all().filter(user=self.request.user)
            
            for item in items.values():
                OrderItem.objects.create(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                
            item.delete()
            
            result=order_serializer.data.copy()
            result['total']=total
            return Response(result, status=status.HTTP_201_CREATED) 
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)  

class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset=Order.objects.all()
    serializer_class=OrderSerializer
    permission_classes=[IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0:
            return Response("Bad",status=403)
        return super().update(request, *args, **kwargs)
    

class GroupView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        users = User.objects.filter(groups__name='Manager')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def create(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)

        managers_group, created = Group.objects.get_or_create(name='Manager')
        managers_group.user_set.add(user)

        return Response({"message": "User added to the Manager group"}, status=status.HTTP_200_OK)

    def destroy(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)

        managers_group = get_object_or_404(Group, name='Manager')
        managers_group.user_set.remove(user)

        return Response({"message": "User removed from the Manager group"}, status=status.HTTP_200_OK)
    
class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        users = User.objects.all().filter(groups__name='Delivery Crew')
        items = UserSerializer(users, many=True)
        return Response(items.data)

    def create(self, request):
        if self.request.user.is_superuser == False:
            if self.request.user.groups.filter(name='Manager').exists() == False:
                return Response({"message":"forbidden"}, status.HTTP_403_FORBIDDEN)
        
        user = get_object_or_404(User, username=request.data['username'])
        dc = Group.objects.get(name="Delivery Crew")
        dc.user_set.add(user)
        return Response({"message": "user added to the delivery crew group"}, 200)

    def destroy(self, request):

        if self.request.user.is_superuser == False:
            if self.request.user.groups.filter(name='Manager').exists() == False:
                return Response({"message":"forbidden"}, status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, username=request.data['username'])
        dc = Group.objects.get(name="Delivery Crew")
        dc.user_set.remove(user)
        return Response({"message": "user removed from the delivery crew group"}, 200)
