

def facebook_link_account_query(rdf_unique_top_string, urrer_uuid,
                                fb_user_name, fb_user_id,
                                fb_user_email, service_home_page='https://facebook.com'):
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
        {}
        sioc:account_of '{}';
        sioc:email '{}';
        foaf:accountServiceHomepage '{}';
        foaf:name '{}';
        foaf:accountName '{}';
    }}
    """
    query_string = query_format.format(str(rdf_unique_top_string), str(urrer_uuid),
                                       str(fb_user_email), str(service_home_page),
                                       str(fb_user_name.encode('ascii', 'ignore')), str(fb_user_id))
    return query_string


def facebook_select_user_by_fb_id(facebook_friend_id):
    query_format = """SELECT ?uniqueId
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
            <https://urer-client.local.revenew.nl/user/{}> sioc:follows <https://urer-client.local.revenew.nl/user/{}>
        }}
        """
    query_string = query_format.format(urrer_id_me, urrer_id_friend, urrer_id_friend, urrer_id_me)
    return query_string
