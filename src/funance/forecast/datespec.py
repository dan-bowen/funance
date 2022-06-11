from typing import Union
import attr
import dateutil.parser as dp
import dateutil.rrule as dr

DATE_FORMAT = '%Y-%m-%d'

frequency_map = {
    'daily':   dr.DAILY,
    'weekly':  dr.WEEKLY,
    'monthly': dr.MONTHLY
}

weekday_map = {
    'mon': dr.MO,
    'tue': dr.TU,
    'wed': dr.WE,
    'thu': dr.TH,
    'fri': dr.FR,
    'sat': dr.SA,
    'sun': dr.SU
}


@attr.define(kw_only=True)
class DateSpec:
    start_date: str = attr.ib()
    end_date: str = attr.ib()
    frequency: str = attr.ib()
    interval: int = attr.ib()
    day_of_week: Union[str, None] = attr.ib()
    day_of_month: Union[int, None] = attr.ib()

    @classmethod
    def from_spec(cls, spec):
        return DateSpec(start_date=spec['start_date'], end_date=spec['end_date'],
                        frequency=spec['frequency'], interval=spec['interval'],
                        day_of_week=spec['day_of_week'], day_of_month=spec['day_of_month'])

    def generate_dates(self, start_date, end_date):
        """
        Generate dates according to spec. Filtered by start_date, end_date

        :param start_date:
        :param end_date:
        :return:
        """
        start_date = dp.parse(start_date)
        end_date = dp.parse(end_date)
        rrule_start = dp.parse(self.start_date)
        # Dates from spec could (more likely as time progresses) generate dates we don't care about.
        # Here we set the max `until` argument for the rrule.
        if self.end_date is None:
            # self.end_date from the spec could be None to define infinite dates.
            # There has to be a limit, so substitute None with end_date argument.
            rrule_end = end_date
        else:
            # Substitute if spec_end_date > end_date
            spec_end_date = dp.parse(self.end_date)
            rrule_end = end_date if spec_end_date > end_date else spec_end_date

        """
        Specify "last day of month" when self.day_of_month would exclude certain months.

        See this StackOverflow answer for discussion of the issue.
        https://stackoverflow.com/questions/38328313/dateutils-rrule-returns-dates-that-2-months-apart/38555283#38555283
        """
        day_of_month = self.day_of_month
        if day_of_month in [29, 30, 31]:
            """
            Specify "last day of the month" by passing bymonthday=-1 to the rrule generator, thereby including 
            months like February where self.day_of_month would be "out of bounds".

            TODO Fix edge cases 

            This solution still leaves edge cases where, for example:

            day_of_month = 29
            October has 31 days
            Date generated as 2021-10-31
            More accurate would be 2021-10-29
            """
            day_of_month = -1
        rr = dr.rrule(
            frequency_map.get(self.frequency),
            dtstart=rrule_start,
            until=rrule_end,
            interval=self.interval,
            byweekday=weekday_map.get(self.day_of_week),
            bymonthday=day_of_month
        )
        dates = list(rr)
        # Filter start dates. End dates were limited in rrule
        dates = [d for d in dates if d >= start_date]
        return dates
