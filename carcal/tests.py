from datetime import timedelta, datetime
import random

from django.test import TransactionTestCase, TestCase, Client

from carcal.models import Car, make_car_list, is_weekend, is_sunday, is_saturday, CarDate, Calendar, get_week, get_favorite_set


class DateUtilsTest(TestCase):
    def testIsWeekend(self):
        d = datetime(2013, 11, 10)
        self.assertTrue(is_weekend(d))

    def testIsSunday(self):
        d = datetime(2013, 11, 10)
        self.assertTrue(is_sunday(d))

    def testIsSaturday(self):
        d = datetime(2013, 11, 9)
        self.assertTrue(is_saturday(d))

    def testGetWeekKnown(self):
        car_list = [
            (datetime(2014, 5, 3), Car.objects.get(pk=15)),
            (datetime(2014, 5, 4), Car.objects.get(pk=7)),
            (datetime(2014, 5, 5), Car.objects.get(pk=1)),
            (datetime(2014, 5, 6), Car.objects.get(pk=19)),
            (datetime(2014, 5, 7), Car.objects.get(pk=12)),
            (datetime(2014, 5, 8), Car.objects.get(pk=20)),
            (datetime(2014, 5, 9), Car.objects.get(pk=13)),
            (datetime(2014, 5, 10), Car.objects.get(pk=1)),
            ]

        known_sunday = datetime(2014, 5, 4)
        self.assertTrue(is_sunday(known_sunday))

        week = get_week(datetime(2014, 5, 10), car_list)
        self.assertEquals(week[0][0].day, 4)

    def testGetWeekSimple(self):
        curdate = datetime(2013, 11, 10)
        calendar = [curdate]

        for i in xrange(1, 10):
            curdate += timedelta(days=1)
            calendar.append(curdate)

        week = get_week(curdate, calendar)
        self.assertTrue(is_sunday(week[0]))

        calendar = calendar[:3]
        self.assertTrue(is_sunday(get_week(curdate, calendar)[0]))

class CalendarUtilsTest(TransactionTestCase):
    def testGetFavoriteSet(self):
        cur_day = datetime(2014, 5, 10)
        favorites = [Car.objects.get(pk=1)]
        car_list = [
            (datetime(2014, 5, 3), Car.objects.get(pk=15)),
            (datetime(2014, 5, 4), Car.objects.get(pk=7)),
            (datetime(2014, 5, 5), Car.objects.get(pk=1)),
            (datetime(2014, 5, 6), Car.objects.get(pk=19)),
            (datetime(2014, 5, 7), Car.objects.get(pk=12)),
            (datetime(2014, 5, 8), Car.objects.get(pk=20)),
            (datetime(2014, 5, 9), Car.objects.get(pk=13)),
        ]
        week = get_week(cur_day, car_list)
        favorite_set = get_favorite_set(week, favorites)
        self.assertTrue(favorite_set <= set(favorites))



class CarTest(TransactionTestCase):
    def testVehicleClass(self):
        car = Car.make("Porsche_test", "GT3", "fast")
        self.assertEquals(car.vehicle_class, "fast")

    def testMakeFavorite(self):
        old_favorite = Car.objects.get(pk=1)
        self.assertTrue(old_favorite.is_favorite)
        car = Car.objects.get(pk=3)
        car.make_favorite()

        self.assertTrue(car.is_favorite)
        old_favorite = Car.objects.get(pk=1)
        self.assertFalse(old_favorite.is_favorite)

        old_favorite.make_favorite(car)
        self.assertFalse(car.is_favorite)
        self.assertTrue(old_favorite.is_favorite)


