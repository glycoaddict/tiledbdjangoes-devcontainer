from django.contrib.auth import authenticate, login
from django.http import HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

import requests
import json
import logging

logger = logging.getLogger('django')
logger.setLevel(logging.INFO)

# Define the URL of the API endpoint for authentication
API_AUTH_URL = "https://prism.bii.karnanilab.com/prism/login/"

class MyBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        # Check the username/password and return a user.
        # auth_result = api_authenticate(request)  
            
        username = request.POST.get("username", username)
        password = request.POST.get("password", password)  
        
        response = requests.post(API_AUTH_URL, data=json.dumps({"username": username, "password": password}))
        try:
            # Check if the authentication was successful
            response.raise_for_status()  # Raise exception for non-OK response codes
        except:
            print('Authentication failed level 1')            
            return None
        
        data = response.json()
        
        # Check if the authentication was successful
        if (response.status_code == 200) and (data.get('data').get("username") == username):
            logger.info('Authentication success')
            # Get or create the user based on the username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                logger.info('create new user')                
                # no need for password since it will be API authenticating only.
                user = User(
                    username=username,
                    first_name=data.get('data').get('first_name'),
                    last_name=data.get('data').get('last_name'),
                    email=data.get('data').get('email'),
                    )
                # save user                              
                user.save()                                         
                # set permissions here if needed
                grp = Group.objects.get(name="prismUsers")                
                user.groups.add(grp)
                user.save()
            logger.info('Returning user')
            return user
        else:
            # Authentication failed
            # return HttpResponseBadRequest("Invalid login credentials")
            # raise PermissionDenied()
            logger.info('Authentication failed level 2')
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        

# @csrf_exempt
# def api_authenticate(username, password):
#     # Only process POST requests
#     if request.method != "POST":
#         return HttpResponseBadRequest("Invalid request method")

#     # Extract the username and password from the request POST data
#     username = request.POST.get("username")
#     password = request.POST.get("password")

#     # Call the API endpoint to authenticate the user
#     try:
#         response = requests.post(API_AUTH_URL, data={"username": username, "password": password})
#         response.raise_for_status()  # Raise exception for non-OK response codes
#         data = response.json()
#     except (requests.exceptions.RequestException, ValueError) as e:
#         return HttpResponseBadRequest("Unable to authenticate user: {}".format(str(e)))

#     # Check if the authentication was successful
#     print('data', data)
#     if data.get("success") == True:
#         # Get or create the user based on the username
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return HttpResponse("Authenticated successfully")
#     else:
#         # Authentication failed
#         return HttpResponseBadRequest("Invalid login credentials")