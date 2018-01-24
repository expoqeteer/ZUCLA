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

from zucla.zflib import ZfLib, ZfLibException
from getpass import getpass
import argparse

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class ZfCLI(ZfLib):
    """ 
    The base class for all commands.
    """

    _parser = None
    the_args = None

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, description):
        """
        Initialize the class.
        """

        # Define the arguments common to all commands
        self._parser = argparse.ArgumentParser(description)
        self._parser.add_argument("-u", "--user", action="store",
                                  help="Zenfolio login name.",
                                  required=True);
        self._parser.add_argument("--password", action="store",
                                  help="Password for Zenfolio user.",
                                  required=False)
        self._parser.add_argument("--nossl", action="store_false",
                                  dest='ssl',
                                  help="Disable SSL (default is SSL).",
                                  required=False)
        self._parser.add_argument("--debug", action="store_true",
                                  help="Show debugging information.",
                                  required=False)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def parse_args(self):

        # Parse the arguments.
        self.the_args = self._parser.parse_args()

        # Create the Zenfolio Library object
        ZfLib.__init__(self, debug=self.the_args.debug,
                       username=self.the_args.user,
                       ssl=self.the_args.ssl)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_password(self):
        if ( self.the_args.password ):
            passwd = self.the_args.password
        else:
            passwd = getpass()

        logged_in = 0
        retries = 3
        while (not logged_in and retries > 0 ):
            rv = self.login(passwd, self.the_args.user)
            if ( rv == 0 ):
                print "Login failure.  Please try again."
                passwd = getpass()
                retries -= 1
            logged_in = rv

        if ( not logged_in ):
            print "Login failure."
            
        return logged_in

class ZfCLIException(ZfLibException):
    """                                                                        
    Handle problems with the library 

    Attributes:
    function: function name where the exception was raised.
    msg: Descriptive message
    """

    def __init__(self, function, msg):
        ZfLibException.__init__(self, function, msg)
