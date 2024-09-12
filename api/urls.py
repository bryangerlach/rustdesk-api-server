import django
if django.__version__.split('.')[0]>='4':
    from django.urls import re_path as url
else:
    from django.conf.urls import  url, include

from api import views
 
urlpatterns = [
    url(r'^login',views.login),
    url(r'^logout',views.logout),
    url(r'^ab',views.ab),
    url(r'^users',views.users),
    url(r'^peers',views.peers),
    url(r'^currentUser',views.currentUser),
    url(r'^sysinfo',views.sysinfo),
    url(r'^heartbeat',views.heartbeat),
    #url(r'^register',views.register), 
    url(r'^user_action',views.user_action),  # 前端
    url(r'^work',views.work),  # 前端
    url(r'^share',views.share),  # 前端
    url(r'^installers',views.installers),  # 前端
    url(r'^conn_log',views.conn_log),
    url(r'^file_log',views.file_log),
    url(r'^audit',views.audit),
    url(r'^clients',views.clients),
    url(r'^download',views.download),
    url(r'^generator',views.generator_view),
    url(r'^check_for_file',views.check_for_file),
    url(r'^creategh',views.create_github_run),
    url(r'^updategh',views.update_github_run),
    url(r'^save_custom_client',views.save_custom_client),
    url(r'^delete_file',views.delete_file),
    ]
