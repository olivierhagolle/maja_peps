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

###########################################################################


class OptionParser (optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

        # Assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error("%s option not supplied" % option)


###########################################################################
def parse_launch_feedback(log_prod):
    """ Gets processing Id """
    with open(log_prod) as ftmp:
        for ligne in ftmp.readlines():
            if ligne.find("statusLocation") > 0:
                status_url = ligne.split("statusLocation")[1].split('"')[1]
                wpsId = status_url.split("pywps-")[1].split(".xml")[0]
    return status_url,wpsId
    
###########################################################################
def parse_update(update_prod):
    """ Gets update """
    with open(update_prod) as ftmp:
        for ligne in ftmp.readlines():
            if ligne.find("wps:Reference") > 0:
                json_url = ligne.split("href")[1].split('"')[1]	
    return json_url
        
###########################################################################
def parse_status(stat_prod):
    """ checks if processing is completed """
    status = "computing"
    download_url = None
    L2A_name = None
    percent = 0
    with open(stat_prod) as ftmp:
        for ligne in ftmp.readlines():
            if ligne.find("percentCompleted") > 0:
                percent = int(ligne.split(":")[1].split(",")[0])
            if ligne.find("FINISHED") > 0:
                status = "finished"
            if ligne.find("CANCELED") > 0:
                status = "canceled"
            if ligne.find("zip") >= 0 and status == "finished":
                print ligne
                download_url = ligne.split('"')[1]
                L2A_name = download_url.split('/')[-1]
    return percent, status, download_url, L2A_name


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

    if options.write_dir is None:
        options.write_dir = os.getcwd()


# ====================
# read authentification file
# ====================
try:
    f = open(options.auth)
    (email, passwd) = f.readline().split(' ')
    if passwd.endswith('\n'):
        passwd = passwd[:-1]
    f.close()
except IOError:
    print("error with password file")
    sys.exit(-2)

# ====================
# read product list
# =====================

try:
    with open(options.prod_list) as f:
        lignes = f.readlines()
except IOError:
    print("error with product list file")
    sys.exit(-2)

prod_list = []
for ligne in lignes:
    prod_list.append(ligne.strip())

# check processing completion and download
for prod in prod_list:
    # get status file
    log_prod = os.path.join(options.write_dir, str(prod + '.log'))
    status_url,wpsId = parse_launch_feedback(log_prod)
    print("wpsId: ", wpsId)
    
    #-- Charlotte add
    update_prod = os.path.join(options.write_dir, str('update_' + prod + '.txt'))
    update_status = 'curl -o %s -k -u  "%s:%s" %s' % (
		update_prod, email, passwd, status_url)
    print(update_status)
    os.system(update_status)
    
    json_url = parse_update(update_prod)
    stat_prod = os.path.join(options.write_dir, str(prod + '.stat'))
    get_status = 'curl -o %s -k -u  "%s:%s" %s' % (
		stat_prod, email, passwd, json_url)
    print(get_status)
    os.system(get_status)
    (percent, status, download_url, L2A_name) = parse_status(stat_prod)
    
    #~ stat_prod = os.path.join(options.write_dir, str(prod + '.stat'))
    #~ get_status = 'curl -o %s -k -u  "%s:%s" "https://peps.cnes.fr/resto/wps?service=WPS&request=execute&version=1.0.0&identifier=PROCESSING_STATUS&datainputs=\[wps_id=%s\]"' % (
        #~ stat_prod, email, passwd, wpsId)
    #~ print(get_status)
    #~ os.system(get_status)

    # Check status
    (percent, status, download_url, L2A_name) = parse_status(stat_prod)
    if status == "finished" and not(os.path.exists("%s/%s" % (options.write_dir, L2A_name))):
        get_product = 'curl -o %s.tmp -k -u  "%s:%s" "%s"' % (prod, email, passwd, download_url)
        print get_product
        os.system(get_product)
        os.rename("%s.tmp" % prod, "%s/%s" % (options.write_dir, L2A_name))
        print("\n #### completed download of %s/%s #### \n" % (options.write_dir, L2A_name))
    elif status == "canceled":
        print("\n #### processing was canceled #### ")
        print("can happen outside |lat|<60° for lack of SRTM DEM\n")
    else:
        if os.path.exists("%s/%s" % (options.write_dir, L2A_name)):
            print ("\n #### %s already downloaded #### \n" % prod)
        else:
            print("\n #### processing of %s not completed #### \n" % prod)
            print("percentage processed : %s" % percent)
