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
import urllib3
import pytaf

TAF_URL="http://weather.noaa.gov/cgi-bin/mgettaf.pl?cccc=%s"

class DecoderCompact(pytaf.Decoder):
    def decode_taf(self):
        result = ""

        result += self._decode_header(self._taf.get_header()) + "\n"

        for group in self._taf.get_groups():
            group_result = []

            if group["header"]:
                result += self._decode_group_header(group["header"])
            if group["wind"]:
                group_result.append( "wind %s" % self._decode_wind(group["wind"]) )
            if group["visibility"]:
                group_result.append( "visibility %s" % self._decode_visibility(group["visibility"]) )
            if group["clouds"]:
                group_result.append( "%s" % self._decode_clouds(group["clouds"]) )
            if group["weather"]:
                group_result.append( "%s" % self._decode_weather(group["weather"]) )
            if group["windshear"]:
                group_result.append( "windshear %s" % self._decode_windshear(group["windshear"]) )
            result += "; ".join(group_result) + "\n"

        if self._taf.get_maintenance():
            result += self._decode_maintenance(self._taf.get_maintenance())

        result += "\n"

        return(result)


class TAFException(Exception):
    def __init__(self, msg):
        self.strerror = msg


class TAF(callbacks.Plugin):
    """Displays TAF information for specified ICAO airport code."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TAF, self)
        self.__parent.__init__(irc)
        self._http = urllib3.PoolManager()

    def _fetch_taf(self, station):
        regex = re.compile("^[a-zA-Z]{4}$")
        if not regex.match(station):
            raise TAFException(station + " can't be a valid ICAO code")

        try:
            station = station.upper()
            url = TAF_URL % station
            reply = self._http.request('GET', url)
            report = reply.data.decode()
        except Exception as e:
            raise TAFException("Could not fetch report for " + station + ". Make sure your code is correct and try again later.")
            return 1

        re_nf = re.compile("No TAF from")
        nf = re_nf.search(report)
        if nf:
            raise TAFException("No TAF data from " + station.upper())

        regex = re.compile("<pre>([^<]*)</pre>")
        match = regex.search(report)
        if match:
            report = match.group(1)
        else:
            raise TAFException("Parse error")

        return(report)


    def taf(self, irc, msg, args, station):
        """<ICAO airport code>

           Display raw TAF information for <ICAO airport code>
        """

        try:
            report = self._fetch_taf(station)
        except TAFException as e:
            irc.reply(e.strerror)
            return(1)

        report = re.sub(r'TAF\s+', 'TAF ', report)
        report = re.sub(r'\n', ' ', report)
        report = re.sub(r'\s{2,}', '; ', report)
        irc.reply(report)

    def itaf(self, irc, msg, args, station):
       """<ICAO airport code>

          Display decoded TAF information for <ICAO airport code>
       """

       try:
            report = self._fetch_taf(station)
       except TAFException as e:
            irc.reply(e.strerror)
            return(1)

       try:       
           parser = pytaf.TAF(report)
           decoder = DecoderCompact(parser)
       except (pytaf.MalformedTAF, pytaf.DecodeError) as e:
           irc.reply("An error had occured, parser says: " + e.strerror)
           return(1)
     
       parsed_report = decoder.decode_taf()
       parsed_report = parsed_report.split('\n')

       for line in parsed_report:
            if line:
                irc.reply(line, to=msg.nick, prefixNick=False,
                          private=True)
       irc.reply("End of message", to=msg.nick, prefixNick=False, private=True)

    itaf = wrap(itaf, ["something"])
    taf = wrap(taf, ["something"])


Class = TAF


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
