#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
Checks if a maja processing submitted to PEPS is completed.
If completed, the product is downloaded
"""
import os
import os.path
import optparse
import sys
import requests
import json
import shutil

###########################################################################


class OptionParser (optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

        # Assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)

# ##########################################################################


def downloadFile(url, fileName, email, password):
    r = requests.get(url, auth=(email, passwd), stream=True, verify=False)
    with open(fileName, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return


def getURL(url, fileName, email, passwd):
    req = requests.get(url, auth=(email, passwd), verify=False)
    with open(fileName, "w") as f:
        f.write(req.text.encode('utf-8'))
        if req.status_code == 200:
            print("Request OK")
        else:
            print("Wrong request status {}".format(str(req.status_code)))
            sys.exit(-1)

    return

###########################################################################


def parse_json(json_file, email, passwd, write_dir):
    with open(json_file) as data_file:
        data = json.load(data_file)
    status = data["USER_INFO"]["job_status"]
    # processing finished
    if status == "FINISHED":
        print("finished")
        results = data["USER_INFO"]["results"]
        for urlL2A in results:
            L2AName = urlL2A.split('/')[-1]
            if L2AName.find('NOVALD') >= 0:
                print("%s was too cloudy" % L2AName)
            elif os.path.isfile(os.path.join(write_dir, L2AName)):
                print("skipping {}: already on disk".format(L2AName))
            else:
                print("downloading %s" % L2AName)
                downloadFile(urlL2A, "%s/%s" % (write_dir, L2AName), email, passwd)
        n_unproc = int(data["USER_INFO"]["unprocessed"])
        if n_unproc > 0:
            print("\nWarning: {:d} products have not been processed".format(n_unproc))
            print("For more information, please check {}".format(json_file))
    # processing still on-going
    elif status == "STALLED":
        progress = data["USER_INFO"]["process"]
        print("Processing is not finished yet, please try again later")
        print("It takes usually 25 minutes per image + 1 hour for the first one")
        print("Progress indicates %s, but the percentage is often exagerated" % progress)
    elif status == "PENDING":
        print("Processing is still pending")
        print("CNES HPC center must be busy")
    # processing finished with error
    elif status == "ERROR" or status == "CANCELED":
        urlLog = data["USER_INFO"]["logs"][0]
        message = data["USER_INFO"]["message"]
        finalLog = json_file.replace(".json", ".finalLog")
        print(message)

    return


# ######################### MAIN
# ==================
# parse command line
# ==================
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print('      ' + sys.argv[0] + ' [options]')
    print("     Aide : ", prog, " --help")
    print("        ou : ", prog, " -h")
    print("example : python %s -a peps.txt -g Full_MAJA_31TCJ_51_2019.log -w ./Full_MAJA_31TCJ_51_2019 " %
          sys.argv[0])

    sys.exit(-1)
else:
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)

    parser.add_option("-w", "--write_dir", dest="write_dir", action="store", type="string",
                      help="Path where the products should be downloaded", default='.')
    parser.add_option("-a", "--auth", dest="auth", action="store", type="string",
                      help="Peps account and password file")
    parser.add_option("-l", "--log", dest="logName", action="store", type="string",
                      help="log file name ", default='Full_Maja.log')

    (options, args) = parser.parse_args()
    parser.check_required("-a")

    if not (os.path.exists(options.write_dir)):
        os.mkdir(options.write_dir)
print("---------------------------------------------------------------------------")


# ====================
# read authentification file
# ====================
try:
    f = open(options.auth)
    try:
        (email, passwd) = f.readline().split(' ')
        if passwd.endswith('\n'):
            passwd = passwd[:-1]
        f.close()
    except ValueError:
        print("error with password file content")
        sys.exit(-2)
except IOError:
    print("error with password file")
    sys.exit(-2)

# =======================================
# read log file from full_maja_process.py
# =======================================

try:
    with open(options.logName) as f:
        lignes = f.readlines()
        urlStatus = None
        for ligne in lignes:
            if ligne.startswith("<wps:ExecuteResponse"):
                wpsId = ligne.split("pywps-")[1].split(".xml")[0]
                urlStatus = ligne.split('statusLocation="')[1].split('">')[0]
        if urlStatus is None:
            print("url for production status not found in logName %s" % options.logName)
            sys.exit(-4)
except IOError:
    print("error with logName file provided as input or as default parameter")
    sys.exit(-3)

statusFileName = options.logName.replace('log', 'stat')
getURL(urlStatus, statusFileName, email, passwd)

peps = "http://peps.cnes.fr/resto/wps"

url = "{}?request=execute&service=WPS&version=1.0.0&identifier=PROCESSING_STATUS&datainputs=wps_id={}&status=false&storeExecuteResponse=false".format(
    peps, wpsId)

# Update log files
print("Updating status files: {}".format(url))
req = requests.get(url, auth=(email, passwd))


# get json file from urlStatus
# ====================

try:
    with open(statusFileName) as f:
        lignes = f.readlines()
        urlJSON = None
        for ligne in lignes:
            if ligne.find("<wps:Reference") >= 0:
                urlJSON = ligne.split('href="')[1].split('"')[0]
        if urlJSON is None:
            print("url for json output not found in statusFileName %s" % statusFileName)
            sys.exit(-4)
except IOError:
    print("error with status url found in logName")
    sys.exit(-3)

# get urlJSON:
print("Execution report: {}".format(urlJSON))
JSONFileName = options.logName.replace('log', 'json')
getURL(urlJSON, JSONFileName, email, passwd)


# parse the resul json file, and download products if processing is completed
parse_json(JSONFileName, email, passwd, options.write_dir)
print("---------------------------------------------------------------------------")
