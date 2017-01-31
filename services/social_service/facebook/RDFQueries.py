import sys
reload(sys)
sys.setdefaultencoding('utf8')


def facebook_link_account_query(rdf_unique_top_string, urrer_uuid,
                                fb_user_name, fb_user_id,
                                fb_user_email, fb_user_profile_picture, service_home_page='https://facebook.com'):
    """
        INSERT  DATA
        {
           <https://urer-client.local.revenew.nl/user/id> # rdf_unique_top
            sioc:account_of ?uniqueId;
            sioc:email ?email;
            foaf:accountServiceHomepage ?homepage;
            foaf:name ?username;
            foaf:accountName ?password.
        }
    """

    query_format = """
    INSERT DATA {{
        GRAPH <https://urrer.me/users> { 
            {}
            rdf:type sioc:UserAccount;
            sioc:account_of '{}';
            sioc:email '{}';
            foaf:accountServiceHomepage '{}';
            foaf:name '{}';
            foaf:accountName '{}';
            sioc:avatar '{}';
        }
    }}
    """
    query_string = query_format.format(unicode(rdf_unique_top_string), unicode(urrer_uuid),
                                       unicode(fb_user_email), unicode(service_home_page),
                                       unicode(fb_user_name), unicode(fb_user_id),
                                       unicode(fb_user_profile_picture))
    return query_string


def facebook_select_user_by_fb_id(facebook_friend_id):
    query_format = """SELECT ?uniqueId
        FROM <https://urrer.me/users>
        WHERE
        {{     ?facebookAccountIdentifier foaf:accountServiceHomepage 'https://facebook.com';
              foaf:accountName '{}';
              sioc:account_of ?uniqueId;
        }}
        """
    query_string = query_format.format(facebook_friend_id)
    return query_string


def facebook_insert_follow(urrer_id_me, urrer_id_friend):

    query_format = """
        INSERT DATA {{
            GRAPH <https://urrer.me/users> { 
              <https://urer-client.local.revenew.nl/user/{}> sioc:follows <https://urer-client.local.revenew.nl/user/{}>
            }
        }}
        """
    query_string = query_format.format(unicode(urrer_id_me),
                                       unicode(urrer_id_friend)
                                       )
    return query_string
