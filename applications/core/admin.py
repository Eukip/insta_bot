from django.contrib import admin
from django.contrib.auth import models as auth_models

from applications.core import models


admin.site.unregister(auth_models.User)
admin.site.unregister(auth_models.Group)


class CommentInline(admin.StackedInline):
    model = models.Comment


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    fields = ('social_media', 'username', 'password', )
    search_fields = ('username', )
    list_display = ('username', 'password', 'social_media', )
    list_filter = ('social_media', )
    inlines = (CommentInline, )


@admin.register(models.PublicPage)
class PublicPageAdmin(admin.ModelAdmin):
    fields = ('social_media', 'name', 'url', )
    search_fields = ('name', 'url', )
    list_display = ('name', 'social_media', 'url', )
    list_filter = ('social_media', )


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    fields = ('account', 'text', )
    search_fields = ('text', )
    list_display = ('account', 'text', )
    list_filter = ('account__username', )


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    fields = ('social_media', 'public_page', 'url', 'added_to_gs')
    search_fields = ('url', )
    list_display = ('url', 'public_page', 'social_media', 'created_at', 'added_to_gs')
    list_filter = ('social_media', 'public_page', 'added_to_gs')

