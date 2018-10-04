#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
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

def parse_launch_feedback(prod):
    with open("%s.log" % prod) as ftmp:
        for ligne in ftmp.readlines():
            if ligne.find("statusLocation") > 0:
                status_url = ligne.split("statusLocation")[1].split('"')[1]
                wpsId = status_url.split("pywps-")[1].split(".xml")[0]
    return wpsId
###########################################################################


def parse_status(prod):
    finished = False
    download_url = None
    with open("%s.stat" % prod) as ftmp:
        for ligne in ftmp.readlines():
            if ligne.find("FINISHED") > 0:
                finished = True
            if ligne.find("zip")>=0 and finished is True:
                print ligne
                download_url = ligne.split('"')[1]
                 
    return finished, download_url


# ===================== MAIN
# ==================
# parse command line
# ==================
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print('      ' + sys.argv[0] + ' [options]')
    print("     Aide : ", prog, " --help")
    print("        ou : ", prog, " -h")
    print("example : python %s -p prod_list.txt -a peps.txt -w /mnt/data/MAJA_PEPS" % sys.argv[0]) 

    sys.exit(-1)
else:
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)

    parser.add_option("-p", "--prod_list", dest="prod_list", action="store", type="string",
                      help="file which contains the list of products to download", default=None)
    parser.add_option("-w", "--write_dir", dest="write_dir", action="store", type="string",
                      help="Path where the products should be downloaded", default='.')
    parser.add_option("-a", "--auth", dest="auth", action="store", type="string",
                      help="Peps account and password file")


    (options, args) = parser.parse_args()
    parser.check_required("-p")
    parser.check_required("-a")




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
    
# ====================
# read product list
#=====================

try:
    with open(options.prod_list) as f:
        lignes=f.readlines()
except IOError:
    print("error with product list file")
    sys.exit(-2)

prod_list=[]
for ligne in lignes:
    prod_list.append(ligne.strip())

print prod_list
# check processing completion and download
for prod in prod_list:
    # get status file
    wpsId = parse_launch_feedback(prod)
    print wpsId
    get_status = 'curl -o %s.stat -k -u  "%s:%s" "https://peps.cnes.fr/resto/wps?service=WPS&request=execute&version=1.0.0&identifier=PROCESSING_STATUS&datainputs=\[wps_id=%s\]"' % (prod, email, passwd, wpsId)
    print(get_status)
    os.system(get_status)

    # Check status 
    (finished, download_url) = parse_status(prod)
    if finished is True:
        get_product = 'curl -o %s.tmp -k -u  "%s:%s" "%s"' % (prod, email, passwd, download_url)
        print get_product
        os.system(get_product)
        os.rename("%s.tmp"% prod, "%s/%s.zip" % (options.write_dir, prod))
        print("\n #### completed download of %s/%s.zip #### \n" % (options.write_dir, prod))
    else:
        print("\n #### processing of %s not completed #### \n" % prod)


