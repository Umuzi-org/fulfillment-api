import os
import sys
import time

import psycopg

ATTEMPTS = 30


def main():
    for _ in range(ATTEMPTS):
        try:
            connection = psycopg.connect(
                dbname=os.environ['POSTGRES_DB'],
                user=os.environ['POSTGRES_USER'],
                password=os.environ['POSTGRES_PASSWORD'],
                host=os.environ['POSTGRES_HOST'],
                port=os.environ['POSTGRES_PORT'],
                connect_timeout=2,
            )
        except psycopg.OperationalError:
            time.sleep(1)
            continue
        connection.close()
        return
    sys.exit('database did not accept connections')


if __name__ == '__main__':
    main()
