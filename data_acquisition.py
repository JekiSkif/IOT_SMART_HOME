# data acqusition module
import csv

from os import name
import pandas as pd
from init import *
import sqlite3
from sqlite3 import Error
from datetime import datetime
import time as tm
from icecream import ic as ic2
import matplotlib.pyplot as plt
import random


# Set up icecream for logging with timestamps
def time_format():
    return f'{datetime.now()}  data acq|> '


ic2.configureOutput(prefix=time_format)


# Database connection creation function
def create_connection(db_file=db_name):
    """
    Create a database connection to the SQLite database specified by db_file.
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        pp = ('Connected to version: ' + sqlite3.version)
        ic2(pp)
        return conn
    except Error as e:
        ic2(e)
    return conn


# create a table
def create_table(conn, create_table_sql):
    """
    Create a table from the create_table_sql statement.
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        ic2(e)


# Initialize the database and tables
def init_db(database):
    """
    Initialize the database with the required tables.
    """
    # SQL statements for table creation
    tables = [
        """ CREATE TABLE IF NOT EXISTS `data` (
        `name` TEXT NOT NULL,
        `timestamp` TEXT NOT NULL,
        `value` TEXT NOT NULL,
        FOREIGN KEY(`value`) REFERENCES `iot_devices`(`name`)
        );""",
        """CREATE TABLE IF NOT EXISTS `iot_devices` (
        `sys_id` INTEGER PRIMARY KEY,
        `name` TEXT NOT NULL UNIQUE,
        `status` TEXT,
        `units` TEXT,
        `last_updated` TEXT NOT NULL,
        `update_interval` INTEGER NOT NULL,
        `SafeSleepCardId` TEXT,
        `placed` TEXT,
        `dev_type` TEXT NOT NULL,
        `enabled` INTEGER,    
        `state` TEXT,
        `mode` TEXT,
        `fan` TEXT,
        `temperature` REAL,
        `dev_pub_topic` TEXT NOT NULL,
        `dev_sub_topic` TEXT NOT NULL,
        `special` TEXT        
        ); """
    ]
    # Create a database connection
    conn = create_connection(database)

    # Create tables
    if conn is not None:
        for table in tables:
            create_table(conn, table)
        conn.close()
    else:
        ic2("Error! Cannot create the database connection.")


# Acquire data from CSV and load into the database
def csv_acq_data(table_name):
    """
    Load data from CSV into the specified table.
    :param table_name: Name of the table to load data into
    """
    conn = create_connection(db_name)
    try:
        if db_init:
            data = pd.read_csv("data/SafeSleepData.csv")
            data.to_sql(table_name, conn, if_exists='append', index=False)
        else:
            data = pd.read_sql_query("SELECT * FROM " + table_name, conn)
    except Error as e:
        ic2(e)
    finally:
        if conn:
            conn.close()

        # Create a new IoT device record in the database


