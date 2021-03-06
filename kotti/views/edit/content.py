"""
Content edit views
"""

import random
from StringIO import StringIO
import colander
from colander import SchemaNode
from colander import null
from deform import FileData
from deform.widget import FileUploadWidget
from deform.widget import RichTextWidget
from deform.widget import TextAreaWidget

from kotti.resources import Document
from kotti.resources import File
from kotti.resources import Image
from kotti.util import _
from kotti.views.form import get_appstruct
from kotti.views.form import AddFormView
from kotti.views.form import EditFormView
from kotti.views.form import FileUploadTempStore
from kotti.views.form import ObjectType
from kotti.views.form import deferred_tag_it_widget
from kotti.views.form import validate_file_size_limit


class ContentSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        title=_(u'Title'),
        )
    description = colander.SchemaNode(
        colander.String(),
        title=_('Description'),
        widget=TextAreaWidget(cols=40, rows=5),
        missing=u"",
        )
    tags = colander.SchemaNode(
        ObjectType(),
        title=_('Tags'),
        widget=deferred_tag_it_widget,
        missing=[],
        )


class DocumentSchema(ContentSchema):
    body = colander.SchemaNode(
        colander.String(),
        title=_(u'Body'),
        widget=RichTextWidget(
            # theme='advanced', width=790, height=500
        ),
        missing=u"",
        )


def FileSchema(tmpstore, title_missing=None):
    class FileSchema(ContentSchema):
        file = SchemaNode(
            FileData(),
            title=_(u'File'),
            widget=FileUploadWidget(tmpstore),
            validator=validate_file_size_limit,
            )

    def set_title_missing(node, kw):
        if title_missing is not None:
            node['title'].missing = title_missing

    return FileSchema(after_bind=set_title_missing)


class DocumentEditForm(EditFormView):
    schema_factory = DocumentSchema


class DocumentAddForm(AddFormView):
    schema_factory = DocumentSchema
    add = Document
    item_type = _(u"Document")


class FileEditForm(EditFormView):
    def before(self, form):
        form.appstruct = get_appstruct(self.context, self.schema)
        if self.context.data is not None:
            form.appstruct.update({'file': {
                'fp': StringIO(self.context.data),
                'filename': self.context.name,
                'mimetype': self.context.mimetype,
                'uid': str(random.randint(1000000000, 9999999999)),
            }})

    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)
        return FileSchema(tmpstore)

    def edit(self, **appstruct):
        title = appstruct['title']
        self.context.title = title
        self.context.description = appstruct['description']
        self.context.tags = appstruct['tags']
        if appstruct['file']:
            buf = appstruct['file']['fp'].read()
            self.context.data = buf
            self.context.filename = appstruct['file']['filename']
            self.context.mimetype = appstruct['file']['mimetype']
            self.context.size = len(buf)


class FileAddForm(AddFormView):
    item_type = _(u"File")
    item_class = File  # specific to this class

    def schema_factory(self):
        tmpstore = FileUploadTempStore(self.request)
        return FileSchema(tmpstore, title_missing=null)

    def save_success(self, appstruct):
        if not appstruct['title']:
            appstruct['title'] = appstruct['file']['filename']
        return super(FileAddForm, self).save_success(appstruct)

    def add(self, **appstruct):
        buf = appstruct['file']['fp'].read()
        filename = appstruct['file']['filename']
        return self.item_class(
            title=appstruct['title'] or filename,
            description=appstruct['description'],
            tags=appstruct['tags'],
            data=buf,
            filename=filename,
            mimetype=appstruct['file']['mimetype'],
            size=len(buf),
            )


class ImageEditForm(FileEditForm):
    pass


class ImageAddForm(FileAddForm):
    item_type = _(u"Image")
    item_class = Image


def includeme(config):
    config.add_view(
        DocumentEditForm,
        context=Document,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        DocumentAddForm,
        name=Document.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        FileEditForm,
        context=File,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        FileAddForm,
        name=File.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        ImageEditForm,
        context=Image,
        name='edit',
        permission='edit',
        renderer='kotti:templates/edit/node.pt',
        )

    config.add_view(
        ImageAddForm,
        name=Image.type_info.add_view,
        permission='add',
        renderer='kotti:templates/edit/node.pt',
        )
