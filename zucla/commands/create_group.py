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

from zucla.zfcli import ZfCLI
import argparse
from os.path import basename, dirname

class CreateGroup(ZfCLI):
    
    def __init__(self):
        ZfCLI.__init__(self, "create-group")
        
        self._parser.add_argument("-p", "--parents", action="store_true",
                                  help="Create parent groups as needed.",
                                  required=False)
        self._parser.add_argument("-c", "--caption", action="store",
                                 help="Caption to add to the group.")
        self._parser.add_argument("-f","--friendly-url",
                                  "--url","--access-code", 
                                 action="store", dest="url",
                                 help="Friendly URL/Access Code for the group.")
        self._parser.add_argument("-a", "--auto-url", \
                                  action="store_true",
                                  help="Automatically create a friendly " + \
                                     "URL from the group path.  The " + \
                                     "last entry in the group " + \
                                     "path will be converted to lower case, " +\
                                     "and spaces replaced with dashes.")
        self._parser.add_argument("group_path", action="store",
                                  help="Destination group to create, " + \
                                      "specified as a slash(\"/\")-"+ \
                                      "delimited path. For example: " + \
                                      "\"/All Photographs/Soccer/Earthquakes\".")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def run(self):
        self.parse_args()
        
        if ( self.the_args.parents == True ):
            print "Sorry, -p/--parents not implemented yet."
            exit()

        if ( self.get_password() ):

            group_title = basename(self.the_args.group_path)
            parent_path = dirname(self.the_args.group_path)

            if ( self.the_args.url == None ):
                if ( self.the_args.auto_url ):
                    url = group_title.lower().replace(" ", "-")
                else:
                    url = None
            else:
                url = self.the_args.url

            print "Creating group \"" + group_title + "\" "
            print "  in group \"" + parent_path + "\""
            if ( self.the_args.caption != None ):
                print "  with caption \"" + self.the_args.caption + "\""
            if ( url != None ):
                print "  with access code/url \"" + url + "\""

            try:
                rv =self.create_group(group_path = parent_path, 
                                          title = group_title,
                                          caption = self.the_args.caption,
                                          custom_reference=url)
                api_response = self.zfapi_response()

                if ( rv ):
                    print "Access URL is", api_response['result']['PageUrl']
                else:
                    print "Error:", api_response['error']['message']
    
            except ZfLibException as e:
                print
                print e.msg
