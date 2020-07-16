# BadgrClient
_A python library for Badgr APIs_


## Usage

Instantiate a client

```python
from badgrclient import BadgrClient

client = BadgrClient('username', 'password', 'client_id', 'rw:profile rw:issuer rw:backpack')
```
Fetch your entities with the client or by providing an entityId

```python
>>> my_issuers = client.get_issuer()
[Issuer(7fde21f03a30dfg), Issuer(de21ce2d52df0)]

>>> baby_badger = client.get_badgeclass('entity_id')[0]
BadgeClass(nm190nsk093msdf)
```

Use member functions to perform actions on the entity

```python
>>> baby_badger.issue('jane@gmail.com')
Assertion(amfsdlkmlsfmkfd)
```
