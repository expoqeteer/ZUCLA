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
from os.path import basename, dirname

class CreateGallery(ZfCLI):

    def __init__(self):
        ZfCLI.__init__(self, "create-gallery")
        
        self._parser.add_argument("-p", "--parents", action="store_true",
                            help="Create parent groups as needed.",
                            required=False)
        self._parser.add_argument("-c", "--caption", action="store",
                            help="Caption to add to the newly created gallery.")
        self._parser.add_argument("-k", "--keyword", "--keywords", \
                            action="append", dest="keywords", \
                            help="Keyword to be associated with the gallery. "+\
                                "May be specified multiple times.")
        self._parser.add_argument("-g", "--category", "--categories", \
                            action="append",dest="categories", \
                            help="Category to be associated with the gallery."+\
                                " May be specified multiple times.")
        self._parser.add_argument("-f", "--friendly-url", "--url", \
                                 "--access-code", \
                                 action="store", dest="url", \
                                 help="Friendly URL/Access Code to " + \
                                     "associate with the gallery.")
        self._parser.add_argument("-a", "--auto-url", \
                                 action="store_true",
                                 help="Automatically create a friendly URL " + \
                                     "from the gallery path.  The " + \
                                     "last two entries in the gallery " + \
                                     "path will be converted to lower case, " +\
                                     "and spaces replaced with dashes.")
        self._parser.add_argument("gallery_path", action="store", \
                            help="Destination gallery to create, specified " + \
                                "as a path delimited with slashes " + \
                                "(\"/\") For example: " + \
                                "\"/All Photographs/Soccer/Earthquakes\".")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def run(self):
        self.parse_args()

        if ( self.the_args.parents == True ):
            print "Sorry, -p/--parents not implemented yet."
            exit()

        if ( self.the_args.categories != None ):
            print "Sorry, categories have not been implemented yet."
            exit()

        if ( self.get_password() ):
            gallery_title = basename(self.the_args.gallery_path)
            parent_path = dirname(self.the_args.gallery_path)

            if ( self.the_args.url == None ):
                if ( self.the_args.auto_url ):
                    url = basename(parent_path).lower().replace(" ", "-") + \
                        "_" + \
                        gallery_title.lower().replace(" ", "-") 
                else:
                    url = None
            else:
                url = self.the_args.url

            print "Creating gallery \"" + gallery_title + "\" "
            print "  in group \"" + parent_path + "\""
            if ( self.the_args.caption != None ):
                print "  with caption \"" + self.the_args.caption + "\""
            if ( url != None ):
                print "  with access code/url \"" + url + "\""
            if ( self.the_args.keywords != None ):
                print "  with keywords", self.the_args.keywords

            try:
                rv =  self.create_gallery(group_path = parent_path, 
                                              title = gallery_title,
                                              caption = self.the_args.caption,
                                              keywords = self.the_args.keywords,
                                              categories = \
                                                  self.the_args.categories,
                                              custom_reference = url)
                api_response = self.zfapi_response()
                if ( rv ):
                    print "Access URL is", api_response['result']['PageUrl']
                else:
                    print "Error:", api_response['error']['message']
    
            except (ZfCLIException, ZfLibException) as e:
                print
                print e.msg
