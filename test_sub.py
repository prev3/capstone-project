import threading
import tkinter
import tkinter.ttk
import traceback

import dotenv
from google.cloud import pubsub_v1

config = dotenv.dotenv_values("config.env")

keep_subscription_alive = True

def init_subscription() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(config["project_id"], config["subscription_id"]) #`projects/{project_id}/subscriptions/{subscription_id}`

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        result_box.insert(tkinter.END, f"Received {message}.\n")
        message.ack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback = callback)
    result_box.insert(tkinter.END, f"Listening for messages on {subscription_path}..\n")

    with subscriber:
        try:
            while keep_subscription_alive:
                try:
                    streaming_pull_future.result(timeout = 60)
                except TimeoutError:
                    result_box.insert(tkinter.END, "Timeout hit, retrying\n")
        except Exception:
            result_box.insert(tkinter.END, traceback.format_exc())

        result_box.insert(tkinter.END, "Unsubscribing\n")
        streaming_pull_future.cancel()
        streaming_pull_future.result()

def kill_subscription() -> None:
    global keep_subscription_alive
    result_box.insert(tkinter.END, "Unsubscribe Requested, thread will exit after timeout\n")
    keep_subscription_alive = False

def request_thread_run(thread) -> None:
    if init_thread and not init_thread.is_alive():
        thread.start()
    else:
        result_box.insert(tkinter.END, "Declining thread start request thread does not exist or is already running\n")

def clear_text() -> None:
    result_box.delete(0.0, tkinter.END)

root = tkinter.Tk()
root.title("Test Sub")

frame = tkinter.ttk.Frame(root, padding = 10)
frame.grid(sticky = "EWNS")

result_box = tkinter.Text(frame)
result_box.grid(column = 0, row = 0, columnspan = 3)

message = "test message"
test_attribute = "test_attribute"

init_thread = threading.Thread(target = init_subscription, daemon = True)
subscribe_button = tkinter.ttk.Button(frame, text = "Subscribe", command = lambda: request_thread_run(init_thread))
subscribe_button.grid(column = 0, row = 1, ipady = 25, pady = 5, sticky = "EWNS")

unsubscribe_button = tkinter.ttk.Button(frame, text = "Unsubscribe", command = kill_subscription)
unsubscribe_button.grid(column = 1, row = 1, ipady = 25, pady = 5, sticky = "EWNS")

clear_button = tkinter.ttk.Button(frame, text = "Clear", command = clear_text)
clear_button.grid(column = 2, row = 1, ipady = 25, pady = 5, sticky = "EWNS")

root.update()
root.mainloop()