class CalendarTest(TransactionTestCase):

    def setUp(self):
        super(CalendarTest, self).setUp()
        # Set the seed for deterministic behavior
        random.seed(1)
        self.cars = Car.objects.all()

    def testCanGenerateList(self):
        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))
        self.assertIsInstance(car_list, list)
        self.assertEquals(len(car_list), 52*7*6)

    def testNoDuplicateDays(self):
        car_list = make_car_list(self.cars, datetime(2010, 11, 10), timedelta(weeks=52*6))
        self.assertIsInstance(car_list, list)
        self.assertEquals(len(set([x[0] for x in car_list])), 52*7*6)

    def testFavoriteCarChosenEveryWeek(self):
        start_date = datetime(2013, 11, 10)
        delta = timedelta(weeks=52)
        car_list = make_car_list(self.cars, start_date, delta)
        num_occurrences = len(filter(lambda x: x[1].is_favorite, car_list))

        self.assertEqual(num_occurrences, 52)

        try:
            self.assertLessEqual(num_occurrences, 52)
        except AssertionError:
            cur_date = start_date
            times_seen = 0
            it = 0
            while cur_date <= start_date + delta:
                if is_sunday(car_list[it][0]):
                    times_seen = 0
                if car_list[it][1].is_favorite:
                    times_seen += 1
                if times_seen > 1:
                    print "fuck"
                    cl = car_list[it-7:it+7]
                    for d, c in cl:
                        c_str = str(c)
                        if c.is_favorite:
                            c_str += "*"
                        d_str = str(d)
                        if is_sunday(d):
                            d_str += "*"
                        print d_str, c_str, c.pk

                    print cur_date
                it += 1
                cur_date += timedelta(days=1)
                self.fail("There are not 52 instances of the favorite car")
    def testNoBackToBackManufacturers(self):
        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))

        for i, car in enumerate(car_list):
            if i != 0:
                self.assertNotEquals(car[1].manufacturer, car_list[i-1][1].manufacturer)

    def testWeekendFavorites(self):
        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))
        weekend_cars = filter(lambda x: is_weekend(x[0]), car_list)
        weekend_car_prefer = filter(lambda x: x[1].vehicle_class == "fast", weekend_cars)

        self.assertTrue(len(weekend_car_prefer) > len(weekend_cars) / 2)

    def testWeekdayFavorites(self):
        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))
        weekday_cars = filter(lambda x: x[1].vehicle_class == "offroad", car_list)
        self.assertTrue(len(filter(lambda x: not is_weekend(x[0]), weekday_cars)) > len(weekday_cars) / 2)

    def testCreateCalendar(self):
        cal = Calendar(name="test cal")
        cal.save()

        self.assertEquals(len(Calendar.objects.all()), 2) # One is loaded in the fixture

    def testCreateCarDates(self):
        cal = Calendar(name="test cal")
        cal.save()

        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))

        for car in car_list:
            CarDate(calendar=cal, date=car[0], car=car[1]).save()

        self.assertEquals(len(cal.cardate_set.all()), len(car_list))

    def testWeeks(self):
        cal = Calendar(name="test cal")
        cal.save()

        car_list = make_car_list(self.cars, datetime(2013, 11, 10), timedelta(weeks=52*6))

        for car in car_list:
            CarDate(calendar=cal, date=car[0], car=car[1]).save()

        self.assertEquals(len(cal.weeks), 52*6)


class CalendarViewTest(TransactionTestCase):

    def testGet(self):
        client = Client()
        resp = client.get('/')
        self.assertEquals(resp.status_code, 200)

    def testPost(self):
        client = Client()
        resp = client.post('/', {
            "name": "test-post",
            "start_date": "2013-11-10",
            "end_date": "2013-12-30"
        })

        self.assertEquals(resp.status_code, 302)

        cal = Calendar.objects.get(name="test-post")
        self.assertIsInstance(cal, Calendar)
        self.assertGreater(len(cal.cardate_set.all()), 0)

        fail_resp = client.post('/', {
            "name": "test-post",
            "start_date": "2013-11-10",
            "end_date": "2013-12-30"
        })
        self.assertEquals(fail_resp.status_code, 200)

    def testCalendarNotFound(self):
        client = Client()
        resp = client.get("/123")
        self.assertEquals(resp.status_code, 404)


class CarViewTest(TransactionTestCase):
    def testMakeFavorite(self):
        car = Car.objects.get(pk=1)
        car2 = Car.objects.get(pk=3)
        self.assertTrue(car.is_favorite)
        self.assertFalse(car2.is_favorite)

        resp = Client().post("/make-favorite", {"favorite": 3})
        self.assertEquals(resp.status_code, 302)

        car = Car.objects.get(pk=1)
        self.assertFalse(car.is_favorite)

        car = Car.objects.get(pk=3)
        self.assertTrue(car.is_favorite)

