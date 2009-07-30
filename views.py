
from django.http import HttpResponseRedirect
from djata.views2 import *
from djata.formats.format_html_chart import HtmlChartModelFormat
import bugwar.models as models
import bugwar.settings
from commons import *

default_format = 'html'

class Views(Views):
    def __call__(self, request):
        return HttpResponseRedirect("batteries.html")

class BugwarView(View):
    class Meta:
        abstract = True

    def process_extra(self, request):
        context = request.context
        if 'embed' in request.GET:
            context['embed'] = True

class Battery(BugwarView):
    class Meta:
        insecure = True
        default_page_length = 50
        default_page_number = -1
        index = 'name'

    def order(self, objects):
        return super(Battery, self).order(objects)
        # this didn't work out because lists don't have the "get" method, among other
        # things that query set collections provide (although the system does tollerate "all"
        # already)
        return sorted(
            super(Battery, self).order(objects).all(),
            cmp = datetime_cmp,
            key = lambda object: object.latest_salvo.stop
        )

    class HtmlModelFormat(HtmlModelFormat):
        template = 'bugwar/batteries.html'

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/battery.html'

    class Status(HtmlObjectFormat):
        name = 'status.html'
        template = 'bugwar/battery-status.html'

        def process_extra(self, request, view):
            battery = view.get_object()
            context = request.context

            latest_salvo = battery.salvos.latest('stop')
            try:
                salvo_in_progress = battery.salvos.filter(stop = None).latest('start')
                if not latest_salvo.start < salvo_in_progress.start:
                    salvo_in_progress = None
            except models.Salvo.DoesNotExist:
                salvo_in_progress = None

            context['latest_salvo'] = latest_salvo
            context['salvo_in_progress'] = salvo_in_progress

class Entry(dict):
    pass

class Timeline(BugwarView):

    class Meta:
        model = models.Salvo
        insecure = True
        default_page_length = 800
        default_page_number = -1
        visible = False
        verbose_name = 'timeline'

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/timeline.html'

        def process_extra(self, request, view):
            context = request.context
            salvo = view.get_object()

            log = sorted(chain(
                chain(*(
                    chain(
                        (
                            Entry({
                                'result': True,
                                'datetime': result.datetime,
                                'label': result.label,
                                'object': result,
                            }),
                        ),
                        (
                            Entry({
                                'log': True,
                                'datetime': log.datetime,
                                'label': log.label,
                                'object': log,
                            })
                            for log in result.logs.all()
                        )
                    )
                    for result in salvo.results.all()
                )),
                chain(*(
                    chain(
                        (
                            Entry({
                                'measure': True,
                                'datetime': measure.datetime,
                                'label': 'info',
                                'object': measure,
                            }),
                        ),
                        (
                            Entry({
                                'log': True,
                                'datetime': log.datetime,
                                'label': log.label,
                                'object': log,
                            })
                            for log in measure.logs.all()
                        )
                    )
                    for measure in salvo.measures.all()
                )),
                (
                    Entry({
                        'log': True,
                        'datetime': log.datetime,
                        'label': log.label,
                        'object': log,
                    })
                    for log in salvo.logs.all()
                    if log.result is None and log.measure is None
                ),
                (
                    Entry({
                        'attachment': True,
                        'datetime': log.datetime,
                        'label': 'attach',
                        'object': attachment,
                    })
                    for attachment in salvo.attachments.all()
                ),
            ), key = lambda event: (
                event['object'].creation_counter,
                event['datetime'],
                event['object'].pk
            ))

            log = view.paginate_for_request(log)

            context['log'] = log

