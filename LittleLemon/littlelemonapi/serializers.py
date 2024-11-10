from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class CategorySerialize(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id','title','slug']
        
class MenuItemSerialize(serializers.ModelSerializer):
    category=serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model=MenuItem
        fields=['title','price','featured','category']
        
class CartSerializer(serializers.ModelSerializer):
    user=serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    class Meta:
        model=Cart
        fields=['user','menuitem','unit_price','quantity','price']
        extra_kwargs={
            'price':{'read_only':True}
        }
        
    def validate(self, attrs):
        attrs['price']=attrs['quantity']*attrs['unit_price']
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrderItem
        fields=['order','menuitem','quantity','price']
        
class OrderSerializer(serializers.ModelSerializer):
    orderitem=OrderItemSerializer(many=True, read_only=True, source='order')
    class Meta:
        model=Order
        fields=['id', 'user', 'delivery_crew','status', 'date', 'total', 'orderitem']
        
class UserSerializer(serializers.Serializer):

    class Meta:
        model=User
        fields=['id','username','email']