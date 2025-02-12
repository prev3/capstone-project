import datetime
import threading
import tkinter
import tkinter.ttk
import traceback

import dotenv
from google.cloud import pubsub_v1

config = dotenv.dotenv_values("config.env")

def publish_message(message: str, attributes: str) -> str:
    publisher = pubsub_v1.PublisherClient()
    topic_name = "projects/" + config["project_id"] + "/topics/" + config["topic"]
    future = publisher.publish(topic_name, message.encode("UTF-8"), **attributes)
    return future.result()

def run_publish(message: str, test_attribute: str) -> None:
    try:
        publish_button.config(state = tkinter.DISABLED)
        result = publish_message(message, test_attribute)
        result_box.insert(tkinter.END, result + "\n")
        publish_button.config(state = tkinter.ACTIVE)
    except Exception:
        result_box.insert(tkinter.END, traceback.format_exc())
        publish_button.config(state = tkinter.ACTIVE)

def clear_text() -> None:
    result_box.delete(0.0, tkinter.END)

root = tkinter.Tk()
root.title("Test Pub")

frame = tkinter.ttk.Frame(root, padding = 10)
frame.grid(sticky = "EWNS")

result_box = tkinter.Text(frame)
result_box.grid(column = 0, row = 0, columnspan = 2)

message = "test message"
attributes = {
    "version": "1",
    "item_id": "1",
    "location": "Georgia",
    "quantity": "10",
    "transation_datetime": str(datetime.datetime.now(tz=datetime.timezone.utc)),
    "transaction_number": "341",
}

publish_button = tkinter.ttk.Button(frame, text = "Publish", command = lambda: threading.Thread(target = lambda: run_publish(message, attributes)).start())
publish_button.grid(column = 0, row = 1, ipady = 25, pady = 5, sticky = "EWNS")

clear_button = tkinter.ttk.Button(frame, text = "Clear", command = clear_text)
clear_button.grid(column = 1, row = 1, ipady = 25, pady = 5, sticky = "EWNS")

root.update()
root.mainloop()
