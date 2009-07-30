
from django.conf.urls.defaults import *
import bugwar.models as models
from djata import djata

urlpatterns = patterns('',
    (r'^bare-bones(?=\./)$', include('djata.urls2'), {
        'models': 'bugwar.models',
    }),
    (r'^assault(?=\./)$', include('djata.urls2_model'), {
        'module_name': 'bugwar.views',
        'model_name': 'salvos',
    }),
    (r'^', include('djata.urls2_root'), {
        'module_name': 'bugwar.views'
    }),
)

