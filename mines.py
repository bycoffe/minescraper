#!/usr/bin/env python
import csv
import re
import sys
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup


class MineScraper(object):

    ROWS_PER_PAGE = 5000

    MINE_FIELDS = ['mine_id', 'name', 'state', 'county', 'mine_type', 'coal_metal',
                   'status', 'status_date', 'inspections', 'accidents', 'violations',
                   'contractors', 'controller_id', 'controller_name', 'operator_id',
                   'operator_name', 'begin_date', 'sic', 'sic_description', ]

    INSPECTION_FIELDS = ['event_no', 'mine_id', 'violations', 'activity_code',
                         'description', 'begin_date', 'end_date', ]

    ACCIDENT_FIELDS = ['mine_id', 'contractor_id', 'subunit', 'subunit_description', 
                       'date', 'injury_degree', 'classification_description',
                       'occupation_code_description', 'miner_activity',
                       'total_experience', 'mine_experience', 'job_experience',
                       'accident_narrative',]

    CONTRACTOR_FIELDS = ['mine_id', 'contractor_id', 'name', 'start_date',
                         'end_date', ]

    VIOLATION_FIELDS = ['violation_no', 'assessed', 'event_no', 'date_issued',
                        'designation', 'cfr', 'section', 'issuance_type', 
                        'date_terminated', ]

    ASSESSMENT_FIELDS = ['violation_no', 'violator_id', 'violator_name',
                         'proposed_penalty', 'current_assessment_amt',
                         'paid_proposed_penalty', 'last_action', ]

    def __init__(self, mine_filename, inspection_filename, accident_filename,
            contractor_filename, violation_filename, assessment_filename,
            include_inspections=True, include_violations=True, 
            include_assessments=True, include_accidents=True,
            include_contractors=True,
            active_only=False):
        """Arguments are the filenames where each type 
        of data should be saved. This should be overridden 
        if you'd rather save the data to a database or 
        output it in another way. The include_ arguments
        are used to determine whether to include that data. 

        Set active_only to True to retrieve data only for active mines.

        Leaving out unnecessary data sets can speed this script
        up considerably.
        """
        self.mine_filename = mine_filename
        self.inspection_filename = inspection_filename
        self.accident_filename = accident_filename
        self.contractor_filename = contractor_filename
        self.violation_filename = violation_filename
        self.assessment_filename = assessment_filename

        self.include_inspections = include_inspections
        self.include_violations = include_violations
        self.include_assessments = include_assessments
        self.include_accidents = include_accidents
        self.include_contractors = include_contractors

        self.active_only = active_only


    def write_headers(self):
        # Output header rows for each data file.
        csv.writer(open(self.mine_filename, 'a')).writerow(self.MINE_FIELDS)

        if self.include_inspections:
            csv.writer(open(self.inspection_filename, 'a')).writerow(self.INSPECTION_FIELDS)

        if self.include_accidents:
            csv.writer(open(self.accident_filename, 'a')).writerow(self.ACCIDENT_FIELDS)

        if self.include_contractors:
            csv.writer(open(self.contractor_filename, 'a')).writerow(self.CONTRACTOR_FIELDS)

        if self.include_violations:
            csv.writer(open(self.violation_filename, 'a')).writerow(self.VIOLATION_FIELDS)

        if self.include_assessments:
            csv.writer(open(self.assessment_filename, 'a')).writerow(self.ASSESSMENT_FIELDS)


    def scrape(self, state):
        self.state = state

        # Loop through a list of all the mines in this state
        # and basic data about them (type, operator, etc.)
        for row_data in self._get_state_mines(self.state):

            # Check whether this mine is active and whether 
            # the active_only flag is set to True, then act
            # accordingly.
            if self.active_only and row_data['status'] != 'Active':
                continue

            self._output_data(open(self.mine_filename, 'a'), 
                              row_data,
                              self.MINE_FIELDS)

            # If this mine has had at least one inspection,
            # get data about the inspection.
            if int(row_data['inspections']) > 0 and self.include_inspections:
                for inspection_row in self._get_inspection_data(row_data):
                    inspection_row = dict(zip(self.INSPECTION_FIELDS, inspection_row))
                    self._output_data(open(self.inspection_filename, 'a'),
                                      inspection_row,
                                      self.INSPECTION_FIELDS)

                    # If any violations were reported during this
                    # inspection, get data about it.
                    if int(inspection_row['violations']) > 0 and self.include_violations:
                        for violation_row in self._get_violation_data(inspection_row):
                            violation_row = dict(zip(self.VIOLATION_FIELDS,
                                                     violation_row))
                            self._output_data(open(self.violation_filename, 'a'),
                                              violation_row,
                                              self.VIOLATION_FIELDS)

                            # If any penalties were assessed for this 
                            # violation, get the available data about them.
                            if violation_row['assessed'] == 'Yes' and self.include_assessments:
                                for assessment_row in self._get_assessment_data(violation_row):
                                    self._output_data(open(self.assessment_filename, 'a'),
                                                      assessment_row,
                                                      self.ASSESSMENT_FIELDS)


            # Get data about any accidents reported at this mine.
            if int(row_data['accidents']) > 0 and self.include_accidents:
                self._get_related_data(row_data, 
                                       'http://ogesdw.dol.gov/mshaAccident.php',
                                       self.ACCIDENT_FIELDS,
                                       self.accident_filename,
                                       self._parse_accident_page)


            # Get data about any contractors associated with this mine.
            if int(row_data['contractors']) > 0 and self.include_contractors:
                self._get_related_data(row_data,
                                       'http://ogesdw.dol.gov/mshaMineContractor.php',
                                       self.CONTRACTOR_FIELDS,
                                       self.contractor_filename,
                                       self._parse_page)
                

    def _get_state_mines(self, state):
        """Get a list of all the mines in the given state, along
        with the data about each available on the state listing page.
        """
        page = self._get_state_page(state)
        data = self._parse_page(page)

        # We're only getting 5,000 results at a time
        # (or else we'll get a broken page), so if the
        # first result set has 5,000 records in it, we
        # need to get another page worth of data. (It would
        # be safer to use a while loop to continue 
        # getting data until there's none left, but
        # at the time of this writing the most 
        # mines in a single state was less than 10,000.)
        if len(data) >= self.ROWS_PER_PAGE:
            page = self._get_state_page(state, 2)
            data += self._parse_page(page)

        if len(data) >= self.ROWS_PER_PAGE * 2:
            page = self._get_state_page(state, 3)
            data += self._parse_page(page)

        for row in data:
            row_data = dict(zip(self.MINE_FIELDS, row))

            yield row_data


    def _get_inspection_data(self, row_data):
        """Get a list of all inspections for the mine
        whose ID is given in row_data.
        """
        inspection_url = 'http://ogesdw.dol.gov/mshaInspection.php'
        inspection_page = self._get_list_page(
                inspection_url,
                row_data['mine_id'])
        inspection_data = self._parse_page(inspection_page)

        # We're only getting 5,000 results at a time
        # (or else we'll get a broken page), so if the
        # first result set has 5,000 records in it, we
        # need to get another page worth of data. (It would
        # be safer to use a while loop to continue 
        # getting data until there's none left, but
        # at the time of this writing the most 
        # inspections for a single mine was just
        # over 5,000.)
        if len(inspection_data) >= self.ROWS_PER_PAGE:
            inspection_page = self._get_list_page(
                    inspection_url,
                    row_data['mine_id'], 
                    2)
            inspection_data += self._parse_page(inspection_page)

        return inspection_data


    def _get_violation_data(self, inspection_row):
        """Get a list of violations for the inspection whose
        ID is given in inspection_row.
        """
        violations_page = self._get_violation_list_page(inspection_row['event_no'])
        violation_data = self._parse_page(violations_page)
        return violation_data


    def _get_assessment_data(self, violation_row):
        """Get a list of assessed penalties for the violation
        whose ID is given in violation_row.
        """
        assessment_page = self._get_assessment_page(violation_row['violation_no'])
        assessment_data = self._parse_page(assessment_page)
        return assessment_data



    def _get_related_data(self, row_data, url, fields, filename, parser):
        """Get contractor or accident data for the mine_id given in row_data.
        """
        page = self._get_list_page(url, row_data['mine_id'])
        data = parser(page)
        for row in data:
            self._output_data(open(filename, 'a'), row, fields)
                              

    def _get_state_page(self, state, set_num=0):
        """Set second_set to True if it's the second pass for this state,
        because only 5000 results can be fetched at a time.
        """
        url = 'http://ogesdw.dol.gov/mshaMine.php'
        data = {'states[]': state,
                'MSHA': 'MSHA',
                'resultsPerPage': self.ROWS_PER_PAGE,
                'offset': self.ROWS_PER_PAGE * (set_num-1),
                'currentPage': set_num,
                }
        return self._get_page(url, data)


    def _parse_row(self, row):
        """Get the relevant data out of a table row: whatever's in
        the innermost tag of each cell.
        """
        data = []
        for cell in row.findAll('td'):
            if cell.find('a'):
                content = cell.find('a').renderContents()
            else:
                content = cell.renderContents()
            data.append(content.replace('&nbsp;', ' ').strip())

        return data


    def _parse_page(self, content):
        """Get the table that contains the data we're after.
        This works for most cases because most of the data pages
        are structured the same way.

        Those that are structured in a different way should get
        their own parse function.
        """
        soup = BeautifulSoup(content)

        # The table with the data in it is the first (and,
        # incidentally, the only) table on the page with an
        # inline width set to 965px.
        table = soup.find('table', {'width': '965px'})
        return [self._parse_row(row) for row in table.findAll('tr')[2:] 
                if row.find('td')]


    def _output_data(self, fh, data, fields):
        """Write the given data to the given file handler
        in CSV format.
        """
        if type(data) == dict:
            row = data
        else:
            row = dict(zip(fields, data))

        csv.DictWriter(fh, fields).writerow(row)
        fh.close()


    def _get_page(self, url, data):
        """Get the contents of the page at the given URL,
        using the given data as POST parameters.
        """
        req = urllib2.Request(url, urllib.urlencode(data))
        response = urllib2.urlopen(req)
        if response.code == 200:
            return response.read()

        return None


    def _get_list_page(self, url, mine_id, page_no=1):
        """Most of the data pages we're interested in can
        be accessed with the same parameters, though they each
        have a different URL. This function keeps us from
        repeating the same code for each URL.
        """
        data = {'resultsPerPage': self.ROWS_PER_PAGE,
                'mineId': mine_id,
                'mineOffset': '0',
                'mineCurrentPage': page_no, }
        return self._get_page(url, data)


    def _parse_accident_page(self, content):
        """The table on accident pages is set up differently from
        those on mine and inspection pages, so self._parse_page
        won't work.
        """
        soup = BeautifulSoup(content)
        table = soup.find('table', {'id': 'ogdbTable'})

        # This table has intermediary rows that have 
        # no content in them (they're just empty <tr></tr>
        # tags. Skip those.
        rows = [row for row in table.findAll('tr') if row.find('td')]
        data = []
        for row in rows:
            data.append([cell.renderContents().strip() for cell in row.findAll('td')])
        return data


    def _get_violation_list_page(self, violation_id):
        url = 'http://ogesdw.dol.gov/mshaViolation.php'
        data = {'violSearchId': violation_id, }
        return self._get_page(url, data)


    def _get_assessment_page(self, violation_id):
        url = 'http://ogesdw.dol.gov/mshaAssdViolation.php'
        data = {'assViolSearchId': violation_id, }
        return self._get_page(url, data)


STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 
          'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 
          'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 
          'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', ]


if __name__ == '__main__':
    scraper = MineScraper('mines.csv', 'inspections.csv', 'accidents.csv',
                       'contractors.csv', 'violations.csv', 'assessments.csv')
    scraper.write_headers()
    for state in STATES:
        print state
        scraper.scrape(state)
