API Documentation
===================

BadgrClient is the class that is responsible for authentication and calling of the APIs. The client also 
has some fetcher functions and some operations that dont fall spcifically under any 'Badgr Model'. For other
operations you will have to use the Badgr Models (Asserstion, BadgeClass, Issuer).

.. note::
   Keep in mind that the models can't do anything on their own so they still need to be passed a client instance to do it's job. 

.. toctree::
   :maxdepth: 4

   badgrclient.badgrclient
   badgrclient.badgrmodels
