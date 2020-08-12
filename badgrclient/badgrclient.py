import requests
import logging
import datetime
import base64
from .badgrmodels import (
    Assertion,
    BadgeClass,
    Issuer,
    )
from typing import List, Union
from .exceptions import APIError, BadgrClientError

MODELS = {
    'Assertion': Assertion,
    'BadgeClass': BadgeClass,
    'Issuer': Issuer,
}

IMAGE_MIME_TYPES = {
    'svg': 'image/svg+xml',
    'png': 'image/png',
}

Logger = logging.getLogger('badgrclient')


class BadgrClient:

    def __init__(
        self,
        username: str = None,
        password: str = None,
        client_id: str = None,
        scope: str = 'rw:profile rw:issuer rw:backpack',
        base_url: str = 'http://localhost:8000',
        token: str = None,
        refresh_token: str = None,
        unique_badge_names: bool = False,
    ):
        """Initalize a new client

        Args:
            username: Badgr username(or email). Defaults to None.
            password: Badgr password. Defaults to None.
            client_id: client_id to use to connect to badgr. Defaults to None.
            scope: OAuth Scope. Defaults to None.
            base_url: badgr-server's url. Defaults to 'http://localhost:8000'.
            token: Token to use for auth. Defaults to None.
            refresh_token: Refresh token to use for auth. Defaults to None.
            unique_badge_names: Declares that badge_names per issuer are
                unique and canbe used as a unique identifier for operations.
                Call load_badge_names with appropriate issuer id after init
                or only badges you create will get registered
        """
        self.session = requests.session()
        self.header = {}
        self.refresh_token = refresh_token
        self.token_expires_at = None
        self.scope = scope
        self.client_id = client_id
        self.base_url = base_url
        self.unique_badge_names = unique_badge_names

        if self.unique_badge_names:
            # Make a dictonary to keep track of badgenames and entity IDs
            # for each issuer
            self.badge_names = {}

        if token:
            if not refresh_token:
                raise BadgrClientError('For authentication with token, also provide a \
                    refresh token')
            self.header = {'Authorization': 'Bearer {}'.format(token)}
        else:
            self._get_auth_token(username, password)

    def _call_api(
            self,
            endpoint,
            method='GET',
            params=None,
            data=None,
            auth=True) -> dict:
        """Method used to call the API.
        It returns the raw JSON returned by the API or raises an exception
        if something goes wrong.
        Args:
            endpoint: the endpoint to call
            method: the HTTP method to use when calling the specified
            URL, can be GET, POST, DELETE, UPDATE...
            Defaults to GET
            params: the params to specify to a GET request
            data: the data to send to a POST request
            auth: Wether authorization is required
        """
        if auth and self.token_expires_at:
            if self.token_expires_at < datetime.datetime.now():
                self._get_auth_token()

        url = self.base_url + endpoint
        header = self.header

        if not auth and 'Authorization' in header:
            header.pop('Authorization')

        req = self.session.request(
            method=method,
            url=url,
            params=params,
            headers=self.header,
            json=data,
            verify=True,
        )

        response = self._get_json(req)

        return response

    @staticmethod
    def _get_json(req):
        """
        Get json from response
        """
        response = None
        try:
            response = req.json()
        except Exception as err:
            Logger.debug(req.text)
            raise APIError('Error while decoding JSON: {0}'.format(err))

        if req.status_code >= 300:
            Logger.error(response)
            if 'error' in response:
                raise APIError(response['error'])

        if 'status' in response:
            if not response['status']['success']:
                Logger.error(response)
                if 'description' in response['status']:
                    raise APIError(response['status']['description'])

        return response

    def _get_auth_token(self, username=None, password=None):
        """Fetches token and sets header for api calls. Uses refresh_token
        if username and password isn't provided

        Args:
            username (string): Badgr username
            password (string): Badgr password
        """
        now = datetime.datetime.now()

        payload = {
            'client_id': self.client_id,
        }

        if self.scope:
            payload['scope'] = self.scope

        if username and password:
            payload['username'] = username
            payload['password'] = password
            payload['grant_type'] = 'password'
        elif self.refresh_token:
            payload['refresh_token'] = self.refresh_token
            payload['grant_type'] = 'refresh_token'
            self.refresh_token = None

        req = requests.post(
            self.base_url + '/o/token',
            data=payload
        )

        response = self._get_json(req)

        self.token_expires_at = now + datetime.timedelta(
            seconds=response['expires_in'])
        self.refresh_token = response['refresh_token']
        self.header = {
            "Authorization": "Bearer " + response['access_token']
        }

    def _deserialize(self, result: list) -> List[
            Union[BadgeClass, Assertion, Issuer]]:
        """
            Get the appropriate model instances list from result list
        Args:
            result: The result in the payload

        """
        return_value = []

        for i in result:
            entityType = i['entityType']
            if MODELS[entityType]:
                return_value.append(
                    MODELS[entityType](self).set_data(i))
            else:
                return_value.append(i)

        return return_value

    def _fetch_id_or_self(self, endpoint, eid):
        """Appends entityId to endpoint if provided and calls it

        Args:
            endpoint (string): Endpoint to call
            eid ([type]): entityId
        """
        if eid:
            ep = endpoint + '/{}'.format(eid)
            response = self._call_api(ep)
        else:
            response = self._call_api(endpoint)

        return self._deserialize(response['result'])

    def _save_badge_name(self, badge: BadgeClass):
        """
        Add a single badge to it's issuers list
        Args:
            badge (BadgeClass): Badge to save
        """
        eid = badge.entityId
        badge_name = badge.data.get('name', None)
        issuer_eid = badge.data.get('issuer', None)

        if not (eid or badge_name or issuer_eid):
            Logger.error(
                'Unable to read badge while updating badge_name\
                index: {}'.format(badge))
            return

        if not self.badge_names.get('issuer_eid', None):
            self.badge_names[issuer_eid] = {}

        self.badge_names[issuer_eid][badge_name] = eid

    def load_badge_names(self, issuer_eid: str):
        """
        (Re)loads the badge name index for an issuer
        Args:
            issuer_eid (str): eid of the issuer
        """
        issuer = Issuer(self, issuer_eid)
        issuers_badges = issuer.fetch_badgeclasses()

        for badge in issuers_badges:
            self._save_badge_name(badge)

    def get_eid_from_badge_name(self, badge_name: str, issuer_eid: str):
        """Get eid from badge name and in's issuer eid
        Args:
            badge_name (string): Name of badge.
            issuer_eid (string): entityId of the the issuer badge belongs to
        """
        if not (badge_name or issuer_eid):
            return None

        badge_names = self.badge_names

        if badge_names.get(issuer_eid, False) \
                and badge_names[issuer_eid].get(
                    badge_name, False):
            return badge_names[issuer_eid][badge_name]

        return None

    @staticmethod
    def encode_image(file: str):
        """
        Encode file to base64 data-uri string
        Args:
            file (str): the path to file
        """
        extension = file.split('.')[-1]
        mime_type = IMAGE_MIME_TYPES[extension]

        if not mime_type:
            raise BadgrClientError('Image format {} not \
                supported'.format(extension))

        with open(file, 'rb') as img_f:
            encoded_string = 'data:{};base64,{}'.format(
                mime_type,
                base64.b64encode(img_f.read()).decode('utf8'),
            )

            return encoded_string

    def fetch_tokens(self):
        """Get a list of access tokens for authenticated user
        """
        response = self._call_api('/v2/auth/tokens')
        return response.result

    def fetch_assertion(self, eid=None) -> List[Assertion]:
        """
        Get Assertion of the specified entityId, if eid is not provided
        then get a list of Assertions in authenticated user's backpack
        Args:
            eid (string, optional): entityId of the entity to fetch.
            Defaults to None.
        """

        if eid:
            ep = Assertion.ENDPOINT + '/{}'.format(eid)
        else:
            ep = '/v2/backpack/assertions'

        response = self._call_api(ep)

        return self._deserialize(response['result'])

    def fetch_badgeclass(self, eid=None) -> List[BadgeClass]:
        """
        Get BadgeClass of the specified entityId, if eid is not provided
        then get a list of BadgeClasses for authenticated user
        Args:
            eid (string, optional): entityId of the entity to fetch.
            Defaults to None.
        """

        return self._fetch_id_or_self(BadgeClass.ENDPOINT, eid)

    def fetch_issuer(self, eid=None) -> List[Issuer]:
        """
        Get Issuer of the specified entityId, if eid is not provided
        then get a list of Issuers for authenticated user
        Args:
            eid (string, optional): entityId of the entity to fetch.
            Defaults to None.
        """
        return self._fetch_id_or_self(Issuer.ENDPOINT, eid)

    def fetch_collection(self, eid=None):
        """
        Get Collection of the specified entityId, if eid is not provided
        then get a list of collections for authenticated user
        Args:
            eid (string, optional): entityId of the entity to fetch.
            Defaults to None.
        """
        return self._fetch_id_or_self('/v2/backpack/collections', eid)

    def revoke_assertions(self, ids, reason='Revoked by badgerclient'):
        """Revoke multiple assertions

        Args:
            ids (list): List of entityIds of Assertionsto revoke
            reason (string): Revocation reason, defaults to
            'Revoked by badgerclient'
        """
        payload = []

        for eid in ids:
            payload.append({
                'entityId': eid,
                'revocationReason': reason
            })

        return self._call_api('/v2/assertions/revoke', 'POST', data=payload)

    def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        marketing_opt_in: bool = False,
        agreed_terms_service: bool = True,
    ):

        if not email:
            raise Exception('Email is required to make an account')

        if not password:
            raise Exception('Password is required to make an account')

        payload = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'marketing_opt_in': marketing_opt_in,
            'agreed_terms_service': agreed_terms_service
        }

        response = self._call_api(
            '/v1/user/profile', 'POST', data=payload,
            auth=False)

        return response
