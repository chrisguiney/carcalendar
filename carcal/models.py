import hashlib
import logging
from random import choice
from datetime import timedelta, date, datetime

from django.db import models

LOGGER = logging.getLogger('django')

CLASS_CHOICES = (
    ("fast", "Fast"),
    ("normal", "Normal"),
    ("offroad", "Offroad")
)


class Car(models.Model):
    manufacturer = models.CharField(max_length=50, db_index=True)
    model = models.CharField(max_length=50, db_index=True)
    vehicle_class = models.CharField(max_length=32, choices=CLASS_CHOICES, db_index=True)
    is_favorite = models.NullBooleanField(unique=True)

    @classmethod
    def make(cls, manufacturer, model, vehicle_class, is_favorite=None):
        c = Car(**{"manufacturer": manufacturer,
                   "model": model,
                   "vehicle_class": vehicle_class,
                   "is_favorite": is_favorite})
        c.save()
        return c

    def make_favorite(self, old_favorite_obj=None):
        self.is_favorite = True

        if not old_favorite_obj:
            old_favorite = Car.objects.filter(is_favorite=True).get()
        else:
            old_favorite = old_favorite_obj

        old_favorite.is_favorite = None
        old_favorite.save()
        self.save()

    def __str__(self):
        return "%s, %s, %s" % (self.manufacturer, self.model, self.vehicle_class)


class Calendar(models.Model):
    name = models.CharField(max_length=200, unique=True)

    @property
    def weeks(self):
        weeks = []
        days = []
        for car_date in self.cardate_set.all():
            days.append(car_date)
            if is_saturday(car_date.date):
                weeks.append(days)
                days = []
        return weeks

    def __str__(self):
        return self.name


class CarDate(models.Model):
    date = models.DateField()
    car = models.ForeignKey(Car)
    calendar = models.ForeignKey(Calendar)

    def __str__(self):
        return "%s: %s" % (self.date, self.car)


def is_saturday(dt):
    return dt.weekday() == 5


def is_sunday(dt):
    return dt.weekday() == 6


def is_weekend(dt):
    return is_saturday(dt) or is_sunday(dt)


def get_week(cur_day, calendar):
    try:
        return calendar[-(cur_day.isoweekday()+1):]
    except IndexError:
        return calendar


def cars_in_list(l):
    return (x[1] for x in l)


def get_favorite_set(week, favorite_cars):
    favorite_cars = set(favorite_cars)
    cars_in_week = set(cars_in_list(week))
    return favorite_cars - cars_in_week


def make_car_list(cars, start_date, delta):
    cur_day = start_date
    prev_manufacturer = None

    used_cars = set()
    all_cars = set(cars)

    fast_cars = set(filter(lambda x: x.vehicle_class == "fast", cars))
    normal_cars = set(filter(lambda x: x.vehicle_class == "normal", cars))
    offroad_cars = set(filter(lambda x: x.vehicle_class == "offroad", cars))

    favorite_cars = filter(lambda x: x.is_favorite is True, all_cars)
    has_favorite = len(favorite_cars) > 0

    weekend_options = [fast_cars, normal_cars, offroad_cars]
    weekday_options = [offroad_cars, normal_cars, fast_cars]

    calendar = []

    while cur_day < start_date + delta:
        must_retry = False

        prev_manufacturer_set = set(filter(lambda x: x.manufacturer == prev_manufacturer, all_cars))

        # If all cars have been used, any are available for use
        if all_cars <= used_cars:
            used_cars = set()

        # Favorite car is available if it hasn't been used since sunday
        week = get_week(cur_day, calendar)
        favorite_set = get_favorite_set(week, favorite_cars)

        # The last iteration made an impossible scenario
        if len((((all_cars - used_cars) | favorite_set) - prev_manufacturer_set)) == 0:
            must_retry = True
        else:
            options = weekend_options if is_weekend(cur_day) else weekday_options
            # Use the first vehicle class set that has available cars to use based on the options preference list
            for possible_car_set in options:
                # Exclude any used cars, and cars from the previous manufacturer,  include the favorite
                # Favorite will be an empty set once selected for the week
                car_set = (((possible_car_set - used_cars) | favorite_set) - prev_manufacturer_set)
                if len(car_set) != 0:
                    break

            try:
                car = choice(list(car_set))
                must_retry = False
                if car.is_favorite:
                    favorite_set = set()
            except IndexError:
                must_retry = True


        # If its the end of the week, and the favorite car hasn't been used,
        # Or some otherwise non-possible scenario has occurred
        # Roll back the week to preserve randomness of the favorite car choosing
        # as well as ensuring that the previous manufacturer is not used twice in a row.

        favorite_rollback_conditions = all([
            # It's the end of the week, or the last day
            (is_saturday(cur_day) or cur_day == start_date + delta),
            # A favorite car has been declared
            has_favorite,
            # The favorite car has not yet been used
            len(favorite_set) != 0])


        if any([must_retry, favorite_rollback_conditions]):
            # Rollback 13 days because the current day has not yet been applied
            rollback_date = max((cur_day - timedelta(days=13), start_date))
            rollback_days = (cur_day - rollback_date).days
            keep_days = len(calendar) - rollback_days
            calendar, discarded = calendar[:keep_days], set(x[1] for x in calendar[keep_days:])
            used_cars -= discarded
            cur_day = rollback_date

            try:
                prev_manufacturer = calendar[-1][1].manufacturer
            except IndexError:
                # The first week has been rolled back
                prev_manufacturer = None
            continue

        used_cars.add(car)
        calendar.append((cur_day, car))
        prev_manufacturer = car.manufacturer
        cur_day += timedelta(days=1)

    return calendar