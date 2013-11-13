from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.FormView.as_view(), name='calendar_form'),
    url(r'^(\d+)$', views.CalendarView, name='calendar_view'),
    url(r'^cars$', views.CarView.as_view(), name='car_list'),
    url(r'make-favorite$', views.make_favorite, name='make_favorite'),
    )