class Assault(BugwarView):
    class Meta:
        model = models.Battery
        insecure = True
        default_page_length = 7
        default_page_number = -1
        visible = False
        verbose_name = 'assault'
        verbose_name_plural = 'assaults'
        index = 'name'

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/assault.html'
        def process_extra(self, request, view):
            context = request.context
            battery = view.get_object()
            salvos = battery.salvos.order_by('start', 'id').all()

            salvos = view.paginate_for_request(salvos)

            context['salvos'] = salvos

            context['results'] = [
                {
                    'name': name,
                    'results': [
                        only(salvo.results.filter(name = name).all())
                        for salvo in salvos
                    ],
                }
                for name in commons([
                    [
                        result.name
                        for result in row
                    ] for row in (
                        salvo.results.filter(
                            Q(label = 'pass') |
                            Q(label = 'fail') |
                            Q(label = 'error')
                        ).all()
                        for salvo in salvos
                    )
                ])
            ]

            context['measures'] = [
                {
                    'name': name,
                    'measures': [
                        only(salvo.measures.filter(name = name).all())
                        for salvo in salvos
                    ],
                }
                for name in commons([
                    [measure.name for measure in salvo.measures.all()]
                    for salvo in salvos
                ])
            ]

class Salvo(BugwarView):

    class Meta:
        insecure = True
        default_page_length = 50
        default_page_number = -1

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/salvo.html'

    class HtmlModelFormat(HtmlModelFormat):
        template = 'bugwar/salvos.html'

    class BatteryHtmlModelFormat(HtmlModelFormat):
        name = 'battery.html'
        template = 'bugwar/battery.html'

        def process_extra(self, request, view):
            context = request.context
            salvos = view.get_objects()

            table = [
                salvo.results.filter(
                    Q(label = 'pass') |
                    Q(label = 'fail') |
                    Q(label = 'error')
                ).all()
                for salvo in salvos
            ]

            context['salvos'] = salvos

            context['names'] = names = commons([
                [result.name for result in row]
                for row in table
            ])

            context['rows'] = [
                {
                    'name': name,
                    'results': [
                        only(salvo.results.filter(name = name).all())
                        for salvo in salvos
                    ],
                }
                for name in names
            ]

class Result(BugwarView):

    class Meta:
        default_page_length = 50
        default_page_number = -1
        insecure = True

    def filter(self, objects):
        if 'battery_name' in self._request.GET:
            objects = objects.filter(
                salvo__battery__name =
                self._request.GET['battery_name']
            )
        return super(Result, self).filter(objects)

    def process_extra(self, request):
        context = request.context
        context['settings'] = bugwar.settings
        context['embed'] = 'embed' in request.GET

    class HtmlModelFormat(HtmlModelFormat):
        template = 'bugwar/results.html'

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/result.html'
        def process_extra(self, request, view):
            result = view.get_object()
            log = list(
                (
                    Entry({
                        'log': True,
                        'datetime': log.datetime,
                        'label': log.label,
                        'object': log,
                    })
                    for log in result.logs.all()
                )
            )
            log = view.paginate_for_request(log)
            request.context['log'] = log

class Log(BugwarView):
    class Meta:
        insecure = True
        default_page_length = 800
        default_page_number = -1
        visible = False

class Measure(BugwarView):
    class Meta:
        insecure = True
        default_page_length = 50
        default_page_number = -1
        visible = False

    class HtmlModelFormat(HtmlModelFormat):
        template = 'bugwar/measures.html'

    class HtmlObjectFormat(HtmlObjectFormat):
        template = 'bugwar/measure.html'
        def process_extra(self, request, view):
            measure = view.get_object()
            log = list(
                (
                    Entry({
                        'log': True,
                        'datetime': log.datetime,
                        'label': log.label,
                        'object': log,
                    })
                    for log in measure.logs.all()
                )
            )
            log = view.paginate_for_request(log)
            request.context['log'] = log

    class HtmlChartModelFormat(HtmlChartModelFormat):
        x = 'datetime'
        y = 'value'
        series = 'name'
        width = 800
        height = 600

class Attachment(BugwarView):
    class Meta:
        insecure = True
        default_page_length = 800
        default_page_number = -1
        visible = False


def datetime_cmp(a, b):
    if a is None and b is None:
        return 0
    elif a is None or b is None:
        return (a is None) - (b is None)
    else:
        return cmp(a, b)

