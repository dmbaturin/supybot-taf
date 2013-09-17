from pytaf import *

class DecoderCompact(Decoder):
    def decode_taf(self):
        result = ""

        result += self._decode_header(self._taf.get_header()) + "\n"

        for group in self._taf.get_groups():
            group_result = []

            if group["header"]:
                result += self._decode_group_header(group["header"])

            if group["wind"]:
                group_result.append( "Wind %s" % self._decode_wind(group["wind"]) )

            if group["visibility"]:
                group_result.append( "Visibility %s" % self._decode_visibility(group["visibility"]) )

            if group["clouds"]:
                group_result.append( "Clouds %s" % self._decode_clouds(group["clouds"]) )

            if group["weather"]:
                group_result.append( "%s" % self._decode_weather(group["weather"]) )

            if group["windshear"]:
                group_result.append( "Windshear %s" % self._decode_windshear(group["windshear"]) )

            result += "; ".join(group_result) + "\n"

        if self._taf.get_maintenance():
            result += self._decode_maintenance(self._taf.get_maintenance())

        result += "\n"

        return(result)
