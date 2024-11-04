# == This code was created by https://noauto-nolife.com/post/django-auto-create-models-forms-admin/ == #
from django import forms
from .models import Article,Infra,Table

class ArticleForm(forms.ModelForm):
    class Meta:
        model	= Article
        fields	= [ "name" ]

class InfraForm(forms.ModelForm):
    class Meta:
        model	= Infra
        fields	= [ "title", "article" ]

class TableForm(forms.ModelForm):
    class Meta:
        model	= Table
        fields	= [ "infra", "dxf", "article" ]