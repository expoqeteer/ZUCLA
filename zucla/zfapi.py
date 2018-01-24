#    Zenfolio API implemented as a python class
#
#    For more information, see http://github.com/bryanmason/ZUCLA
# 
#    Copyright (c) 2011-2013 Bryan Mason
#
#    This file is part of ZUCLA.
#   
#    ZUCLA is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
#    ZUCLA uses the public ZenfolioAPI documented at
#    http://www.zenfolio.com/zf/tools/api.aspx.  ZUCLA and Zenfolio are
#    not affiliated and Zenfiolio does not endorse the use of ZUCLA to 
#    access the Zenfiolo service.
#
###############################################################################
#
# Function List:
#
# _open_connection (INTERNAL):          Open a connection to the zf host
# debug:                                Get/set debugging state
# zf_host:                              Get/set host name
# api_path:                             Get/Set ZF API Path
# state:                                Get API state
# zfapi_error:                          Get API Error object
# zfapi_response:                       Get last API response
# success:                              Get success of last method call
# _make_call (INTERNAL):                Make a call to the API
# Authenticate:                         Challenge/Response auth
# AuthenticatePlain:                    Plain text auth
# LoadGroupHierarchy:                   Load the complete GroupHierarchy
# LoadPhotoSet:                         LoadPhotoSet
# UploadPhototoURL:                     Upload a photo to the Gallery URL
# CreatePhotoSet:                       CreatePhotoSet
# CreateGroup:                          CreateGroup
# DeletePhoto:                          DeletePhoto
#
###############################################################################

import httplib
import json
from hashlib import sha256
from struct import pack, unpack
import os
import time
from urllib import urlencode

