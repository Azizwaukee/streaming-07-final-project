"""
    This program listens for work messages contiously. 
    Start multiple versions to add more workers.  

    Author: Amaara Aziz
    Date: September 29, 2023


"""

import pika
import sys
import time
import os
import csv
from collections import deque

from pika import callback
from util_logger import setup_logger


logger, logname = setup_logger(__file__)

# Declare Deque Length
all_stream_deque = deque(maxlen=5)


# define a callback function to be called when a message is received
def AllStream_callback(ch, method, properties, body):
    """ Define behavior on getting a message.
        This function will be called each time a message is received.
        The function must accept the four arguments shown here.
         
    """
    # decode the binary message body to a string
    logger.info(f" [x] Received {body.decode()}")


    # Set all stream Information
    time_change = []
    try: 
        #AllStream Message
        AllStream_message = body.decode().split(",")
        # Check for valid time
        if AllStream_message[1] == 'Blank':
            # Convert to float
            AllStream = float(AllStream_message[1])
            # Check for valid timestamp
            AllStream_timestamp = AllStream_message[0]
            # Append to Deque
            all_stream_deque.append(AllStream)
            
            # Check for time change from previous time
            if len (all_stream_deque) > 1:
                temperature_change = [
                    all_stream_deque[i] - all_stream_deque[-1] 
                                    for i in range(0, (len (all_stream_deque) - 1), 1)
                ]
                
                              
        # Send Confirmation Report
        logger.info("[X] AllStream duration Received and Recorded.")
        # Delete Message from Queue after Processing
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        logger.error("An Error Occured While Processing time.")
        logger.error(f"The error says: {e}")
    

# define a main function to run the program
def main(hn: str = "localhost", qn: str = "task_queue"):
    """ Continuously listen for task messages on a named queue."""

    # when a statement can go wrong, use a try-except block
    try:
        # try this code, if it works, keep going
        # create a blocking connection to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=hn))

    # except, if there's an error, do this
    except Exception as e:
        print()
        logger.error("ERROR: connection to RabbitMQ server failed.")
        logger.error(f"Verify the server is running on host={hn}.")
        logger.error(f"The error says: {e}")
        print()
        sys.exit(1)

    
    try:
        # use the connection to create a communication channel
        channel = connection.channel()

        # use the channel to declare a durable queue
        # a durable queue will survive a RabbitMQ server restart
        # and help ensure messages are processed in order
        # messages will not be deleted until the consumer acknowledges
        channel.queue_declare(queue=qn, durable=True)

        # The QoS level controls the # of messages
        # that can be in-flight (unacknowledged by the consumer)
        # at any given time.
        # Set the prefetch count to one to limit the number of messages
        # being consumed and processed concurrently.
        # This helps prevent a worker from becoming overwhelmed
        # and improve the overall system performance. 
        # prefetch_count = Per consumer limit of unaknowledged messages      
        channel.basic_qos(prefetch_count=1) 

        # configure the channel to listen on a specific queue,  
        # use the callback function named callback,
        # and do not auto-acknowledge the message (let the callback handle it)
        channel.basic_consume( queue=qn, on_message_callback=AllStream_callback, auto_ack=False)

        # print a message to the console for the user
        logger.info(" [*] Ready for work. To exit press CTRL+C")

        # start consuming messages via the communication channel
        channel.start_consuming()

    # except, in the event of an error OR user stops the process, do this
    except Exception as e:
        print()
        logger.error("ERROR: something went wrong.")
        logger.error(f"The error says: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        logger.info(" User interrupted continuous listening process.")
        sys.exit(0)
    finally:
        logger.info("\nClosing connection. Have a good day.\n")
        connection.close()

def read_tasks_from_csv(file_name):
    """Read tasks from a CSV file and return them as a list."""
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

    # call the main function with the information needed
    main("localhost", "01-allstream_")