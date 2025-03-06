import datetime
import json
import random
import threading
import tkinter
import tkinter.ttk
import traceback

import dotenv
from google.cloud import pubsub_v1

config = dotenv.dotenv_values("config.env")

def log_debug(message: str) -> None:
    print(message)  # noqa: T201
    try:
        result_box.insert(tkinter.END, str(message) + "\n")
    except Exception:
        print("Failed to insert message into ui")  # noqa: T201

def publish_message(message: str, attributes: str) -> str:
    publisher = pubsub_v1.PublisherClient()
    topic_name = "projects/" + config["project_id"] + "/topics/" + config["topic"]
    future = publisher.publish(topic_name, json.dumps(message).encode("UTF-8"), **attributes)
    return future.result()

def run_publish(message: str, test_attribute: str) -> None:
    log_debug("Message publish requested")
    try:
        message["message_id"] = message_id_entry.get()
        message["item_id"] = item_id_entry.get()
        message["location"] = location_entry.get()
        message["quantity"] = quantity_entry.get()
        message["transation_datetime"] = str(datetime.datetime.now(tz=datetime.timezone.utc))
        message["transaction_number"] = random.randint(1, 10000)
        publish_button.config(state = tkinter.DISABLED)
        log_debug("Publishing message")
        log_debug(message)
        result = publish_message(message, test_attribute)
        log_debug(result)
        publish_button.config(state = tkinter.ACTIVE)
    except Exception:
        result_box.insert(tkinter.END, traceback.format_exc())
        publish_button.config(state = tkinter.ACTIVE)

def clear_log() -> None:
    result_box.delete(0.0, tkinter.END)

root = tkinter.Tk()
root.title("Test Pub")

frame = tkinter.ttk.Frame(root, padding = 10)
frame.grid(sticky = "EWNS")

result_box = tkinter.Text(frame)
result_box.grid(column = 0, row = 0, columnspan = 2)

message = {
    "message_id": None,
    "item_id": None,
    "location": None,
    "quantity": None,
    "transation_datetime": None,
    "transaction_number": None,
}
attributes = {
    "version": "1",
}

message_id_label = tkinter.Label(frame, text = "Message ID:")
message_id_label.grid(column = 0, row = 1, ipady = 0, pady = 5, sticky = "EWNS")
message_id_entry = tkinter.Entry(frame)
message_id_entry.insert(0, "1")
message_id_entry.grid(column = 1, row = 1, ipady = 0, pady = 5, sticky = "EWNS")

item_id_label = tkinter.Label(frame, text = "Item ID:")
item_id_label.grid(column = 0, row = 2, ipady = 0, pady = 5, sticky = "EWNS")
item_id_entry = tkinter.Entry(frame)
item_id_entry.insert(0, "1")
item_id_entry.grid(column = 1, row = 2, ipady = 0, pady = 5, sticky = "EWNS")

location_label = tkinter.Label(frame, text = "Location:")
location_label.grid(column = 0, row = 3, ipady = 0, pady = 5, sticky = "EWNS")
location_entry = tkinter.Entry(frame)
location_entry.insert(0, "Georgia")
location_entry.grid(column = 1, row = 3, ipady = 0, pady = 5, sticky = "EWNS")

quantity_label = tkinter.Label(frame, text = "Quantity:")
quantity_label.grid(column = 0, row = 4, ipady = 0, pady = 5, sticky = "EWNS")
quantity_entry = tkinter.Entry(frame)
quantity_entry.insert(0, "10")
quantity_entry.grid(column = 1, row = 4, ipady = 0, pady = 5, sticky = "EWNS")

publish_button = tkinter.ttk.Button(frame, text = "Publish", command = lambda: threading.Thread(target = lambda: run_publish(message, attributes)).start())
publish_button.grid(column = 0, row = 5, ipady = 25, pady = 5, sticky = "EWNS")

clear_log_button = tkinter.ttk.Button(frame, text = "Clear Log", command = clear_log)
clear_log_button.grid(column = 1, row = 5, ipady = 25, pady = 5, sticky = "EWNS")

root.update()
root.mainloop()
