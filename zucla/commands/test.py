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

class test(ZfCLI):

    def __init__(self):
        ZfCLI.__init__(self, "test")
        
        self._parser.add_argument("gallery_path", action="store", \
                            help="Gallery to query, specified " + \
                                "as a path delimited with slashes " + \
                                "(\"/\") For example: " + \
                                "\"/All Photographs/Soccer/Earthquakes\".")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def run(self):
        self.parse_args()

        if ( self.get_password() ):
            print "testing '" + self.the_args.gallery_path + "\""

            try:
                rv =  self.get_photoset(self.the_args.gallery_path);

                api_response = self.zfapi_response()
    
            except (ZfCLIException, ZfLibException) as e:
                print
                print e.msg
