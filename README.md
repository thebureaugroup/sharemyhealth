# ShareMyHealth - An OAuth2 Provider for Health Care

This project is an OAuth2 Server and FHIR Server.  Here is some
of what you can do:


* Use the built in tools to proxy FHIR through OAuth2
* Register and manage applications (OAuth2 Clients)
* Connect this service to an upstream OpendID Connect Provider
* Build your own! You can build virtually any RESTful API or app
on top of this base project.

This tool is based off of work done on behalf of the
Office of the National Coordinator for Health Information
Technology (HHS ONC) and the  Centers for Medicare and Medicaid
Services (HHS CMS). It was built provider consumer-facing APIs and shares
a common code base with the CMS Blue Button 2.0 API. See https://bluebutton.cms.gov/
for more details.


Installation
------------

This project is based on Python 3.6 and Django 2.1.x. 

Download the project:


    git clone https://github.com/TransparentHealth/sharemyhealth.git
   

Install supporting libraries. (Consider using virtualenv for your python setup).


    cd sharemyhealth
    pip install -r requirements.txt

Depending on your local environment you made need some supporting libraries
for the above command to run cleanly. For example you need a 
compiler and python-dev.

Setup some local environment variables. 


    export ALLOWED_HOSTS="*"
    export EC2PARAMSTORE_4_ENVIRONMENT_VARIABLES=".ENV" 
    
The `EC2PARAMSTORE_4_ENVIRONMENT_VARIABLES`  setting says to look for envvars in a file called `.env`. If this string is `EC2_PARAMSTORE`,
the anything in `.env` will be overridden with parameters in an AWS EC2 Parameter store.
There are a number of variables that can be set based on your
specific environment and setup.  This is how you can brand the project to your needs.
See the `settings.py` and for a full list.  Below are some basic variable you may want to set.


    export AWS_ACCESS_KEY_ID="YOUR_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
    export DJANGO_SUPERUSER_USERNAME="youruser"
    export DJANGO_SUPERUSER_PASSWORD="yourpassword"
    export DJANGO_SUPERUSER_EMAIL="super@example.com"
    export DJANGO_SUPERUSER_FIRST_NAME="Super"
    export DJANGO_SUPERUSER_LAST_NAME="User"
    export ALLOWED_HOSTS="*"


Just add the above to a `.env` and then do a 'source .env' to make the changes take effect.
See https://docs.djangoproject.com/en/2.2/topics/settings/ for all the details about Django settings.

Create the database:


    python manage.py migrate


Create a superuser (Optional)


    python manage.py create_super_user_from_envars

    
Create a Sample Application (So the test Client application  will work as expected.)


    python manage.py create_test_user_and_application

Be Sure to register this application in the OIDC Server and then set the values in your `.env`.
For example your `.env` file may contain the following lines:


     export SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_KEY="sharemyhealth-1kjdfkdjfasasas"
     export SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_SECRET="sharemyhealth-dsjkfj87234ndsh89r3b434y8dTWocG"
     export SOCIAL_AUTH_VERIFYMYIDENTITY_OPENIDCONNECT_OIDC_ENDPOINT="http://verifymyidentity:8000"

If running this server and the OIDC server locally lom the same machine for development,
we recommend setting up names for each server host in `/etc/hosts`.
You might add lines like the following to that file:


     127.0.0.1       smhapp
     127.0.0.1       verifymyidentity
     127.0.0.1       sharemyhealth

In development our convention is to run `vmi` on port `8000`, `sharemyhealth` on 8001, and `smh_app` on `8002`.
To start this server on port 8001 issue the following command.


     python manage.py runserver 8001


Advanced Connectivity Topics
=============================


Connecting to a Backend FHIR service
------------------------------------

The following settings illustrate how you can connect to an existing FHIR backend service (such as Microsoft Azure)
using OAuth2 client credentials grant type.


     export DEFAULT_FHIR_SERVER="https://example.azurehealthcareapis.com/"
     export DEFAULT_FHIR_URL_PREFIX="/fhir/R4"
     export BACKEND_FHIR_CLIENT_ID="xxxxxxxxxxxx-0000-11111-222222222222"
     export BACKEND_FHIR_CLIENT_SECRET="8347843ndnisd723nj23423cjbndu89er3i4jn3890d823r3r"
     export BACKEND_FHIR_RESOURCE="https://example.azurehealthcareapis.com"
     export BACKEND_FHIR_TOKEN_ENDPOINT="https://login.microsoftonline.com/ee75491b-f5a0-4a95-a1a0-a05eb719943c/oauth2/token"


Connecting to a Health Information Exchange (HIE)
-------------------------------------------------


This OAuth2 Provider can connect to an InterSystems-based backend. The `hie` app gets a CCDA(XML) document,
converts it to FHIR (JSON), and then serve it as a consumer-facing API via OAuth2.  If your organization is
interested in using this feature, please contact us.



## Deploy with Docker

Docker is supported. It will also configure a postgreSQL docker instance on 
port **5432**.

Run docker with:

     docker-compose -f .development/docker-compose.yml up
     
If you make changes to requirements.txt to add libraries re-run 
docker-compose with the --build option.

If you're working with a fresh db image the migrations have 
to be run.

## Associated Projects

[ShareMyHealth App](https://github.com/TransparentHealth/smh_app) is 
a personal health records for aggregating and sharing data with 
organizations.

ShareMyHealth acts as a relying party to 
[vmi](https://github.com/TransparentHealth/vmi).

ShareMyHealth is an OAuth2 Provider for the ShareMyHealth App.
https://github.com/TransparentHealth/smh_app


[VerifyMyIdentity - VMI](https://github.com/TransparentHealth/vmi), 
a standards-focused OpenID Connect Identity Provider.

## Supporting Resources

vmi uses css resources from Bootstrap (v.3.3.x) and 
Font-Awesome (v4.4.x). 

