
from django.conf.urls.defaults import *
import bugwar.models as models

urlpatterns = patterns('',
    #(r'^bare-bones(?=\.|/)', include('djata.urls'), {
    #    'models': 'bugwar.models',
    #}),
    (r'^assault(?=\.|/)$', include('djata.urls_model'), {
        'module_name': 'bugwar.views',
        'view_name': 'salvos',
    }),
    (r'^', include('djata.urls_root'), {
        'module_name': 'bugwar.views',
    }),
)

