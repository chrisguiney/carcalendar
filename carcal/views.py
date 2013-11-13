from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect

from django.views.generic import View, ListView

from carcal.forms import CalendarForm
from carcal.models import Calendar, make_car_list, Car, CarDate


class FormView(View):
    def get(self, request):
        form = CalendarForm()
        return render(request, "carcal/calendar_form.html", {
                      "calendars": Calendar.objects.all(),
                      "form": form},
                      content_type="text/html")

    def post(self, request):
        form = CalendarForm(request.POST)

        try:
            if not form.is_valid():
                raise ValueError()
            calendar = form.save()
            start_date = form.cleaned_data.get("start_date")
            end_date = form.cleaned_data.get("end_date")

            car_list = make_car_list(Car.objects.all(),
                                     start_date, end_date - start_date)

            for date, car in car_list:
                CarDate(calendar=calendar, date=date, car=car).save()

            return redirect("/%s" % calendar.pk)

        except ValueError:
            return render(request, "carcal/calendar_form.html", {"form": form},
                          content_type="text/html")


def CalendarView(request, id):
    calendar = get_object_or_404(Calendar, pk=id)
    return render(request, "carcal/calendar_view.html", {"calendar": calendar},
                  content_type="text/html")


class CarView(ListView):
    model = Car


def make_favorite(request):
    car_id = request.POST.get("favorite", -1)
    car = get_object_or_404(Car, pk=car_id)
    car.make_favorite()
    return redirect("/cars")