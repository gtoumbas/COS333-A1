"""
Authors: George Toumbas, Shanzay Waseem

Contains the class RegDB, which can search and
display information from the registrar database.
"""
import sqlite3
import textwrap
import sys


class RegDB:
    """
    Represents registrar database.

    Attributes:
        DB_URL (str): Path to database

    Methods:
        close():
            Closes connection to the db.
        search(args):
            Searches the database and displays the results.
        get_details(args):
            Searches the database for single class and displays
            the results.
        get_search_query(args):
            Returns a SQL query for a search based on the arguments.
        get_details_query():
            Returns a SQL query for classid-based search.
        display_table(results, max_len=72):
            Creates a table from the results of sql search query.
        replace_wildcards(string):
            Replaces wildcard chars with escape chars + wildcard char.
        format_args(args):
            Formats the arguments for the search query.
    """

    DB_URL = 'file:reg.sqlite?mode=ro'

    def __init__(self):

        try:
            self.conn = sqlite3.connect(
                self.DB_URL, isolation_level=None, uri=True)
            self.cur = self.conn.cursor()

        except Exception as error:
            sys.stderr.write(f"{sys.argv[0]}: {error}")
            sys.exit(1)

    def close(self):
        """
        Closes the connection to the database.
        """
        self.conn.close()

    def search(self, args):
        """
        Searches the database and displays the results.

        Args:
            args (argparse.Namespace): Arguments from command line
        """
        self.format_args(args)
        query = self.get_search_query(args)
        # Parameters set to fill in prepared statements
        parameters = []
        if args.d:
            parameters.append(args.d)
        if args.n:
            parameters.append(args.n)
        if args.a:
            parameters.append(args.a)
        if args.t:
            parameters.append(args.t)
        try:
            results = self.cur.execute(query, parameters).fetchall()

        # Error if the query is unsuccessful
        except Exception as error:
            sys.stderr.write(f"{sys.argv[0]}: {error}")
            sys.exit(1)

        self.display_table(results)

    def get_details(self, args):
        """
        Searches the database for a single class and
        displays the results.

        Args:
            args (argparse.Namespace): Arguments from command line
        """
        class_id = args.classID

        if not str(class_id).isdigit():
            sys.stderr.write("Error: Class ID must be a number")
            sys.exit(1)

        query = self.get_details_query()
        # Parameters set to fill in prepared statements
        parameters = [class_id]
        results = self.cur.execute(query, parameters).fetchall()

        if len(results) == 0:
            sys.stderr.write(f"no class with classid {class_id} exists")
            sys.exit(1)

        self.display_details(results)

    def get_search_query(self, args):
        """
        Returns a SQL query for search based on the arguments.

        Args:
            args (argparse.Namespace): Arguments from command line

        Returns:
            query (str): SQL query
        """
        dept = args.d
        num = args.n
        area = args.a
        title = args.t

        query = """
        SELECT classid, dept, coursenum, area, title
        FROM classes
        INNER JOIN courses ON classes.courseid = courses.courseid
        INNER JOIN crosslistings ON classes.courseid = crosslistings.courseid
        """

        # adding WHERE prepared clauses to the query
        where = "WHERE "
        if dept:
            where += "dept LIKE ? escape '@' AND "
        if num:
            where += "coursenum LIKE ? escape '@' AND "
        if area:
            where += "area LIKE ? escape '@' AND "
        if title:
            where += "title LIKE ? escape '@' AND "

        # Remove last AND
        if where != "WHERE ":
            where = where[:-5]
        else:
            where = ""

        # Adding WHERE to QUERY
        query += where

        # Adding ORDER BY
        query += " ORDER BY dept, coursenum, classid"

        return query

    def get_details_query(self):
        """
        Returns a SQL query for classid-based search.

        Returns:
            query (str): SQL query
        """
        query = """
        SELECT classes.courseid, days, starttime, endtime, bldg, roomnum, dept, coursenum, area, title, descrip, prereqs, profname
        FROM classes
        INNER JOIN courses ON classes.courseid = courses.courseid
        INNER JOIN crosslistings ON classes.courseid = crosslistings.courseid
        LEFT JOIN coursesprofs ON classes.courseid = coursesprofs.courseid
        LEFT JOIN profs ON coursesprofs.profid = profs.profid
        """

        # Adding WHERE clauses
        where = "WHERE classid = ?"

        # Adding WHERE to QUERY
        query += where

        # Adding ORDER BY
        query += " ORDER BY dept, coursenum"
        return query

    def display_details(self, results):
        """
        Displays the results of a classid-based search.

        Args:
            results (list): Results of the search query
        """
        num_columns = 13
        res = results[0]

        # Checking the length of results. This should never happen,
        # as errors should be caught be when query executed
        if len(res) != num_columns:
            sys.stderr.write(
                "Error: Invalid number items in details display")
            sys.exit(1)

        # case for multiple depts and profs
        dept_num = ""
        profs = []
        for curr in results:
            new_dept_num = f"{curr[6]} {curr[7]}"
            if new_dept_num not in dept_num:
                dept_num += f"Dept and Number: {new_dept_num}\n"
            profs.append(curr[12])

        profs = list(set(profs))
        profs.sort()
        prof_str = ""
        for curr_prof in profs:
            prof_str += f"Professor: {curr_prof}\n"

        # Removing the last newline
        prof_str = prof_str[:-1]

        wrapped_descrip = textwrap.fill(
            f"Description: {res[10]}", 72, break_long_words=False)
        wrapped_title = textwrap.fill(
            f"Title: {res[9]}", 72, break_long_words=False)
        wrapped_prereqs = textwrap.fill(
            f"Prerequisites: {res[11]}", 72, break_long_words=True)

        print(f"Course Id: {res[0]}\n")
        print(f"Days: {res[1]}")
        print(f"Start time: {res[2]}")
        print(f"End time: {res[3]}")
        print(f"Building: {res[4]}")
        print(f"Room: {res[5]}\n")
        print(dept_num)
        print(f"Area: {res[8]}\n")
        print(f"{wrapped_title}\n")
        print(f"{wrapped_descrip}\n")
        if len(res[11]) > 0:
            print(f"{wrapped_prereqs}\n")
        else:
            print("Prerequisites:\n")
        if profs[0] is not None:
            print(f"{prof_str}")

    def display_table(self, results, max_len=72):
        """
        Creates and prints a table of results from a search query.

        Args:
            results (list): Results of the search query
            max_len (int): Maximum length of a line
        """

        header = "ClsId Dept CrsNum Area Title"
        underline = "----- ---- ------ ---- -----"
        print(header)
        print(underline)

        for curr in results:
            classid, dept, coursenum, area, title = curr

            # Right aligning columns except title.
            # Info from https://docs.python.org/3/library/string.html
            line = f"{classid:>5} {dept:>4} {coursenum:>6} " + \
                f"{area:>4} {title}"
            len_without_title = len(line) - len(title)

            line = textwrap.fill(
                line, max_len, subsequent_indent=" " *
                len_without_title, break_long_words=False)

            print(line)

    def replace_wildcards(self, string):
        """
        Replaces wildcard chars with escape chars + wildcard char.

        Args:
            string (str): String to replace wildcards in

        Returns:
            string (str): String with wildcards replaced
        """
        string = string.replace("%", "@%")
        string = string.replace("_", "@_")
        return string

    def format_args(self, args):
        """
        Removes wildcards, converts to lowercase,
        and removes newline chars

        Args:
            args (list): List of arguments to format
        """
        for key, value in vars(args).items():
            if value:
                value = self.replace_wildcards(value)
                value = value.lower()
                value = value.replace("\n", "")
                value = f"%{value}%"
                setattr(args, key, value)
