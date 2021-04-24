# Quickstart

**badgrclient** is a python library for [Badgr](https://github.com/concentricsky/badgr-server) APIs

#### Installation

```bash
pip install badgrclient
```

### Docs

https://badgrclient.readthedocs.io/

#### Usage

Instantiate a client

```python
from badgrclient import BadgrClient

client = BadgrClient('username', 'password', 'client_id')
```

Fetch your entities with the client or by giving an entityId.

```python
>>> my_issuers = client.fetch_issuer()
[Issuer(7fde21f03a30dfg), Issuer(de21ce2d52df0)]

>>> baby_badger = client.fetch_badgeclass('<baby_badgr_entity_id>')[0]
BadgeClass(<baby_badgr_entity_id>)
```

Use member functions to perform actions on the entity

```python
>>> baby_badger.issue('jane@gmail.com')
Assertion(<entity_id>)
```

Or directly import a model and get going

```python
>>> from badgrclient import Assertion
>>> janes_assertion = Assertion(client, eid='<entity_id>')
Assertion(<entity_id>)

>>> janes_assertion.revoke('Revocation Reason')
```
