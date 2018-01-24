#    Utliities that extend the Zenfolio API 
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
###############################################################################
#
#    ZUCLA uses the public ZenfolioAPI documented at
#    http://www.zenfolio.com/zf/tools/api.aspx.  ZUCLA and Zenfolio are
#    not affiliated and Zenfiolio does not endorse the use of ZUCLA to 
#    access the Zenfiolo service.
#
###############################################################################
#
# Function list:
#
# _find_dlement (INTERNAL):             Find an element in the hierarchy
# _get_element (INTERNAL):              Return an element from the hierarchy
# login:                                Log in to Zenfolio
# group_hierarchy:                      Return the group hierarchy
# retrive_group_hierarchy:              Get group hierarchy from Zenfolio
# get_group:                            Find a group from a path
# get_photoset:                         Find a photoset from a path
# get_photo:                            Find a photo in a photoset
# delete_photo:                         Delete a photo from a photoset
# get_upload_url:                       Find the url to upload to from a path
# upload_to_path:                       Upload a file to a gallery path
# create_gallery:                       Create a gallery in a path
# create_group:                         Create a group in a path

from zucla.zfapi import ZfAPI, ZfAPIException
import re

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class ZfLib(ZfAPI):
    
    # Log in methods
    (LoginChallengeResponse, LoginPlain) = range(0,2)
    
    _group_hierarchy = None

    def __init__(self,
                 ssl = 1,
                 debug = 0,
                 username = ""):
        """
        Initialize the class.

        Parameters:
        ssl:      zero - use HTTP (non SSL) connection; 
                  nonzero - use SSL. Defaults is SSL.
        debug:    zero - don't emit debug information; 
                  nonzero - be verbose. Default is no debug.
        username: Login name of the user. Defaults to "" 
        """

        ZfAPI.__init__(self, ssl=ssl, debug=debug, username=username)
        self._group_hierarchy = None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _find_element(self, path, elements, etype="Any"):
        """
        INTERNAL - Find an element of the given type from an array
        representing a path to the element.
        
        Parameters:
        path: Array containing a path to the element. (For example,
              ['All Photographs', 'Soccer', 'Earthquakes']
        elements: An "Elements" array in the Group Hierarchy
        etype: Type of element to find or "Any".
        
        Returns: The element corresponding to the path.
        """
        if ( self.debug ):
            print ">>>> ZfLib._find_element(", path, ", [elements], ", \
                ",", etype, ")"

        if ( path == None or path == [] or elements == None):
            return None

        for element in elements:
            if ( element['Title'] == path[0] ):
                # If this is the end of the path, then return the element
                # that we found.
                if ( len(path) == 1 ):
                    if ( self.debug ):
                        print "Found leaf element."
                    if ( element['$type'] == etype or etype == "Any" ):
                        return element
                    else:
                        if ( self.debug ):
                            print "But it was the wrong type."
                
                # Otherwise, find the element specified by the
                # rest of the path.
                else:
                    if ( self.debug ):
                        print "Found branch element."
                    return self._find_element(path[1:], 
                                              element['Elements'],
                                              etype)

        # If we get here, then the search has failed.
        if ( self.debug ):
            print "Couldn't find element."
        return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _get_element(self, path, delimiter="/", etype="Any"):
        """
        INTERNAL - Get an element of the specified type from the group
        hierarchy.
        
        Parameters: 
        path: A string containing the path to convert, or None if the
            path cannot be converted.
        delimiter: A regular expression that delimts each component
            of the path.
        etype: The type of the element to retrieve, or "Any" for the first
            element found.
                    
        Returns: The requested element.
        """ 
        if ( self.debug ):
            print ">>>> ZfLib._get_element(", path, ",", delimiter, \
                ",", etype, ")"

        # Retrieve the Group Hierarchy, if we don't already have it.
        if ( self._group_hierarchy == None ):
            if ( self.retrieve_group_hierarchy() == 0 ):
                return None

        # If the first element is empty, then skip it.
        path_array = re.split(delimiter, path)
        if ( path_array[0] == '' ):
            path_array = path_array[1:]

        # Make sure the root matches.
        if ( self._group_hierarchy['Title'] != path_array[0] ):
            return None

        element = self._find_element(path_array[1:], 
                                     self._group_hierarchy['Elements'],
                                     etype)

        if ( element == None ):
            return None
        else:
            return element
 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def login(self, password="", username="", method=LoginChallengeResponse):
        """
        Log in to Zenfolio.
        
        Parameters:
        username: String containing the username to use. Defaults to a
                  null string which means use the one already in the
                  API.
        password: Password to use.  Defaults to the empty string.
        method:   Method to use (challenge/response or plain text).
                  Default is challenge response.

        Returns: Zero on failure.  Nonzero otherwise.
        """
        if ( self.debug ):
            print ">>>> ZfLib.login ( <...shhh...> , ", username , ",",\
                method, ",", ")"

        if ( method == self.LoginChallengeResponse ):
            if ( self.GetChallenge(username) ):
                return self.Authenticate(password)
            else:
                return 0
        else:
            return self.AuthenticatePlain(password, username)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def group_hierarchy(self):
        """
        Get the group hierarchy for the Zenfolio account

        Parameters: None
        Returns: A dict containing the hierarchy
        """
        if ( self.debug ):
            print ">>>> ZfLib.group_hierarchy ===================="
        return self._group_hierarchy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def retrieve_group_hierarchy(self, username=""):
        """
        Retrieve the group hierarchy from the ZF API and store it here
        
        Parameters: None
        Returns: nonzero on success, zero otherwise
        """
        if ( self.debug ):
            print ">>>> ZfLib.retrieve_group_hierarchy (", username, \
                ")"

        if ( self.LoadGroupHierarchy(username) ):
            self._group_hierarchy = self.zfapi_response()['result']
            return 1
        else:
            self._group_hierarchy = None
            return 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_photoset(self, path, delimiter="/", level="Level1", \
                                  include_photos="False"):
        """
        Retrieve a photoset snapshot.

        Parameters:
        path: A string containing the path to convert, or None if the
            path cannot be converted.
        delimiter: A regular expression that delimts each component
            of the path.
        level: Amount of information to retrieve ("Level1", "Level2" or "Full").
            Defaults to "Level1".
        include_photos: Whether or not to load the photos into the photoset
            shapshot.  Defaults to "False"

        Returns: a PhotoSet object.
        """

        if ( self.debug ):
            print ">>>> ZfLib.get_photoset(", path, ",", delimiter, ",", \
                level, ",", include_photos, ")"

        if ( path == None or path == "" or delimiter == ""):
            return None;

        # Get the element that we need.
        element = self._get_element(path, delimiter, "PhotoSet")

        # If we didn't find it, then fail.
        if ( element == None ):
            return None
        else:
            # Go get it!
            photoset = self.LoadPhotoSet(element['Id'], 
                                             level,
                                             include_photos)
            if ( photoset == None ):
                return None
            else:
                return photoset

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_photo(self, photoset, filename, level="Level1"):
        """
        Retrieve a photo from a photoset.

        Parameters:
        photoset: the photo set from which to retrieve the photo.
        filename: filename of the phot to retrieve.
        level: Amount of information to retrieve ("Level1", "Level2" or "Full").
            Defaults to "Level1".
        include_photos: Whether or not to load the photos into the photoset
            shapshot.  Defaults to "False"

        Returns: a PhotoSet object.
        """

        if ( self.debug ):
            print ">>>> ZfLib.get_photo({photoset} ", filename, ",", \
                level, ")"

        # Check the arguments
        if ( photoset == None or filename == None or filename == "" ):
            return None;

        # No photos in the array.
        if ( photoset['Photos'] == [] ):
            return None

        # Look for the photo filename and return it if we find it.
        for photo in photoset['Photos']:
            if ( photo['FileName'] == filename ):
                return photo

        # If we never find it, then return None
        return None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def delete_photo(self, photoset, filename, level="Level1"):
        """
        Remove a photo from a photoset.

        Parameters:
        photoset: the photo set from which to retrieve the photo.
        filename: filename of the phot to retrieve.

        Returns: True on success, false otherwisel
        """

        if ( self.debug ):
            print ">>>> ZfLib.delete_photo({photoset} ", filename, ")"

        # Check the arguments
        if ( photoset == None or filename == None or filename == "" ):
            return None;

        # No photos in the array.
        if ( photoset['Photos'] == [] ):
            return False

        # Look for the photo filename and return it if we find it.
        for photo in photoset['Photos']:
            if ( photo['FileName'] == filename ):
                return self.DeletePhoto(photo['Id'])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_upload_url(self, path, delimiter="/"):
        """
        Convert a path (delimited by "/") to a Gallery UploadUrl
        
        Parameters: 
        path: A string containing the path to convert, or None if the
            path cannot be converted.
        delimiter: A regular expression that delimts each component
            of the path.
                    
        Returns: A string containing the upload URL, or None on failure.
        """ 
        if ( self.debug ):
            print ">>>> ZfLib.get_upload_url(", path, ",", delimiter,\
                ")"

        element = self._get_element(path, delimiter, "PhotoSet")

        if ( element == None ):
            return None
        else:
            return element['UploadUrl']
 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def upload_to_path(self, image_path, gallery_path):
        """
        Upload an image to the specified gallery
        
        Parameters:
        image_path: The path on the system that specifies the image to upload
        gallery_path: The path to the gallery to which to upload the image
        
        Returns: nonzero on success, zero on failure
        """
        if ( self.debug ):
            print ">>>> ZfLib.upload_to_path(", image_path, ",", \
                gallery_path, ")"

        url = self.get_upload_url(gallery_path)

        # If we found the gallery, then upload to it.
        if ( url ):
            return self.UploadPhotoToURL(image_path, url)
        else:
            raise ZfLibException("upload_to_path", 
                                 "Gallery \"" + gallery_path + "\" not found");

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_group(self, path, delimiter="/"):
        """
        Get the group ID for a path (delimited by "/").
        
        Parameters: 
        path: A string containing the path to convert, or None if the
            path cannot be converted.
        delimiter: A regular expression that delimts each component
            of the path.
                    
        Returns: A string containing the gallery id, or None on failure.
        """ 
        if ( self.debug ):
            print ">>>> ZfLib.get_group(", path, ",", delimiter,\
                ")"

        element = self._get_element(path, delimiter, "Group")

        if ( element == None ):
            return None
        else:
            return element
 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def create_gallery(self, group_path, title, caption='',
                       keywords=[], categories=[], custom_reference=''):
        """ 
        Create a gallery with the given path with the specified attributes:

        Parameters: 
        group_path: The path (delimited by "/") in which to to
            create the new gallery.
        title: the gallery title
        caption: the gallery caption
        keywords: the set of keywords to associate with the gallery
        categories: the set of categories to associate with the gallery
        custom_reference: the friendly URL path for the photoset.  Do not
            include the leading slash any other URL entities.

        Returns: a snapshot of the created photoset.

        ToDo: Handle categories by using GetCategories to get the list
            of categories and then convert the category names into
            numeric codes.
        """
     
        if ( self.debug ):
            print ">>>> ZfLib.create_gallery(", group_path, ",", \
                title, ",", \
                caption, ",", \
                keywords, ",", \
                categories, ",", \
                custom_reference, ",", \
                ")"

        # Get the ID for the group specified by group_path.
        parent_group = self.get_group(group_path)

        # If we found the gallery then create the new gallery
        if ( parent_group ):
            # Create the PhotoSetUpdater, adding only those items which are
            # not None
        
            psu = ZfAPI.PhotoSetUpdater(title, caption, keywords, 
                                        categories, custom_reference)

            # Invalidate the current group hierarchy, which will force
            # an automatic reload if we need it again.
            # TODO: Merge the new PhotoSet into the existing hierarchy.
            self._group_hierarchy = None
            
            return self.CreatePhotoSet(parent_group['Id'], "Gallery", psu)
        else:
            raise ZfLibException("create_gallery", 
                                 "Gallery \"" + group_path + "\" not found");

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def create_group(self, group_path, title, caption='', custom_reference=''):
        """ 
        Create a group with the given path with the specified attributes:

        Parameters: 
        group_path: The path (delimited by "/") in which to to
            create the new group.
        title: the group title
        caption: the group caption
        custom_reference: the friendly URL path for the photoset.  Do not
            include the leading slash any other URL entities.

        Returns: a snapshot of the created photoset.

        ToDo: Handle categories by using GetCategories to get the list
            of categories and then convert the category names into
            numeric codes.
        """
     
        if ( self.debug ):
            print ">>>> ZfLib.create_group(", \
                group_path, ",", \
                title, ",", \
                caption, ",", \
                custom_reference, ",", \
                ")"

        # Get the ID for the group specified by group_path.
        parent_group = self.get_group(group_path)

        # If we found the group then create the new group
        if ( parent_group ):
            # Create the GroupUpdater
            gu = ZfAPI.GroupUpdater(title, caption, custom_reference)


            # Invalidate the current group hierarchy, which will force
            # an automatic reload if we need it again.
            # TODO: Merge the new group into the existing hierarchy.
            self._group_hierarchy = None

            return self.CreateGroup(parent_group['Id'], gu)
        else:
            raise ZfLibException("create_group", 
                                 "Group \"" + group_path + "\" not found");

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class ZfLibException(ZfAPIException):
    """
    Handle problems with the library

    Attributes:
    function: function name where the exception was raised.
    msg: Descriptive message
    """

    def __init__(self, function, msg):
        ZfAPIException.__init__(self, function, msg)
    
