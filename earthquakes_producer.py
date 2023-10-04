"""
    This program sends a message to a queue on the RabbitMQ server.
    Messages come from a csv file.
    Make tasks harder/longer-running by adding dots at the end of the message.


    Author: Aziz
    Date: October 1, 2023

"""


import pika
import sys
import webbrowser
from util_logger import setup_logger
import csv
import time
import logging


logger, logname = setup_logger(__file__)

# Set up basic configuration for logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Declare program constants
HOST = "localhost"
PORT = 9999
ADDRESS_TUPLE = (HOST, PORT)
TASKS_FILE_NAME = "earthquakes.csv"
SHOW_OFFER = True  # Control whether to show the RabbitMQ Admin webpage offer

SHOW_OFFER = True

def offer_rabbitmq_admin_site():
    """Offer to open the RabbitMQ Admin website"""
    ans = input("Would you like to monitor RabbitMQ queues? y or n ")
    logger.info("Seeing if you want to monitor RabbitMQ queues")
    if ans.lower() == "y":
        webbrowser.open_new("http://localhost:15672/#/queues")
        logger.info(f"Answer is {ans}.")


def send_message(host: str, queue_name: str, message: str):
    """
    Creates and sends a message to the queue each execution.
    This process runs and finishes.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        queue_name (str): the name of the queue
        message (str): the message to be sent to the queue
    """

    try:
        # create a blocking connection to the RabbitMQ server
        conn = pika.BlockingConnection(pika.ConnectionParameters(host))
        # use the connection to create a communication channel
        ch = conn.channel()
        # use the channel to declare a durable queue
        # a durable queue will survive a RabbitMQ server restart
        # and help ensure messages are processed in order
        # messages will not be deleted until the consumer acknowledges
        ch.queue_declare(queue=queue_name, durable=True)
        # use the channel to publish a message to the queue
        # every message passes through an exchange
        ch.basic_publish(exchange="", routing_key=queue_name, body=message)
        # print a message to the console for the user
        logger.info(f" [x] Sent {message}")
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error: Connection to RabbitMQ server failed: {e}")
        sys.exit(1)
    finally:
        # close the connection to the server
        conn.close()


def read_earthquakes_from_csv(file_name):
    """Read earthquakes from a CSV file and return them as a list."""
    tasks = []
    with open(file_name, "r") as input_file:
        reader = csv.reader(input_file)
        for row in reader:
            if row:
                tasks.append(row[0])  # Extract the task from the first column
    return tasks


# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions
# without executing the code below.
# If this is the program being run, then execute the code below
if __name__ == "__main__":  
    # ask the user if they'd like to open the RabbitMQ Admin site
    offer_rabbitmq_admin_site()

    #call the custom function to read tasks from csv to look at our previously specified csv file
    tasks = read_earthquakes_from_csv(TASKS_FILE_NAME)

    for task in tasks:
        send_message("localhost", "earthquakes_queue", task)
        logger.info(f"Sent: {task} to RabbitMQ.")
