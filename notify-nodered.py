#! /usr/bin/env python3

import random
import datetime
import time
import paho.mqtt.client as mqtt
import json
import re
import threading
from argparse import ArgumentParser
from argcomplete import autocomplete

FILE="haproxy-test.log"
DEFAULT_BROKER_MQTT={
    "host": "192.168.1.117",
    "port": 1883
}

def product_logs(file_path: str):
    with open(file_path, "w") as file:
        while True:
            client_ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
            request = random.choice(["GET /index.html", "POST /api/data", "GET /contact", "PUT /update"])
            status_code = 429 if random.random() < 0.2 else random.choice([200, 404, 500])
            response_size = random.randint(100, 5000)
            response_time = random.randint(1, 1000) / 1000.0  # in seconds

            now = datetime.datetime.now()
            syslog_timestamp = now.strftime('%b %d %H:%M:%S')
            hostname = 'localhost'
            pid = random.randint(1000, 5000)
            client_port = random.randint(1024, 65535)
            accept_date = now.strftime('%d/%b/%Y:%H:%M:%S +0000')
            frontend_name = 'http-in'
            backend_name = 'servers'
            server_name = 'srv1'
            Tq = Tw = Tc = Tr = random.randint(1, 100)
            Tt = int(response_time * 1000)
            bytes_read = response_size
            captured_request_cookie = '-'
            captured_response_cookie = '-'
            termination_state = '---'
            actconn = feconn = beconn = srv_conn = retries = random.randint(1, 10)
            srv_queue = backend_queue = 0

            log_entry = (
                f"{syslog_timestamp} {hostname} haproxy[{pid}]: "
                f"{client_ip}:{client_port} [{accept_date}] {frontend_name} {backend_name}/{server_name} "
                f"{Tq}/{Tw}/{Tc}/{Tr}/{Tt} {status_code} {bytes_read} "
                f"{captured_request_cookie} {captured_response_cookie} {termination_state} "
                f"{actconn}/{feconn}/{beconn}/{srv_conn}/{retries} {srv_queue}/{backend_queue} "
                f'"{request}"\n'
            )

            file.write(log_entry)
            file.flush() 
            time.sleep(1)

def notify(broker: dict, date: str, client_ip: str, request: str) -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(
        username="etu",
        password="-etu-"
    )

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected with result code {reason_code}")

    def on_message(client, userdata, msg):
        print(f"{msg.topic} : {msg.payload}")
    
    def on_publish(client, userdata, mid, reason_code, properties):
        print("Message published")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish

    client.connect(
        host=broker["host"],
        port=broker["port"]
    )

    client.loop_start()

    message = {
        "alert": "DDOS",
        "source_ip": client_ip,
        "date": date,
        "request": request
    }

    client.publish("haproxy/alerts", json.dumps(message))

    client.disconnect()
    client.loop_stop()


# Function to extract the date from the log line
def parse_date(line: str) -> str:
    # Regular expression to capture the timestamp within square brackets
    match = re.search("[A-Za-z]{3} [0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", line)
    if match:
        return match.group(0)  # Returns the captured timestamp (e.g., "Jan 13 09:48:43")
    return ""  # Return empty if not found


# Function to extract the client IP address from the log line
def parse_client(line: str) -> str:
    # Regular expression to capture the client IP address (before the date)
    match = re.search("([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*):[0-9]*", line)
    if match:
        return match.group(1)  # Returns the client IP address
    return ""  # Return empty if not found

# Function to extract the HTTP request path from the log line
def parse_request(line: str) -> str:
    # Regular expression to capture the HTTP method and request path
    match = re.search("[A-Z]* /[A-Za-z0-9]+(?:/[A-Za-z0-9]+)*", line)
    if match:
        return match.group(0)  # Returns the captured request path (e.g., "/index.html")
    return ""  # Return empty if not found


def consume_logs(file_path: str):
    notified_429 = False

    with open(file_path, "r") as file:
        while True:
            line = file.readline()
            if not line:
                time.sleep(1)  # Sleep briefly to avoid busy waiting
                continue
            
            # Extract the status code using regex
            match = re.search(r'\s(\d{3})\s', line)
            if match:
                status_code = int(match.group(1))

                if status_code == 429 and not notified_429:
                    print(f"Detected 429: {line.strip()}")
                    date = parse_date(line)
                    client_ip = parse_client(line)
                    request = parse_request(line)

                    notify(broker=BROKER_MQTT, date=date, client_ip=client_ip, request=request)  # Notify on the first 429
                    notified_429 = True
                    print("\nBROKER NOTIFIED\n")

                elif 200 <= status_code < 300:
                    print(f"Detected 2XX: {line.strip()}")
                    notified_429 = False  # Reset after detecting a 2XX status

def main()->None:
    # Command-line argument parsing
    parser = ArgumentParser(description="HAProxy Log Generator and Consumer")
    
    # Define CLI arguments
    parser.add_argument('--run-test', action='store_true', default=False, help="Run log production and consumption in parallel")
    parser.add_argument('--file', type=str, default=FILE, help="Path to the log file")
    parser.add_argument('--broker-host', type=str, default=DEFAULT_BROKER_MQTT["host"], help="MQTT Broker Host")
    parser.add_argument('--broker-port', type=int, default=DEFAULT_BROKER_MQTT["port"], help="MQTT Broker Port")
    
    autocomplete(parser)

    # Parse arguments
    args = parser.parse_args()

    global BROKER_MQTT
    BROKER_MQTT = {
        "host": args.broker_host,
        "port": args.broker_port
    }

    # If --run-test is set, start the log producer and consumer in parallel
    if args.run_test:
        log_producer_thread = threading.Thread(target=product_logs, args=(args.file,))
        log_consumer_thread = threading.Thread(target=consume_logs, args=(args.file,))

        log_producer_thread.start()
        log_consumer_thread.start()

        log_producer_thread.join()
        log_consumer_thread.join()
    else:
        consume_logs(args.file)  # Only consume logs if --run-test is not specified


if __name__ == "__main__":
    main()