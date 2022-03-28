import getopt,sys
import os
import subprocess
from urllib2 import urlopen
import json
import re

# you might need to change this line to locate mtr command
mtr_cmd = "/usr/local/Cellar/mtr/0.95/sbin/mtr"

def usage():
	print "$python process.py -h your_host";

def mtr_report(host, count):
    # returns output as byte string
    outputs = subprocess.check_output([mtr_cmd, '-n', '-r', '-c %s' % (count), host])
    return outputs.decode("utf-8")

# https://ip-api.com/docs/api:json
server_url = "http://ip-api.com/json/%s?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,lat,lon,isp,org,as,asname,query"
def ip_lookup(ipstr):
    # Get the geo information from ip-api.com
    response = urlopen(server_url % ipstr)

    string = response.read().decode('utf-8')
    geos = json.loads(string)
    return geos

def geos_tostring(geos):
    result = ""
    if(geos['status'] == 'success'):    
        if len(geos['org']) > 0:
            result = geos['org'] + "; "
        if len(geos['isp']) > 0:
            result = result + geos['isp'] + "; "
        if len(geos['city']) > 0:
            result = result + geos['city'] + "; "
        if len(geos['regionName']) > 0:
            result = result + geos['regionName'] + "; "
        if len(geos['country']) > 0:
            result = result + geos['country']
    else:
        # print geos
        result = geos['message']
    
    return result

def geos_tohost(index, ipstr, geodesc, geos):
    result = "{\"n\": %s, \"ip\":\"%s\", \"desc\": \"%s\", \"geo\": {\"lat\": %s, \"lng\": %s4}}," % (index, ipstr, geodesc, geos['lat'], geos['lon'])
    return result

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:c:", ["host=", "count="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    host = ""
    mtr_count = 10
    for o, a in opts:
        if o in ("-h", "--host"):
            host = a
        elif o in ("-c", "--count"):
        	mtr_count = a
        else:
            assert False, "unhandled option"
    
    if len(host) == 0:
    	usage()
    	sys.exit(0)

    # show host information
    print "Show traceroute information for host (%s)" %(host)

	# collect traceroute information
    print "Use mtr command to generate traceroute informations, please wait ..."
    outputs = mtr_report(host, mtr_count)
    # print outputs

    # parse geolocation information
    lines = outputs.splitlines()

    print "Parse geolocation from ip-api.com ..."
    hosts = "let hosts = [\n"
    idx = 0
    for index, line in enumerate(lines):
        results = re.findall(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b", line)
        if results:
            ipstr = results[0]
            # print ipstr
            geos = ip_lookup(ipstr)
            # print geos
            geodesc = "%s (%s)" % (ipstr, geos_tostring(geos))
            print line.replace(ipstr, geodesc)

            # generate host 
            hosts += geos_tohost(idx, ipstr, geodesc, geos) + "\n"
            idx += 1    
    hosts += "];\n"

    # write hosts information in "host.js"
    print "Write google maps information to hosts.js ..."
    text_file = open("hosts.js", "w")
    n = text_file.write(hosts)
    text_file.close()

    print "Now we will launch browser to open visual traceroute result ..."
    import webbrowser
    webbrowser.open('file://' + os.path.realpath("google-maps.html"))

if __name__ == "__main__":
    main()
