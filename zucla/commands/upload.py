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
from zucla.zfapi import ZfAPIException
from zucla.zflib import ZfLibException

import argparse
from os.path import basename, dirname
import sys

class Upload(ZfCLI):

    def __init__(self):
        ZfCLI.__init__(self, "upload")
        self._parser.add_argument("-c", "--create", action="store_true", \
                                  help="Create gallery if it doesn't exist.")
        self._parser.add_argument("-p", "--parents", action="store_true",
                                  help="Create parent groups as needed.",
                                  required=False)
        self._parser.add_argument("images", metavar="file", nargs="+", 
                                  help="Path(s) to image file(s) to upload.")
        self._parser.add_argument("gallery", action="store", \
                                  help="Destination gallery, specified " + \
                                      "as a path delimited with slashes "+ \
                                      "(\"/\"). For example: " + \
                                      "\"/All Photographs/Soccer/Earthquakes\".")
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def run(self):
        self.parse_args()

        if ( self.the_args.parents == True ):
            print "Sorry, -p/--parents not implemented yet."
            exit()

        if ( self.get_password() ):
            
            # If we are supposed to create the gallery . . . 
            if ( self.the_args.create ):
                # And the gallery doesn't exist, then create it.
                if ( self.get_group(self.the_args.gallery) == None ):
                    gallery_title = basename(self.the_args.gallery)
                    parent_path = dirname(self.the_args.gallery)
                    print "Creating gallery \"" + gallery_title + "\" "
                    print "  in group \"" + parent_path + "\""
                    self.create_gallery(parent_path, gallery_title)
                
            num_images = len(self.the_args.images)
            print "Uploading", num_images, "images to \"" + \
                self.the_args.gallery + "\""

            # Upload each image..
            upload_count = 0
            for image in self.the_args.images:
                try:
                    print "{:3d}/{:3d}: {:s}..".format(upload_count+1, 
                                                        num_images, image),
                    sys.stdout.flush()
                    rv = self.upload_to_path(image, self.the_args.gallery)
                    upload_count += 1
                    print "Done." 

                # Handle problems from the library.  Print a message
                # and stop the upload process.
                except (ZfCLIException, ZfLibException, ZfAPIException) as e:
                    print
                    print e.msg
                    break

                # Handle problems loading the file.  Just print a message
                # and move to the next file.
                except IOError as e:
                    print e.strerror
            # End for
            print upload_count, "images uploaded."
