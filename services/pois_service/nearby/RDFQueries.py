# -*- coding: utf-8 -*-
import sys
from datetime import datetime
reload(sys)
sys.setdefaultencoding('utf8')


def update_user_location(urer_uid, lat_string, lon_string):
    """

    :param urer_uid:
    :return:
    """
    """
    DELETE WHERE {
        '1' geo:lat ?latitude.
        '1' geo:long ?longitude
        '1' sioc:last_activity_date ?updateTimeForDate
    };

    INSERT DATA {
      '1' geo:lat 'latitude_here';
          geo:long 'longitude_here';
          sioc:last_activity_date 'last_activity_date'.
    }
    """
    query_format = """
    DELETE WHERE {{
        GRAPH <https://urrer.me/users> {{
            '{}' geo:lat ?latitude;
             geo:long ?longitude;
             sioc:last_activity_date ?updateTimeForDate
        }}
    }};
    INSERT DATA {{
       GRAPH <https://urrer.me/users> {{
            '{}' geo:lat '{}';
                geo:long '{}';
                sioc:last_activity_date '{}'.
        }}
    }}
    """
    current_utc_date = datetime.utcnow().strftime('%b %d %Y %H:%M:%S')
    query_string = query_format.format(unicode(urer_uid), unicode(urer_uid),
                                       unicode(lat_string), unicode(lon_string),
                                       unicode(current_utc_date)
                                       )
    return query_string
