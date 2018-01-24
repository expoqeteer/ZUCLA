#    A class to create a Zenfolio command-line interface
# 
#    For more information, see http://github.com/bryanmason/ZUCLA
#
#    Copyright (c) 2011, Bryan Mason
#
#    Copyright (c) 2011, 2012 Bryan Mason
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

from zucla.zfcli import ZfCLI, ZfCLIException
from zucla.zflib import ZfLibException

import argparse
from os.path import relpath, basename, dirname, getsize
import os.path
import os
import sys
import mimetypes

class Backup(ZfCLI):

    def __init__(self):
        ZfCLI.__init__(self, "backup")
        self._parser.add_argument("local_path", action="store", \
                                   help="Path to back up")
        self._parser.add_argument("group_path", action="store", \
                                   help="Group to back up to, specified " + \
                                   "as a path delimited with slashes " + \
                                   "(\"/\") For example: " + \
                                   "\"/All Photographs/Soccer/Earthquakes\".")

        mimetypes.init()
        self.max_socket_retries = 3

        self._add_files = 0
        self._skip_files = 0
        self._old_files = 0
        self._new_files = 0
        self._new_galleries = 0
        self._new_groups = 0
        self._total_retries = 0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def is_image_file(self, filename):
        """
        Is this an image file?

        Parameters:
        filename: Name of the file to check.

        Returns: True (nonzero) if the file is an image file.  False otherwise.
        """

        if ( os.path.exists(filename) ):
            type, encoding = mimetypes.guess_type(filename)
            if ( type == None ):
                return False
            else:
                if ( "image/" in type ):
                    return True
                else:
                    return False
        else:
            return False

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def print_summary(self):
        """
        Print a summary of everything that has been done.

        Parameters:
            None.

        Returns: Nothing
        """

        print ""
        print "Summary:"
        print "  Created {:5d} new groups".format(self._new_groups)
        print "      and {:5d} new galleries".format(self._new_galleries)
        print "  Skipped {:5d} non-image files".format(self._skip_files)
        print "  Skipped {:5d} old image files".format(self._old_files)
        print "  Added   {:5d} image files".format(self._add_files)
        print "  Updated {:5d} image files".format(self._new_files)
        print "  Retried {:5d} operations".format(self._total_retries)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def print_action(self, action, filename):
        """
        Print a line describing the action to be taken.

        Parameters:
            action: a string describing the action

        Returns: Nothing
        """

        if ( self._cur_file > 99
             and self._cur_file % 100 == 0 ):
            print "   Archiving:", self._local_path
            print "          to:", self._zf_path


        print "{:4s} {:4d}/{:4d}: {:s}".format(action, 
                                               self._cur_file, 
                                               self._num_files, 
                                               filename)
        sys.stdout.flush()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def run(self):
        self.parse_args()

        local_root = self.the_args.local_path
        zf_root = self.the_args.group_path

        if ( self.get_password() ):
            try:

                # Walk the directory structure
                for self._local_path, dirs, files in os.walk(local_root, 
                                                       topdown = True):
                    # Sort the directories for neatness.
                    dirs.sort()

                    # Calculate the path from the one specified on the 
                    # command line to our current position.  Then
                    # Join it to the Zenfolio root path.
                    rpath = relpath(self._local_path, local_root)
                    if ( rpath == "." ):
                        self._zf_path = zf_root
                    else:
                        self._zf_path = os.path.join(zf_root, rpath)

                    print "   Archiving:", self._local_path
                    print "          to:", self._zf_path

                    # If there are directories in this location, then 
                    # find/create a group for this location
                    if ( dirs != [] ):
                        group = self.get_group(self._zf_path)
                        if ( group == None):
                            self._new_groups += 1
                            retries = 0
                            while ( retries < self.max_socket_retries ):
                                try:
                                    print "   New group:", self._zf_path
                                    self.create_group(dirname(self._zf_path),
                                                      basename(self._zf_path))
                                except IOError as e:
                                    # Broken pipe or Connection reset by peer
                                    if ( retries < self.max_socket_retries \
                                         and (e.errno == 32 or e.errno == 104) ):
                                        retries += 1
                                        self._total_retries += 1
                                        print "{:s}!  Retry #{:d} - ".format(e.strerror, retries),
                                        self.reset()
                                        if ( not self.get_password() ):
                                            raise e
                                    # Not something we want to handle
                                    else:
                                        raise e
                                # No exception, break from the while
                                else:
                                    break

                    self._num_files = len(files)
                    self._cur_file = 0
                    photoset = None
                    for f in sorted(files):
                        self._cur_file += 1
                        # If the file is an image file, then find or create
                        # A photoset for it.
                        photo_path = os.path.join(self._local_path, f)
                        if ( self.is_image_file(photo_path) ):
                            if ( photoset == None ):
                                # Find the photoset for this location
                                photoset = \
                                    self.get_photoset(self._zf_path,
                                                      level="Level2",
                                                      include_photos="True")

                                # Create it if it doesn't exist
                                if ( photoset == None ):
                                    self._new_galleries += 1
                                    retries = 0
                                    while ( retries < self.max_socket_retries ):
                                        try:
                                            print " New gallery:", self._zf_path
                                            self.create_gallery(dirname(self._zf_path),
                                                                basename(self._zf_path))
                                        except IOError as e:
                                            # Broken pipe or Connection reset by peer
                                            if ( retries < self.max_socket_retries \
                                                 and (e.errno == 32 or e.errno == 104)):
                                                retries += 1
                                                self._total_retries += 1
                                                print "{:s}!  Retry #{:d} - ".format(e.strerror, retries),
                                                self.reset()
                                                if ( not self.get_password() ):
                                                    raise e
                                            # Not something we want to handle
                                            else:
                                                raise e
                                        # No exception, break from the while
                                        else:
                                            break
                                    photoset = \
                                        self.get_photoset(self._zf_path,
                                                          level="Level2",
                                                          include_photos="True")

                            # If the photo doesn't exist in the photoset,
                            # then upload it.
                            photo = self.get_photo(photoset, f)
                            if ( photo == None ):
                                retries = 0
                                # Retry three times
                                while ( retries < self.max_socket_retries ):
                                    try:
                                        # "Add 123/123:"
                                        self._add_files += 1
                                        self.print_action("Add", f)
                                        self.upload_to_path(photo_path, self._zf_path)
                                    except IOError as e:
                                        # Broken pipe or Connection reset by peer
                                        if ( retries < self.max_socket_retries \
                                             and (e.errno == 32 or e.errno == 104)):
                                            retries += 1
                                            self._total_retries += 1
                                            print "{:s}!  Retry #{:d} - ".format(e.strerror, retries),
                                            self.reset()
                                            if ( not self.get_password() ):
                                                raise e
                                        # Not something we want to catch
                                        else:
                                            raise e
                                    # No error, break from the while
                                    else:
                                        break
                            else:
                                # If the photo exists, but is different, then
                                # update it.
                                if ( getsize(photo_path) != photo['Size'] ):
                                    # " New 123/123:"
                                    self._new_files += 1
                                    self.print_action("New", f)
                                    self.upload_to_path(photo_path, self._zf_path)
                                    self.delete_photo(photoset, f)
                                else:
                                    # " Old 123/123:"
                                    self._old_files += 1
                                    self.print_action("Old", f)

                        # Not an image file
                        else:
                            self._skip_files += 1
                            # "Skip 123/123:"
                            self.print_action("Skip", f)
                # Done
                self.print_summary()

            except (KeyboardInterrupt):
                print ""
                print "Interrupt!"
                self.print_summary()
                                    
            except (ZfCLIException, ZfLibException) as e:
                print
                print e.msg
