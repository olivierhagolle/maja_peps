#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Submits a L2A processing with MAJA to PEPS.
- Products are selected through a catalog request.
  - use peps_maja_request.py -h to see the available options
- If more than 10 products are retrieved by the catalog request a confirmation is necessary.
- Before starting production, please use -n option to check the products retrieved
"""
import json
import time
import os
import os.path
import optparse
import sys
from datetime import date

###########################################################################

class OptionParser (optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

        # Assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)

###########################################################################

def parse_catalog(search_json_file):
    """ parses the results of catalog request"""
    # Filter catalog result
    with open(search_json_file) as data_file:
        data = json.load(data_file)

    if 'ErrorCode' in data:
        print(data['ErrorMessage'])
        sys.exit(-2)

    # Sort data
    download_dict = {}
    storage_dict = {}
    size_dict = {}
    if len(data["features"]) > 0:
        for i in range(len(data["features"])):
            prod = data["features"][i]["properties"]["productIdentifier"]
            print(prod, data["features"][i]["properties"]["storage"]["mode"])
            feature_id = data["features"][i]["id"]
            try:
                storage = data["features"][i]["properties"]["storage"]["mode"]
                platform = data["features"][i]["properties"]["platform"]
                resourceSize = data["features"][i]["properties"]["resourceSize"]
                # recup du numero d'orbite
                orbitN = data["features"][i]["properties"]["orbitNumber"]
                if platform == 'S1A':
                    # calcul de l'orbite relative pour Sentinel 1A
                    relativeOrbit = ((orbitN - 73) % 175) + 1
                elif platform == 'S1B':
                    # calcul de l'orbite relative pour Sentinel 1B
                    relativeOrbit = ((orbitN - 27) % 175) + 1

 
                if options.orbit is not None:
                    if prod.find("_R%03d" % options.orbit) > 0:
                        download_dict[prod] = feature_id
                        storage_dict[prod] = storage
                        size_dict[prod] = resourceSize
 
                else:
                    download_dict[prod] = feature_id
                    storage_dict[prod] = storage
                    size_dict[prod] = resourceSize
            except:
                pass
    else:
        print(">>> no product corresponds to selection criteria")
        sys.exit(-1)

    return(prod, download_dict, storage_dict, size_dict)


# ===================== MAIN
# ==================
# parse command line
# ==================
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print('      ' + sys.argv[0] + ' [options]')
    print("     Aide : ", prog, " --help")
    print("        ou : ", prog, " -h")
    print("example 1 : python %s -l Toulouse -a peps.txt -d 2016-12-06 -f 2017-02-01 -c S2ST" % sys.argv[0])
    print("example 2 : python %s --lon 1 --lat 44 -a peps.txt -d 2016-12-06 -f 2017-02-01 -c S2ST" % sys.argv[0])
    print("example 3 : python %s --lonmin 1 --lonmax 2 --latmin 43 --latmax 44 -a peps.txt -d 2016-12-06 -f 2017-02-01-c S2" % sys.argv[0])
    print("example 4 : python %s -t 31TFJ -a peps.txt -d 2016-12-06 -f 2017-02-01 -c S2ST" % sys.argv[0]) 
    sys.exit(-1)
else:
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)

    parser.add_option("-l", "--location", dest="location", action="store", type="string",
                      help="town name (pick one which is not too frequent to avoid confusions)", default=None)
    parser.add_option("-a", "--auth", dest="auth", action="store", type="string",
                      help="Peps account and password file")
    parser.add_option("-w", "--write_dir", dest="write_dir", action="store", type="string",
                      help="Path where the products should be downloaded", default='.')
    parser.add_option("-n", "--no_download", dest="no_download", action="store_true",
                      help="Do not download products, just print curl command", default=False)
    parser.add_option("-d", "--start_date", dest="start_date", action="store", type="string",
                      help="start date, fmt('2015-12-22')", default=None)
    parser.add_option("-t", "--tile", dest="tile", action="store", type="string",
                      help="Sentinel-2 tile number", default=None)
    parser.add_option("--lat", dest="lat", action="store", type="float",
                      help="latitude in decimal degrees", default=None)
    parser.add_option("--lon", dest="lon", action="store", type="float",
                      help="longitude in decimal degrees", default=None)
    parser.add_option("--latmin", dest="latmin", action="store", type="float",
                      help="min latitude in decimal degrees", default=None)
    parser.add_option("--latmax", dest="latmax", action="store", type="float",
                      help="max latitude in decimal degrees", default=None)
    parser.add_option("--lonmin", dest="lonmin", action="store", type="float",
                      help="min longitude in decimal degrees", default=None)
    parser.add_option("--lonmax", dest="lonmax", action="store", type="float",
                      help="max longitude in decimal degrees", default=None)
    parser.add_option("-o", "--orbit", dest="orbit", action="store", type="int",
                      help="Orbit Path number", default=None)
    parser.add_option("-f", "--end_date", dest="end_date", action="store", type="string",
                      help="end date, fmt('2015-12-23')", default='9999-01-01')
    parser.add_option("-p", "--prod_list", dest="prod_list", action="store", type="string",
                      help="file which contains the list of products to download", default=None)

    parser.add_option("--json", dest="search_json_file", action="store", type="string",
                      help="Output search JSON filename", default=None)
    parser.add_option("--windows", dest="windows", action="store_true",
                      help="For windows usage", default=False)

    (options, args) = parser.parse_args()
    parser.check_required("-a")
    parser.check_required("-p")
    
if options.search_json_file is None or options.search_json_file == "":
    options.search_json_file = 'search.json'

#determine location request
if options.tile is None:
    if options.location is None:
        if options.lat is None or options.lon is None:
            if (options.latmin is None) or (options.lonmin is None) or (options.latmax is None) or (options.lonmax is None):
                print("provide at least a point or rectangle")
                sys.exit(-1)
            else:
                geom = 'rectangle'
        else:
            if (options.latmin is None) and (options.lonmin is None) and (options.latmax is None) and (options.lonmax is None):
                geom = 'point'
            else:
                print("please choose between point and rectangle, but not both")
                sys.exit(-1)

    else:
        if (options.latmin is None) and (options.lonmin is None) and (options.latmax is None) and (options.lonmax is None) and (options.lat is None) or (options.lon is None):
            geom = 'location'
        else:
            print("please choose location and coordinates, but not both")
            sys.exit(-1)

# geometric parameters of catalog request
if options.tile is not None:
    if options.tile.startswith('T') and len(options.tile)==6:
        tileid = options.tile[1:6]
    elif len(options.tile)==5:
        tileid = options.tile[0:5]
    else:
        print("tile name is ill-formated : 31TCJ or T31TCJ are allowed")
        sys.exit(-4)
    query_geom="tileid=%s"%(tileid)
elif geom == 'point':
    query_geom = 'lat=%f\&lon=%f' % (options.lat, options.lon)
elif geom == 'rectangle':
    query_geom = 'box={lonmin},{latmin},{lonmax},{latmax}'.format(
        latmin=options.latmin, latmax=options.latmax, lonmin=options.lonmin, lonmax=options.lonmax)
elif geom == 'location':
    query_geom = "q=%s" % options.location

# date parameters of catalog request
if options.start_date is not None:
    start_date = options.start_date
    if options.end_date is not None:
        end_date = options.end_date
    else:
        end_date = date.today().isoformat()



# ====================
# read authentification file
# ====================
try:
    f = open(options.auth)
    (email, passwd) = f.readline().split(' ')
    if passwd.endswith('\n'):
        passwd = passwd[:-1]
    f.close()
except:
    print("error with password file")
    sys.exit(-2)


if os.path.exists(options.search_json_file):
    os.remove(options.search_json_file)


# ====================
# search in catalog
# ====================

search_catalog = 'curl -k -o %s https://peps.cnes.fr/resto/api/collections/S2ST/search.json?%s\&startDate=%s\&completionDate=%s\&maxRecords=500\&productType=S2MSI1C' % (options.search_json_file, query_geom, start_date, end_date)

if options.windows:
    search_catalog = search_catalog.replace('\&', '^&')

print(search_catalog)
os.system(search_catalog)
time.sleep(1)

prod, download_dict, storage_dict, size_dict = parse_catalog(options.search_json_file)

# =====================
# Start Maja processing
# =====================



if len(download_dict) == 0:
    print("No product matches the criteria")
    sys.exit(-1)

print("\nlist of products retrieved by catalog request")
for i,prod in enumerate(list(download_dict.keys())):
    print(i,prod)


nb_prod = len(download_dict)
confirm="yes"
if nb_prod >= 10:
    confirm = raw_input("\n## You are about to ask for production of %s products, please confirm (yes/no)\n" % nb_prod)

if confirm == "yes":
    if options.write_dir is None:
        options.write_dir = os.getcwd()

    with open(options.prod_list,"w") as f_out:
        for prod in list(download_dict.keys()):
            f_out.write("%s\n" % prod)            
            if (not(options.no_download)):
                start_maja = 'curl -o %s.log -k -u "%s:%s" "https://peps.cnes.fr/resto/wps?service=WPS&request=execute&version=1.0.0&identifier=MAJA&datainputs=product=%s&storeExecuteResponse=true&status=true&title=Maja-Process"' % (prod, email, passwd, prod)
                print (start_maja)
                os.system(start_maja)