class ZfAPI:
    """Implements the Zenfolio API, version 1.4"""

    # Status definitions
    (Closed, GotChallenge, Authenticated) = range(0,3)

    _last_http_response = None
    _last_zfresponse = None
    _conn = None
    _state = Closed
    _zf_token = None
    _username = ""
    _ssl = 1
    _zf_host = "www.zenfolio.com",
    _api_path = "/api/1.4/zfapi.asmx"
    debug = 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, 
                 ssl = 1, 
                 debug = 0, 
                 username = "", 
                 zf_host = "www.zenfolio.com",
                 api_path = "/api/1.4/zfapi.asmx"):
        """
        Initialize the class.

        Parameters:
        ssl:      zero - use HTTP (non SSL) connection; 
                  nonzero - use SSL. Defaults is SSL.
        debug:    zero - don't emit debug information; 
                  nonzero - be verbose. Default is no debug.
        username: Login name of the user. Defaults to "" 
        zf_host:  Host name to connect to (defaults to 
                  "www.zenfolio.com")
        api_path: path to the ZF API (defaults to "/api/1.4/zfapi.asmx")

        Returns: Nothing
        """

        self._username = username
        self.debug = debug
        self._ssl = ssl
        self._zf_host = zf_host
        self._api_path = api_path

        self._open_connection()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _open_connection(self):
        """
        INTERNAL_ONLY: Open a connection to the host whose address is
        stored in the class

        Params: None
        Returns: Nothing
        """
        # Close any existing connections.
        if ( self._conn ):
            self._conn.close()

        # Establish the connection
        if ( self._ssl == 1 ):
            self._conn = httplib.HTTPSConnection(self._zf_host)
        else:
            self._conn = httplib.HTTPConnection(self._zf_host)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def debug(self, debug=None):
        """
        Get/Set the current debugging state.

        Parameter: debug: None - don't change zero - no debugging; 
                   nonzero - debugging
        Returns:   previous value.
        """
        old_debug = self.debug
        if ( debug != None ):
            self.debug = debug
        return old_debug

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def zf_host(self, zf_host=None):
        """
        Get/set the name of the host which which we're communicating.

        Parameter: zf_host: String containing the name of the host.
                   None (default) mean's don't change the host.
        Returns: String containing the name of the old host.
        """
        old_host = self._zf_host
        if ( zf_host != None ):
            self._zf_host = zf_host
        
            # Close, and then reopen the connection.
            self._open_connection()

        return old_host

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def api_path(self, api_path=None):
        """
        Get/set the path to the Zenfoiio API.

        Parameter: api_path: String containing the Zenfolio API path.
                   Defailt (None) means don't change the path.
        Returns: Nothing
        """
        old_path = self._api_path
        if ( api_path != None ):
            self._api_path = api_path
            
        return old_path

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def state(self):
        """
        Get the current state of the API.
        
        Parameters: none
        Returns: The current state of the API.
        """
        return self._state

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def reset(self):
        """
        Reset the state of the API to its initial state.

        Parameters: None
        Returns: Nothing
        """

        if ( self._conn ):
            self._conn.close()
        self._state = self.Closed
        self._conn = None
        self._last_http_response = None
        self._last_zfresponse = None
        self._zf_token = None

        self._open_connection()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def zfapi_error(self):
        """
        Get the current Zenfolio API error structure

        Parameters: None
        Returns: The Zenfolio API error
        """
        if ( self._last_zfresponse ):
            return self._last_zfresponse['error']
        else:
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def zfapi_response(self):
        """
        Get the last response from the Zenfolio API
        
        Parameters: None
        Returns: the Zenfolio response object
        """

        return self._last_zfresponse
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def success(self):
        """
        Determine if the last method was successful.
        
        Parameters: None
        Returns: True if the last command was successful, 
                 false otherwise.
        """
        
        # If we've never made a call, then I guess that's successful
        if ( self._last_http_response == None ):
            return 1
        # If the last HTTP response was 2xx, check the response from ZF
        elif (self._last_http_response.status // 100 == 2):
            # No response from ZF will be success
            if ( self._last_zfresponse == None ):
                return 1
            # If no error from ZF, then success
            if ( self._last_zfresponse['error'] == None ):
                return 1

        # If we've made it to here, something failed.
        return 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _make_call(self, method, params):
        """
        INTERNAL: Make the call to the Zenfolio API.

        Parameters:
        method: String containing the method to call
        params: List of parameters to pass
        Returns: Nothing
        """

        # Make sure that the call is appropriate to our current status
        if ( method == "GetChallenge" ):
            if ( self._state != self.Closed ):
                raise ZfAPIException(0, "Close connection first.")
        elif ( method == "Authenticate" ):
            if ( self._state != self.GotChallenge ):
                raise ZfAPIException(0, "Call GetChallenge first.")
        elif ( method == "AuthenticatePlain" ):
            if ( self._state != self.Closed ):
                raise ZfAPIException(0, "Close connection first.")
        else:
            if ( self._state != self.Authenticated ):
                raise ZfAPIException(0, "Authentication required.")
                
        # Create the dictionary that will be passed and convert it to 
        # it's JSON representation
        calldict = {
            'method': method,
            'params': params,
            'id': 1 
            }        
        jsontext = json.dumps(calldict, indent=2)

        # Set the HTTP headers
        headers = {"Content-Type": "application/json",
                   "User-Agent": "PyZFAPI/0.1"}
        if ( self._zf_token ):
            headers['X-Zenfolio-Token'] = self._zf_token
        
        if (self.debug):
            print "Sending:", jsontext

        # Make the call and save the response.
        self._conn.request("POST", self._api_path, jsontext,  headers)
        self._last_http_response = self._conn.getresponse()

        if ( self.debug ):
            print "Response:", self._last_http_response.status, \
                self._last_http_response.reason

        # If the HTTP request was succesful, then save the response
        # from the ZF API.  Otherwise, clear the last response.
        if self._last_http_response.status == 200:
            self._last_zfresponse = json.load(self._last_http_response)
        else:
            self._last_zfresponse = None

        # Print some debugging information, if so inclined.
        if ( self.debug ):
            print "Received:", json.dumps(self._last_zfresponse, indent=2);
            
        # Close the connection.
        self._conn.close()
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetChallenge(self, username = ""):
        """
        Get the challenge (password salt and challenge word).

        Parameters
        username: Name to log in as (defaults to null,
                  which means use the name stored in the class)

        Returns: zero on failure, nonzero otherwise.
        """

        if ( self.debug ):
            print(">>>>>> GetChallenge (", username, ")")

        if username != "" :
            self._username = username
        if self._username == "":
            raise ZfAPIException(0, "Undefined username")
        
        self._make_call("GetChallenge", [self._username])

        if ( self.success() ):
            self._state = self.GotChallenge
        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def Authenticate(self, password):
        """
        Authenticate using previously retreived challenge information.

        Parameters
        password: password to use to authenticate

        Returns: zero on failure, nonzero otherwise.
        """

        if ( self.debug ):
            print(">>>>>> Authenticate (<...shhh...>)")

        if ( self._state == self.Closed ):
            raise ZfAPIException(0, "No challenge accepted.")
        elif ( self._state == self.Authenticated ):
            raise ZfAPIException(0, "Already authenticated.")

        # Extract the password salt from the response.
        pwsalt_list = self._last_zfresponse['result']['PasswordSalt']
        pwsalt_len= len(pwsalt_list)
        pwsalt_binary = pack('B'*pwsalt_len,
                             *pwsalt_list)
                
        # Extract the challenge from the response.
        challenge_list = self._last_zfresponse['result']['Challenge']
        challenge_len = len(challenge_list)
        challenge_binary = pack('B'*challenge_len, *challenge_list)
        
        # Compute the password hash.  This should be
        # PasswordHash := SHA-256(PasswordSalt, UTF-8(password))
        # according to Zenfolio.  
        pwhash_binary = sha256(pwsalt_binary 
                               + password.encode("utf-8")).digest()
        
        # Now compute the response.  This should be:
        # Response := SHA-256(Challenge, PasswordHash)
        # according to zenfolio 
        response_binary = sha256(challenge_binary 
                                 + pwhash_binary).digest()
        response_tuple = unpack('B'*len(response_binary), 
                                response_binary)
        
                # Convert the response into a list.
        response_list = list(response_tuple)
        
        self._make_call("Authenticate", 
                        [challenge_list, response_list]);

        if ( self.success() ):
            self._state = self.Authenticated
            self._zf_token = self._last_zfresponse['result']
        else:
            self._state = self.Closed # Need to restart if failure.
            self._zf_token = None

        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AuthenticatePlain(self, password, username=""):
        """
        Authenticate using plain text.

        Parameters: 
        username: login name of the user.  Defaults to empty string, which
                  means use the name stored in the API.
        password: plain text password for the user
        
        Returns: zero on failure, nonzero otherwise.
        """

        if ( self.debug ):
            print(">>>>>> AuthenticatePlain( <...shhh...> ,", username, ")")

        if username != "" :
            self._username = username
        if self._username == "":
            raise ZfAPIException(0, "Undefined username")
                
        if ( self._state == self.Authenticated ):
            raise ZfAPIException(0, "Already authenticated.")
        
        self._make_call("AuthenticatePlain", [self._username, password])

        if ( self.success() ):
            self._state = self.Authenticated
            self._zf_token = self._last_zfresponse['result']
        else:
            self._state = self.Closed
            self._zf_token = None

        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def LoadGroupHierarchy(self, username = ""):
        """
        Load the complete group hierarchy.

        Parameters:
        username: Login name of the user for which to load the hierarchy.
                  Defaults to the null string, which means used the saved
                  username.

        Returns:  zero on failure, nonzero otherwise.
        """
        
        if ( self.debug ):
            print ">>>>>> LoadGroupHierarchy(", username, ")"

        if username != "" :
            self._username = username
        if self._username == "":
            raise ZfAPIException(0, "Undefined username")

        self._make_call("LoadGroupHierarchy", [self._username])
        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def LoadPhotoSet(self, photoset_id, information_level, include_photos):
        """
        Get a snapshot of a photo set (gallery or collection)
        
        Parameters:
        photoset_id: ID of the photoset to load
        information_level: Level of information to return.  May be
                           "Level1", "Level2", or "Full".
        include_photos: True to include photo information.  False otherwise.

        Returns: A photoset shapshot in the response.
        """

        if ( self.debug ):
            print ">>>>>> LoadPhotoSet(", photoset_id, ",", \
                information_level, ",", include_photos, ")"

        # Check the parameters
        if ( photoset_id == None or photoset_id == ""
             or information_level == None or information_level == ""
             or include_photos == None or include_photos == "" ):
            return 0

        self._make_call("LoadPhotoSet", 
                        [photoset_id, information_level, include_photos])

        if ( self.success() ):
            return self._last_zfresponse['result']
        else:
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UploadPhotoToURL(self, filepath, upload_path):
        """
        Upload an image file to a valid upload URL

        Parameters:
        filepath: name of file to upload
        upload_path: Zenfolio URL to upload to

        Returns: zero on failure, nonzero otherwise
        """
        
        if ( self.debug ):
            print ">>>>>> UploadPhotoToURL(", \
                filepath, ",", \
                upload_path, \
                ")"

        # Check the parameters
        if ( filepath == None or filepath == "" or 
             upload_path == None or upload_path == "" ):
            return 0

        # Set the HTTP headers
        headers = {"User-Agent": "PyZFAPI/0.1",
                   "Content-Type": "image/jpeg"}
        if ( self._zf_token ):
            headers['X-Zenfolio-Token'] = self._zf_token

        # Open the file
        file = open(filepath, 'r')

        # Get the modification date of the file
        fstats = os.stat(filepath)
        mod_time = time.strftime("%a, %d %b %Y %H:%M:%S %z", 
                                     time.gmtime(fstats.st_mtime))

        # Encode the file name and modification date into a query string
        filename = os.path.basename(filepath)
        upload_query = urlencode({"filename": filename,
                                  "modified": mod_time})
        
        # Create the upload URL (path+query)
        upload_url = upload_path + "?" + upload_query
        if (self.debug):
            print "Sending ", filename , "to", upload_url

        # Make the call and save the response.
        self._conn.request("POST", upload_url, file,  headers)
        file.close()
        self._last_http_response = self._conn.getresponse()

        if ( self.debug ):
            print "Response:", self._last_http_response.status, 
            self._last_http_response.reason

        self._last_zfresponse = None
        self._conn.close()
        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CreatePhotoSet(self, group_id, type, psu):
        """
        Create a Photo set (gallery or collection).
        
        Parameters:

        group_id: identifier of the photoset group in which to create
            the photoset.
        type: photoset type, either "Gallery" or "Collection"
        psu: PhotoSetUpdater applied immediately after the
            photoset is created
        """

        if ( self.debug ):
            print ">>>>>> CreatePhotoSet(", group_id, ",", type, ",", psu, ")"
            
        if ( group_id == None or group_id == "" or
             type == None or type == "" or
             psu == None ):
            return None

        updater = {}
        if ( psu.Title != None):
            updater['Title'] = psu.Title
        if ( psu.Caption != None):
            updater['Caption'] = psu.Caption
        if ( psu.Keywords != None):
            updater['Keywords'] = psu.Keywords
        if ( psu.Categories != None):
            updater['Categories'] = psu.Categories
        if ( psu.CustomReference != None):
            updater['CustomReference'] = psu.CustomReference
            
        self._make_call("CreatePhotoSet", [group_id, type, updater])
        
        if ( self.success() ):
            return self._last_zfresponse['result']
        else:
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CreateGroup(self, parent_id, gu):
        """
        Create a Group
        
        Parameters:
        parent_id: Identifier of the group in which to create the
            photoset.
        gu: GroupUpdater applied immediately after the group
            is created
        """

        if ( self.debug ):
            print ">>>>>> CreateGroup(", parent_id, ",", gu, ")"
            
        if ( parent_id == None or parent_id == "" or
             gu == None ):
            return 0
        
        updater = {}
        if ( gu.Title != None ):
            updater['Title'] = gu.Title
        if ( gu.Caption != None ):
            updater['Caption'] = gu.Caption
        if ( gu.CustomReference != None ):
            updater['CustomReference'] = gu.CustomReference

        self._make_call("CreateGroup", [parent_id, updater])
        
        if ( self.success() ):
            return self._last_zfresponse['result']
        else:
            return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DeletePhoto(self, photo_id):
        """
        Delete a photo
        
        Parameters:
        photo_id: Identifier of the photo to delete.

        Returns:
        True on success, false otherwise
        """

        if ( self.debug ):
            print ">>>>>> DeletePhoto(", photo_id, ",", gu, ")"
            
        if ( photo_id == None or photo_id == "" ):
            return 0
        
        self._make_call("DeletePhoto", [photo_id])
        
        return self.success()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class PhotoSetUpdater():
        Title = None
        Caption = None
        Keywords = []
        Categories = []
        CustomReference = None

        def __init__(self, title=None, caption=None, 
                     keywords=[], categories=[],
                     custom_reference=None):
            self.Title = title
            self.Caption = caption
            self.Keywords = keywords
            self.Categories = categories
            self.CustomReference = custom_reference
        #END def
    #END class
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class GroupUpdater():
        Title = None
        Caption = None
        CustomReference = None

        def __init__(self, title=None, caption=None, 
                     custom_reference=None):
            self.Title = title
            self.Caption = caption
            self.CustomReference = custom_reference
        #END def
    #END class
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class ZfAPIException(Exception):
    """
    Handle problems with the API

    Attributes:
        error: Error information from the Zenfolio API return
        msg:   Descriptive message
    """

    def __init__(self, error, msg):
        self.error = error
        self.msg = msg
