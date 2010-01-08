from django import forms
from django.db.models import permalink

from datetime import datetime
import re
from mongoengine import *

from mumblr.models import User


class Comment(EmbeddedDocument):
    """A comment that may be embedded within a post.
    """
    author = StringField()
    body = StringField()
    date = DateTimeField(required=True, default=datetime.now)


class EntryType(Document):
    """The base class for entry types. New types should inherit from this and
    extend it with relevant fields. You must define a method
    :meth:`EntryType.rendered_content`\ , which returns a string of HTML that
    will be used as the content. To make the entry's title link somewhere other
    than the post, you may provide a :attr:`link_url` field.

    New entry types should also specify a form to be used in the admin 
    interface. This is done by creating a subclass of 
    :class:`EntryType.AdminForm` (which must also be called AdminForm) as a
    class attribute.
    """
    title = StringField(required=True)
    slug = StringField(required=True, regex='[A-z0-9_-]+')
    author = ReferenceField(User)
    date = DateTimeField(required=True, default=datetime.now)
    tags = ListField(StringField(max_length=50))
    comments = ListField(EmbeddedDocumentField(Comment))
    published = BooleanField(default=True)
    link_url = StringField()

    _types = {}

    @queryset_manager
    def live_entries(queryset):
        return queryset(published=True)

    @permalink
    def get_absolute_url(self):
        date = self.date.strftime('%Y/%b/%d').lower()
        return ('entry-detail', (date, self.slug))

    def rendered_content(self):
        raise NotImplementedError()

    def save(self):
        def convert_tag(tag):
            tag = tag.strip().lower().replace(' ', '-')
            return re.sub('[^a-z0-9_-]', '', tag)
        self.tags = [convert_tag(tag) for tag in self.tags]
        super(EntryType, self).save()

    class AdminForm(forms.Form):
        title = forms.CharField()
        slug = forms.CharField()
        tags = forms.CharField(required=False)
        published = forms.BooleanField()

    @classmethod
    def register(cls, entry_type):
        """Register an EntryType subclass.
        """
        cls._types[entry_type.type.lower()] = entry_type