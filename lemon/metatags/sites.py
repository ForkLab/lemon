from django.db.models import ManyToManyField
from django.db.models.base import ModelBase
from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.utils.translation import ugettext_lazy as _

from lemon import extradmin
from lemon.metatags.models import Page
from lemon.metatags.options import ModelMetatags


class AlreadyRegistered(Exception):

    pass


class NotRegistered(Exception):

    pass


class MetatagsSite(object):

    def __init__(self):
        self._registry = {}

    @property
    def inline_admin_class(self):
        from lemon.metatags.admin import PageInline
        return PageInline

    def register(self, model_or_iterable, model_metatags_class=None, **options):
        if not model_metatags_class:
            model_metatags_class = ModelMetatags

        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                raise AlreadyRegistered(
                    u'The model %s already registered' % model.__name__)

            admin_object = extradmin.site._registry.get(model)
            if admin_object:
                inline_instance = self.inline_admin_class(model, extradmin.site)
                admin_object.inline_instances = \
                    admin_object.inline_instances + [inline_instance]
                if isinstance(admin_object.tabs, (list, tuple)):
                    tab = {'title': _(u'Meta tags'),
                           'contents': [inline_instance]}
                    admin_object.tabs = admin_object.tabs + [tab]

            if options:
                options['__module__'] = __name__
                model_metatags_class = type(
                    '%sMetatags' % model.__name__,
                    (model_metatags_class,), options)
            model_metatags = model_metatags_class()
            self._registry[model] = model_metatags

            pre_delete.connect(self.delete_metatag, sender=model)
            post_save.connect(self.check_metatag_url_path, sender=model)
            post_save.connect(self.check_metatag_language, sender=model)

            sites_field_class = model_metatags.sites_field_class(model)
            if sites_field_class is ManyToManyField:
                through_model = getattr(
                    model, model_metatags.sites_field_name).through
                m2m_changed.connect(
                    self.check_metatag_sites, sender=through_model)
            else:
                post_save.connect(self.check_metatag_site, sender=model)

    def delete_metatag(self, sender, **kwargs):
        Page.objects.filter_by_content_object(kwargs['instance']).delete()

    def check_metatag_url_path(self, sender, **kwargs):
        instance = kwargs['instance']
        model_metatags = self._registry.get(sender)
        if model_metatags:
            try:
                page = Page.objects.get_for_content_object(instance)
            except Page.DoesNotExist:
                pass
            else:
                page.update_url_path()

    def check_metatag_language(self, sender, **kwargs):
        instance = kwargs['instance']
        model_metatags = self._registry.get(sender)
        if model_metatags:
            try:
                page = Page.objects.get_for_content_object(instance)
            except Page.DoesNotExist:
                pass
            else:
                page.update_language()

    def check_metatag_site(self, sender, **kwargs):
        instance = kwargs['instance']
        model_metatags = self._registry.get(sender)
        if model_metatags:
            try:
                page = Page.objects.get_for_content_object(instance)
            except Page.DoesNotExist:
                pass
            else:
                page.update_sites()

    def check_metatag_sites(self, sender, **kwargs):
        instance = kwargs['instance']
        action = kwargs['action']
        model_metatags = self._registry.get(instance.__class__)
        if model_metatags and action in ('post_add', 'post_remove', 'post_clear'):
            try:
                page = Page.objects.get_for_content_object(instance)
            except Page.DoesNotExist:
                pass
            else:
                page.update_sites()


site = MetatagsSite()
