from django.contrib import admin
from .models import Article,Infra,Table

class ArticleAdmin(admin.ModelAdmin):
    list_display	= [ "id", "name" ]

class InfraAdmin(admin.ModelAdmin):
    list_display	= [ "id", "title", "article" ]

class TableAdmin(admin.ModelAdmin):
    list_display	= [ "id", "infra", "dxf", "article" ]


admin.site.register(Article,ArticleAdmin)
admin.site.register(Infra,InfraAdmin)
admin.site.register(Table,TableAdmin)