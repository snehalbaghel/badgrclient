import pytest
import time
from badgrclient import BadgrClient, Issuer, BadgeClass, Assertion
from pathlib import Path


TOKEN_URL = 'http://localhost:8000/o/token'
TEST_IMAGE_PATH = str(Path('tests/test_image.png'))


def get_mock_auth_text(token: str = 'mock_token', expiry: int = 86400):
    return '{{"access_token": "{}", "expires_in": {}, \
        "token_type": "Bearer","scope": "rw:profile rw:issuer rw:backpack",\
        "refresh_token": "mock_refresh_token"}}'.format(token, expiry)


@pytest.fixture
def client(requests_mock):
    requests_mock.post(
        TOKEN_URL,
        text=get_mock_auth_text())

    client = BadgrClient(
        username='test',
        password='test_pass',
        client_id='kewl_client',
        scope='rw:profile rw:issuer rw:backpack')

    return client


def test_client_init(client):
    """Test client instance is correctly created
    """
    assert client.scope == 'rw:profile rw:issuer rw:backpack'
    assert client.refresh_token == 'mock_refresh_token'
    assert client.base_url == 'http://localhost:8000'
    assert client.header == {'Authorization': 'Bearer mock_token'}


def test_token_refresh(requests_mock):
    """Test token is refreshed after expiry
    """

    requests_mock.post(
        TOKEN_URL,
        text=get_mock_auth_text(expiry=1),)
    requests_mock.get(
        'http://localhost:8000/v2/backpack/assertions', text='{"result": []}')

    client = BadgrClient(
        username='test',
        password='test_pass',
        client_id='kewl_client',
        scope='rw:profile rw:issuer rw:backpack')

    # Wait for token to expire
    time.sleep(1)

    requests_mock.post(
        TOKEN_URL,
        text=get_mock_auth_text(token='refreshed_token'))
    # Call api to rigger refresh
    client.fetch_assertion()

    assert client.header == {'Authorization': 'Bearer refreshed_token'}


def test_fetch_tokens(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.fetch_tokens()
    BadgrClient._call_api.assert_called_once_with(
        '/v2/auth/tokens')


fetch_assertion_params = [
    (None, '/v2/backpack/assertions'),
    ('abcd', '/v2/assertions/abcd')]


@pytest.mark.parametrize("eid, expected", fetch_assertion_params)
def test_fetch_assertion(client, mocker, eid, expected):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.fetch_assertion(eid)
    BadgrClient._call_api.assert_called_once_with(expected)


fetch_badgeclass_params = [
    (None, '/v2/badgeclasses'),
    ('abcs', '/v2/badgeclasses/abcs')
]


@pytest.mark.parametrize("eid, expected", fetch_badgeclass_params)
def test_fetch_badgeclass(client, mocker, eid, expected):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.fetch_badgeclass(eid)
    BadgrClient._call_api.assert_called_once_with(expected)


fetch_issuer_params = [
    (None, '/v2/issuers'),
    ('abcs', '/v2/issuers/abcs')
]


@pytest.mark.parametrize("eid, expected", fetch_issuer_params)
def test_fetch_issuer(client, mocker, eid, expected):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.fetch_issuer(eid)
    BadgrClient._call_api.assert_called_once_with(expected)


fetch_collections_params = [
    (None, '/v2/backpack/collections'),
    ('abcs', '/v2/backpack/collections/abcs')
]


@pytest.mark.parametrize("eid, expected", fetch_collections_params)
def test_fetch_collections(client, mocker, eid, expected):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.fetch_collection(eid)
    BadgrClient._call_api.assert_called_once_with(expected)


def test_revoke_assertions(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.revoke_assertions(['asd', 'lknd3kn4'])
    BadgrClient._call_api.assert_called_once_with(
        '/v2/assertions/revoke',
        'POST',
        data=[{
            'entityId': 'asd',
            'revocationReason': 'Revoked by badgerclient'},
            {
            'entityId': 'lknd3kn4',
            'revocationReason': 'Revoked by badgerclient'
        }])


def test_create_user(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    client.create_user(
        'Jane',
        'Doe',
        'jane@gmail.com',
        'test_pass'
    )
    BadgrClient._call_api.assert_called_once_with(
        '/v1/user/profile',
        'POST',
        data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@gmail.com',
            'password': 'test_pass',
            'marketing_opt_in': False,
            'agreed_terms_service': True
        },
        auth=False
    )


def test_encode_image(client):
    encoded_string = client.encode_image(TEST_IMAGE_PATH)
    assert encoded_string == 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQYV2Ng+M9QDwADgQF/iwmQSQAAAABJRU5ErkJggg=='  # noqa: E501


def test_create_issuer(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    Issuer(client).create(
        'Fedora',
        'Fedora Issuer',
        'test@fedoraproject.org',
        'http://fegora.org',
        client.encode_image(TEST_IMAGE_PATH)
    )
    BadgrClient._call_api.assert_called_once_with(
        '/v2/issuers',
        'POST',
        data={
            'name': 'Fedora',
            'description': 'Fedora Issuer',
            'email': 'test@fedoraproject.org',
            'url': 'http://fegora.org',
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQYV2Ng+M9QDwADgQF/iwmQSQAAAABJRU5ErkJggg=='  # noqa: E501
        }
    )


def test_create_badgeclass(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    BadgeClass(client).create(
        'Speak Up!',
        client.encode_image(TEST_IMAGE_PATH),
        'Participated in an IRC meeting.',
        'aeIo_u',
        criteria_url='https://github.com/dtgay/badges/blob/master/docs/badges.rst',
        tags=['irc', 'community']
    )
    BadgrClient._call_api.assert_called_once_with(
        '/v2/badgeclasses',
        'POST',
        data={
            'name': 'Speak Up!',
            'issuer': 'aeIo_u',
            'description': 'Participated in an IRC meeting.',
            'criteria_url': 'https://github.com/dtgay/badges/blob/master/docs/badges.rst',  # noqa: E501
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQYV2Ng+M9QDwADgQF/iwmQSQAAAABJRU5ErkJggg==',  # noqa: E501
            'tags': ['irc', 'community'],
            'alignments': [],
            'expires': None,
            'criteria_text': None,
        }
    )


def test_issuer_fetch_assertions(client, mocker):
    mocker.patch('badgrclient.BadgrClient._call_api')
    evidence = [{
            'url': 'evidence.com',
            'narrative': 'evidence narraive'
        }]
    Assertion(client).create(
        'bc_eid',
        'jane@mailg.com',
        'test narrative',
        evidence,
        '2018-11-26T13:45:00Z',
        '2022-11-26T13:45:00Z',
    )
    BadgrClient._call_api.assert_called_once_with(
        '/v2/badgeclasses/bc_eid/assertions',
        'POST',
        data={
            'recipient': {
                'type': 'email',
                'identity': 'jane@mailg.com',
            },
            'narrative': 'test narrative',
            'evidence': evidence,
            'expires': '2018-11-26T13:45:00Z',
            'issuedOn': '2022-11-26T13:45:00Z',
            'notify': True,
        }
    )
