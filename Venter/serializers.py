"""
    Serializers for Venter RESTful API Application
"""

from rest_framework import serializers
from Venter.models import Category, Organisation, File


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = (
            'organisation_name',
        )

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'category', 'organisation_name',
        )

class FileSerializer(serializers.ModelSerializer):
    ckpt_date = serializers.DateTimeField(format="%d %B %Y")

    # ckpt_date = datetime.now()

    # ckpt_date = ckpt_date.strftime("%d %B %Y")
    
    class Meta:
        model = File
        fields = (
            'organisation_name', 'ckpt_date', 'id'
        )