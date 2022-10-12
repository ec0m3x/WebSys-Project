# pylint: skip-file
"""Script zum Ausführen einer .sql Datei"""
import mysql.connector
import db_credentials

SCRIPT = db_credentials.DB_SCRIPT

CON = mysql.connector.connect(host=db_credentials.DB_HOST,
                              user=db_credentials.DB_USER,
                              password=db_credentials.DB_PASSWORD,
                              database=db_credentials.DB_DATABASE)

CON.get_warnings = True

CUR = CON.cursor()

# disable foreign key checks for dropping tables
CUR.execute("set foreign_key_checks = 0")

# look for tables and drop any existing ones
print("--- SEARCHING FOR TABLES ---")
CUR.execute("show tables")
for table in CUR.fetchall():
    print("Dropping table %s" % table)
    CUR.execute("drop table if exists %s" % table)

# re-enable foreign key checks
CUR.execute("set foreign_key_checks = 1")

# open and execute sql script
with open(SCRIPT, encoding='utf-8') as file:
    # read lines, drop comments, trailing whitespaces, format commands
    print("--- FETCHING COMMANDS ---")
    # filter generator, ugly
    LINES = list(filter(None, (line.strip() for line in file if not line.strip()
                               .startswith('--') and not line.strip()
                               .startswith('#'))))

    # delete multi line comments
    while '/*' in LINES:
        del LINES[LINES.index('/*'):LINES.index('*/') + 1]

    # replace inline /*...*/ comments in case of '/*...*/ <SQL-QUERY>'
    for i, line in enumerate(LINES):
        if '/*' in line:
            LINES[i] = line.replace(line[line.index('/*'):line.index('*/') + 2],
                                    '').strip()

    # delete empty lines created by string.replace and .strip
    LINES = [line for line in LINES if line]
    # join multi line command and split at semicolon
    COMMANDS = list(filter(None, ' '.join(LINES).split(';')))
    # final cleanup, strip leading whitespaces and filter empty lines
    COMMANDS = list(filter(None, (command.strip() for command in COMMANDS)))

    print("# of commands: {}".format(len(COMMANDS)))

    # execute commands, print results
    print("--- EXECUTING COMMANDS ---")
    for command in COMMANDS:
        print(command)
        CUR.execute(command)
        if CUR.with_rows:
            print("Rows produced: {}".format(CUR.fetchall()))
        else:
            print("Number of rows affected: {}".format(CUR.rowcount))
        print("Warnings: {}".format(CUR.fetchwarnings()))
        print("*" * 70)
    print("--- COMMITTING ---")
    CON.commit()
    print("--- EXECUTION FINISHED ---")
CUR.close()
CON.close()