def create_IOT_dev(name, status, units, last_updated, update_interval, SafeSleepCardId, placed, dev_type, enabled,
                   state, mode, fan, temperature, dev_pub_topic, dev_sub_topic, special):
    """
    Create a new IoT device in the iot_devices table.
    :return: sys_id of the newly created device
    """
    sql = ''' INSERT INTO iot_devices(name, status, units, last_updated, update_interval, SafeSleepCardId, placed, dev_type, enabled, state, mode, fan, temperature, dev_pub_topic, dev_sub_topic, special)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute(sql,
                    [name, status, units, last_updated, update_interval, SafeSleepCardId, placed, dev_type, enabled,
                     state, mode, fan, temperature, dev_pub_topic, dev_sub_topic, special])
        conn.commit()
        re = cur.lastrowid
        conn.close()
        return re
    else:
        ic2("Error! Cannot create the database connection.")

    # Generate a timestamp in the required format


def timestamp():
    return str(datetime.fromtimestamp(datetime.timestamp(datetime.now()))).split('.')[0]


# Add data entry for an IoT device
def add_IOT_data(name, updated, value):
    """
    Add new IoT device data into the data table.
    :return: last row id of the inserted data
    """
    sql = ''' INSERT INTO data(name, timestamp, value)
              VALUES(?,?,?) '''
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute(sql, [name, updated, value])
        conn.commit()
        re = cur.lastrowid
        conn.close()
        return re
    else:
        ic2("Error! Cannot create the database connection.")

    # Read data for a specific IoT device from a table


def read_IOT_data(table, name):
    """
    Query tasks by name.
    :param table: Table name to query
    :param name: Name of the IoT device
    :return: Rows list selected by name
    """
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE name=?", (name,))
        rows = cur.fetchall()
        return rows
    else:
        ic2("Error! Cannot create the database connection.")

    # Update the temperature of a specific IoT device


def update_IOT_dev(tem_p):
    """
    Update temperature of an IoT device by name.
    """
    sql = ''' UPDATE iot_devices SET temperature = ?, special = 'changed' WHERE name = ?'''
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute(sql, tem_p)
        conn.commit()
        conn.close()
    else:
        ic2("Error! Cannot create the database connection.")

    # Update the status of an IoT device


def update_IOT_status(iot_dev):
    """
    Update the special status of an IoT device by sys_id.
    """
    sql = ''' UPDATE iot_devices SET special = 'done' WHERE sys_id = ?'''
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute(sql, (int(iot_dev),))
        conn.commit()
        conn.close()
    else:
        ic2("Error! Cannot create the database connection.")

    # Check for changes in IoT devices


def check_changes(table):
    """
    Check for changes in the IoT devices table.
    :return: Rows with 'changed' status
    """
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT * FROM " + table + " WHERE special=?", ('changed',))
        rows = cur.fetchall()
        return rows
    else:
        ic2("Error! Cannot create the database connection.")

    # Fetch data from a table into a DataFrame with filtering


def fetch_table_data_into_df(table_name, conn, filter):
    """
    Fetch data from a table into a DataFrame.
    :param table_name: Name of the table
    :param conn: Database connection
    :param filter: Filter condition for data
    :return: DataFrame of filtered data
    """
    return pd.read_sql_query("SELECT * from " + table_name + " WHERE `name` LIKE " + "'" + filter + "'", conn)


# Filter data by date range for a specific meter
def filter_by_date(table_name, start_date, end_date, meter):
    """
    Filter data between specific dates for a meter.
    :param table_name: Name of the table
    :param start_date: Start date for filtering
    :param end_date: End date for filtering
    :param meter: Meter name to filter
    :return: Filtered rows
    """
    conn = create_connection()
    if conn is not None:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM " + table_name + " WHERE `name` LIKE '" + meter + "' AND timestamp BETWEEN '" + start_date + "' AND '" + end_date + "'")
        rows = cur.fetchall()
        return rows
    else:
        ic2("Error! Cannot create the database connection.")

    # Fetch data from a database and table into a DataFrame with filtering


def fetch_data(database, table_name, filter):
    """
    Fetch data from the specified table in the database.
    :param database: Database file
    :param table_name: Name of the table
    :param filter: Filter condition for data
    :return: DataFrame of filtered data
    """
    TABLE_NAME = table_name
    conn = create_connection(database)
    with conn:
        return fetch_table_data_into_df(TABLE_NAME, conn, filter)


# Display graph of data for a specific meter between dates
def graph_data(meter, start_date, end_date, database=db_name):
    """
    Display a graph of meter data between specific dates.
    """
    df = pd.DataFrame(filter_by_date('data', start_date, end_date, meter), columns=['name', 'timestamp', 'value'])
    plt.plot(pd.to_datetime(df['timestamp']), df['value'])
    plt.xlabel("Timestamp")
    plt.ylabel(meter)
    plt.show()


# Generate random temperature data between a range
def get_temperature_rand(min=0, max=100):
    """
    Generate a random temperature value within a specified range.
    :return: Random temperature value
    """
    return random.uniform(min, max)


# Generate a unique SafeSleepCardId
def gen_SafeSleepCardId(card='SafeSleepCardId'):
    """
    Generate a random SafeSleepCardId.
    :return: Generated SafeSleepCardId
    """
    return (card + '-' + str(random.randint(1000, 9999)))


# Set the state of an IOT device randomly
def set_state_random():
    """
    Randomly set the state of an IoT device to either 'on' or 'off'.
    :return: Random state value
    """
    return random.choice(['on', 'off'])


# Randomly set a fan value
def set_fan_random():
    """
    Randomly set the fan state of an IoT device to either 'on' or 'off'.
    :return: Random fan state
    """
    return random.choice(['on', 'off'])


# Main execution
if __name__ == '__main__':
    # Initialize the database
    init_db(db_name)
    table = 'iot_devices'

    # Read IoT data and print the results
    rows = read_IOT_data(table, 'SafeSleep002')
    ic2(rows)

    # Check for any changes in IoT devices and update status
    for row in rows:
        ic2(row[0])
        update_IOT_status(row[0])
        newtemp = get_temperature_rand(0, 50)
        update_IOT_dev([newtemp, row[1]])

    # Fetch and display data
    data_df = fetch_data(db_name, 'iot_devices', 'SafeSleep%')
    print(data_df.head())
