API Documentation
===================

BadgrClient is the class that is responsible for authentication and calling of the APIs. The client also 
has some fetcher functions and some operations that dont fall spcifically under any 'Badgr Model'. For other
operations you will have to use the Badgr Models (Asserstion, BadgeClass, Issuer).

You can init badgrclient by either providing credentials to its constructor or setting a .env file with
``BADGR_USERNAME`` and ``BADGR_PASSWORD``


.. toctree::
   :maxdepth: 4

   badgrclient.badgrclient
   badgrclient.badgrmodels
