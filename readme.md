# peps_maja

peps_maja_process.py is a piece of code to ask [PEPS](https://peps.cnes.fr) to process Sentinel-2 products with MAJA. peps_maja_download.py checks if the processing is completed and eventually downloads the products. PEPS is the French Sentinel collaborative ground segment : https://peps.cnes.fr. PEPS is mirroring all the Sentinel data provided by ESA, and is providing a simplified access.

This code was written thanks to the precious help of one my colleagues at CNES, Christophe Taillan, who implemented MAJA production within Peps.

This code relies on python (should work with python 2 and 3), and on the curl utility. I am not sure it can work on windows.


 

## Examples

### peps_maja_process

This software is still quite basic, but if you have an account at PEPS, you may download products using command lines like 

- `python ./peps_maja_process.py  -l Toulouse -a peps.txt -d 2017-11-01 -f 2017-12-01 -p prod_list_toulouse.txt` 

 which downloads the *Sentinel-2 DataTake products*  acquired in November 2017 above Toulouse. When you provide a date YY-MM-DD, it is actually YY-MM-DD:00:00:00. So a request with `-d 2015-11-01 -f 2015-11-01` will yield no result, while `-d 2015-11-01 -f 2015-11-02` will yield data acquired on 2015-11-01 (provided they exist). The list of ordered L2A products is stored in prod_list_toulouse.txt


- `python ./peps_maja_process.py  --lon 1 --lat 43.5 -a peps.txt -d 2017-11-01 -f 2017-12-01 -p prod_list_toulouse.txt`

 which downloads the Sentinel-2 products above --lon 1 --lat 43.5 (~Toulouse), acquired in November 2017. The list of ordered L2A products is stored in prod_list_toulouse.txt
 
 - `python ./peps_maja_process.py 2 --lon 1 --lat 43.5 -a peps.txt -d 2017-11-01 -f 2017-12-01 -o 51 -p prod_list_toulouse.txt ` 

 which downloads the Sentinel-2 products above --lon 1 --lat 43.5 (~Toulouse), acquired in November 2017 from orbit path number 51 only.  The list of ordered L2A products is stored in prod_list_toulouse.txt

The processing at peps takes between one or two hours. For this reason, the dowload is asynchronous and handled by another software.

### peps_maja_download

 - `python peps_maja_download.py -p prod_list_toulouse.txt -a peps.txt -w /mnt/data/PEPS_MAJA'

which checks the completion of the products listed in prod_list_toulouse.txt, and eventually download them to the specified directory /mnt/data/PEPS_MAJA


## Authentification 

The file peps.txt must contain your email address and your password on the same line, such as:

`your.email@address.fr top_secret`

To get an account : https://peps.cnes.fr/rocket/#/register


