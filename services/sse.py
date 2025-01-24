from utils.request import make_request


def events(user_to=None, users=None, request_data=None, data=None, event_code=None, kwargs=None):
    if users is None:
        users = []
    if user_to is not None:
        users.append(user_to['id'])
    else:
        users.append(1)
    if kwargs is None:
        kwargs = {}
    if data is None:
        data = {}
    if request_data is None:
        request_data = {'users_id': users, 'data': data, 'event_code': event_code, 'kwargs': kwargs}
    return make_request(
        endpoint='private/users/events/',
        method='POST',
        data=request_data,
        port=8005,
    )
