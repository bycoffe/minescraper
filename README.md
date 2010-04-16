# Minescraper
This is a Python script for scraping data on U.S. mines, inspections, accidents, violations, penalties and contractors from the [Department of Labor's enforcement site](http://ogesdw.dol.gov/search.php). The site provides a limited search interface, allowing users to search up to five states at a time, with limited sort, drill-down and export capabilities.

This script allows for all the data provided on the site to be downloaded in a more raw format.

## Requirements
Python >= 2.5 
(If you are using an earlier version of Python and need to run this script, please [contact me](mailto:bycoffe@gmail.com) and I will try to assist you.)

[BeautifulSoup](http://www.crummy.com/software/BeautifulSoup)

## Usage
The script can be run from the command line, as is, and will download data for every mine in every state:
$ ./mines.py

This will, by default, create six CSV files in the current directory:

* _mines.csv_ - A list of all mines, along with the following information about each one:
    * Mine ID
    * Mine Name
    * State
    * County
    * Mine Type
    * Coal or Metal Mine
    * Mine Status
    * Mine Status Date
    * Inspections
    * Accidnets
    * Violations
    * Contractors
    * Controller ID
    * Controller Name
    * Operator ID
    * Operator Name
    * Begin Date
    * SIC
    * SIC Description

* _inspections.csv_ - A list of all inspections, along with the following information about each one:
    * Event No.
    * Mine ID (relates to Mine ID in mines.csv)
    * Violations
    * Inspection Activity Code
    * Inspection Activity Code Description
    * Inspection Begin Date
    * Inspection End Date

* _accidents.csv_ - A list of all mine accidents, along with the following information about each one:
    * Mine ID
    * Subunit
    * Subunit Description
    * Accident Date
    * Degree of Injury
    * Accident Classification Description
    * Occupation Code Description
    * Miner Activity
    * Total Experience
    * Mine Experience
    * Job Experience
    * Accident Narrative

* _violations.csv_ - A list of all mine violations, along with the following information about each one:
    * Violation No.
    * Violation Assessed?
    * Event No. (relates to Event No. in inspections.csv)
    * Date Issued
    * S&S Designation
    * 30 CFR
    * Section of Act
    * Type of Issuance
    * Date Terminated

* _assessments.csv_ - A list of all penalties proposed and assessed against mines, along with the following information about each one:
    * Violation No. (relates to Violation No. in violations.csv)
    * Violator ID
    * Violator Name
    * Proposed Penalty Amount
    * Current Assessment Amount
    * Paid Proposed Penalty Amount
    * Last Action Code

* _contractors.csv_ - A list of all mine contractors, along with the following information about each one:
    * Mine ID (relates to Mine ID in mines.csv)
    * Contractor ID
    * Contractor Name
    * Contractor Start Date
    * Contractor End Date

See [the Mine Safety and Health Administration's data dictionary](http://ogesdw.dol.gov/dd/MSHA_DD.pdf) for more detailed data definitions.

_Please note:_ This script can take a long time to run. If you're interested in downloading all the data available, I would suggest running separated instances of the script on several different computers, each responsible for a state or set of states.

_Other usage scenarios:_

* Download data for a single state:

    >>> from minescraper.mines import MineScraper

    >>> scraper = MineScraper('mines.csv', 'inspections.csv', 'accidents.csv', 'contractors.csv', 'violations.csv', 'assessments.csv')

    >>> scraper.write_headers()

    >>> scraper.scrape('WV') # Just download data for West Virginia

* Get only a list of mines (and the rest of the data in mines.csv) for a state:

    >>> from minescraper.mines import MineScraper

    # Don't include inspections, violations, assessments, accidents or contractors
    >>> scraper = MineScraper('mines.csv', 'inspections.csv', 'accidents.csv', 'contractors.csv', 'violations.csv', 'assessments.csv', False, False, False, False, False)

    >>> scraper.write_headers()

    >>> scraper.scrape('WV')

* Get all data for _active_ mines in a single state:

    >>> from minescraper.mines import MineScraper

    # Don't include inspections, violations, assessments, accidents or contractors
    >>> scraper = MineScraper('mines.csv', 'inspections.csv', 'accidents.csv', 'contractors.csv', 'violations.csv', 'assessments.csv', False, False, False, False, False, True)

    >>> scraper.write_headers()

    >>> scraper.scrape('WV')

## License
Two-clause BSD. See [LICENSE](http://github.com/bycoffe/minescraper/blob/master/LICENSE)

## Other data of interest
The Mine Safety and Health Administration has released other mine data [here](http://www.msha.gov/OpenGovernmentData/OGIMSHA.asp)
