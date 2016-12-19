import re
from datetime import datetime

from django.utils import six

date_re = re.compile(
    r'(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4})$'
)


def parse_date(value):
    match = date_re.match(value)
    if match:
        kw = {k: int(v) for k, v in six.iteritems(match.groupdict())}
        return datetime.date(**kw)
