###
# Copyright (c) 2013, Daniil Baturin
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('TAF')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

import re
import urllib2

TAF_URL="http://weather.noaa.gov/cgi-bin/mgettaf.pl?cccc=%s"

class TAF(callbacks.Plugin):
    """Displays TAF information for specified ICAO airport code."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TAF, self)
        self.__parent.__init__(irc)

    def taf(self, irc, msg, args, station):
        """<ICAO airport code>

           Display raw TAF information for <ICAO airport code>
        """

        regex = re.compile("^[a-zA-Z]{4}$")
        if not regex.match(station):
            irc.reply(station + " can't be a valid ICAO code")
            return 1

        try:
            station = station.upper()
            url = TAF_URL % station
            urllib2.install_opener(
                    urllib2.build_opener(urllib2.ProxyHandler, urllib2.HTTPHandler))
            request = urllib2.urlopen(url)
            report = request.read()
        except Exception, e:
            irc.reply("Could not fetch report for " + station + ". Make sure your code is correct and try again later.")
            return 1

        re_nf = re.compile("No TAF from")
        nf = re_nf.search(report)
        if nf:
            irc.reply("No TAF data from " + station.upper())
            return 1

        regex = re.compile("<pre>([^<]*)</pre>")
        match = regex.search(report)
        if match:
            report = match.group(1)
        else:
            irc.reply("Parse error")
            return 1

        report = re.sub(r'TAF\s+', 'TAF ', report)
        report = re.sub(r'\n', ' ', report)
        report = re.sub(r'\s{2,}', '; ', report)
        irc.reply(report)

    taf = wrap(taf, ["something"])


Class = TAF


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
