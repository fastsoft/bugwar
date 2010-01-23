
from django.db.models import *
from django.contrib.auth.models import User
from urlparse import urlparse

LABEL_CHOICES = tuple(
    (label, label) for label in (
        'pass', 
        'fail',
        'log', 
        'warn',
    )
)

class Result(Model):
    salvo = ForeignKey('Salvo', related_name = 'results')
    datetime = DateTimeField()
    creation_counter = IntegerField(null = True)
    label = CharField(choices = LABEL_CHOICES, max_length = 16)
    name = CharField(max_length = 1024)
    message = CharField(null = True, max_length = 1024)
    def __unicode__(self):
        return u'%s %s %s %s' % (self.datetime, self.name, self.label, self.message)

class Measure(Model):
    salvo = ForeignKey('Salvo', related_name = 'measures')
    datetime = DateTimeField()
    creation_counter = IntegerField(null = True)
    name = CharField(max_length = 1024)
    value = FloatField()
    def __unicode__(self):
        return u'%s %s %s' % (self.datetime, self.name, self.value)

    class Meta:
        verbose_name = 'measurement'

class Log(Model):

    class Meta:
        verbose_name = 'event'
        verbose_name_plural = 'log'

    salvo = ForeignKey('Salvo', related_name = 'logs')
    result = ForeignKey('Result', related_name = 'logs', null = True)
    measure = ForeignKey('Measure', related_name = 'logs', null = True)
    datetime = DateTimeField()
    creation_counter = IntegerField(null = True)
    message = CharField(max_length = 1024)
    label = CharField(choices = LABEL_CHOICES, max_length = 16)
    def __unicode__(self):
        return u'%s %s %s' % (self.datetime, self.message, self.label)

class Attachment(Model):
    salvo = ForeignKey('Salvo', related_name = 'attachments')
    result = ForeignKey('Result', related_name = 'attachments', null = True)
    measure = ForeignKey('Measure', related_name = 'attachments', null = True)
    datetime = DateTimeField()
    creation_counter = IntegerField(null = True)
    name = CharField(max_length = 512)
    file = FileField(upload_to = 'bugwar/uploads')
    content_type = CharField(max_length = 128)

class Salvo(Model):
    battery = ForeignKey('Battery', null = True, related_name = 'salvos')
    owner = ForeignKey(User, null = True)
    start = DateTimeField(null = True, blank = True)
    stop = DateTimeField(null = True, blank = True)
    url = CharField(max_length = 1024, null = True, blank = True)
    revision = IntegerField(default = 0, null = True)
    configuration_json = CharField(max_length = 4096, null = True)

    def __unicode__(self):
        return u'%s' % self.id

    @property
    def configuration(self):
        import djata.formatter.json as json
        if self.configuration_json is None: return {}
        return json.loads(self.configuration_json)

    @property
    def passes(self):
        return self.results.filter(label = 'pass')

    @property
    def fails(self):
        return self.results.filter(label = 'fail')

    @property
    def errors(self):
        return self.results.filter(label = 'error')

    @property
    def warnings(self):
        return self.results.filter(label = 'warn')

    @property
    def url_display(self):
        display = urlparse(self.url and self.url or '')[2]
        if len(display) > 27:
            return '...%s' % display[-27:]
        return display

    @property
    def duration(self):
        return self.stop - self.start

    def delete(self):
        for log in self.logs.all():
            log.delete()
        for measure in self.measures.all():
            measure.delete()
        for result in self.results.all():
            result.delete()
        super(Salvo, self).delete()

class Battery(Model):
    name = CharField(max_length = 255, unique = True)
    #name = CharField(max_length = 255, primary = True)
    #created = DateTimeField(auto_now_add = True)

    def __unicode__(self):
        return self.name

    @property
    def latest_salvo(self):
        return self.salvos.latest('start')

    def delete(self):
        for salvo in self.salvos.all():
            salvo.delete()
        super(Battery, self).delete()

    class Meta:
        verbose_name_plural = 'batteries'

