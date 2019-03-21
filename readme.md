

# peps_maja
PEPS is the French Sentinel collaborative ground segment: https://peps.cnes.fr. PEPS is mirroring all the Sentinel data provided by ESA, and is providing a simplified access. It also implements a few processors among which [MAJA atmospheric correction processor](http://www.cesbio.ups-tlse.fr/multitemp/?p=6203). This repository contains two scripts to submit a MAJA L2A processing and to download MAJA L2A products from PEPS. MAJA processing is implemented in two ways within PEPS :
- single product MAJA processing (for which an browser interface is also available)
- full time series MAJA processing (which is only available on the command line)

The full time series production, that we call, with our excellent Frenglish, "Full_MAJA", is much more efficient than the single product processing. If you try to produce a time series with the single product, as MAJA requires time series, the products will be processed several times, requiring a large processing power used inefficiently.

As a result, we provide here an interface to use full maja production on PEPS from python command lines.

- full_maja_process.py asks [PEPS](https://peps.cnes.fr) to process Sentinel-2 products with MAJA. 
- full_maja_download.py checks if the processing is completed and eventually downloads the products. 

This code is only the emerged part of an Iceberg project, which is the implementation of MAJA within PEPS, which was done by a colleague at CNES, Christophe Taillan.

This code relies on python (it should work with python 2 and 3). It was developped for linux, and I am not sure it can work on windows.


 

## Examples

### full_maja_process

This script will ask PEPS to process z continuous time series (from a begin date to an end date). It is currently limited to a maximum of one year and a minimum of two months. You will have to start a different command line for each tile you want to process. Because of issues with Sentinel-2 L1C products before the 1st of April 2016, full_maja processing must start after the 1st of April 2016. The command line is very simple :

- `python ./full_maja_process.py  -t 31TCJ -a peps.txt -d 2017-01-01 -f 2018-01-01 -g 31TCJ_20170101.log` 

It will submit Maja processing for the Sentinel-2 L1C products acquired in 2017 above Toulouse (31TCJ tile). A log file is issued which is necessary to check the completion and download the products with full_maja_download.py. If you want to start several tiles in paralllel, remember to specify a different logfile, or you will lose the information to retrive the data. If you have done such an error (I know it will happen ;) ), it is still possible to retrieve the results from the PEPS interface after having logged.

The option `-a peps.txt` provides the authentification information (see below  for its format)

*Specifying the relative orbit*

Sometimes, a given tile is fully covered by one orbit, and only partially by another one. To save processing time and space, you can select to process only one orbut by specifying the orbit obtion with -o option.

- `python ./full_maja_process.py  -t 31TCJ -o 51 -a peps.txt -d 2017-01-01 -f 2018-01-01 -g 31TCJ_20170101.log` 

It will only process the data from relative orbit 51. But is you want to process the two orbits ofor one tile, it is better to specify nothing than launching two separate processings with each orbit 

### full_maja_download

 - ` python full_maja_download.py -a peps.txt -g 31TCJ_20170101.log`
 
The syntax of full_maja_download.py is even simpler, only the authentification information and the  log file are necessary.

 - ` python full_maja_download.py -a peps.txt -g 31TCJ_20170101.log -w /path/to/31TCJ`

You may also specify an output directory for downloading the datasets.

The processing of the time series with MAJA can't be done in parallel, as date D+1 needs the result of date D to be processed. It takes less than one hour to generate the first product of a time series, which is based on a complex initiatlisation procedure, and then around 25 minutes per date to process. To save time and space, the dates with more than 90% of clouds are not issued. The products are only made available at the end, when everything is produced, so if you are noat patient, you will have to start  the command line several times.



## Authentification 

The file peps.txt must contain your email address and your password on the same line, such as:

`your.email@address.fr top_secret`

To get an account : https://peps.cnes.fr/rocket/#/register


