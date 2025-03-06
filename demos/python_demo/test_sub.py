import json
import sqlite3
import threading
import tkinter
import tkinter.ttk
import traceback

import dotenv
from google.cloud import pubsub_v1

config = dotenv.dotenv_values("config.env")

keep_subscription_alive = True

DATABASE_TABLE_NAME = "messages"

def log_debug(message: str) -> None:
    print(message)  # noqa: T201
    try:
        result_box.insert(tkinter.END, str(message) + "\n")
    except Exception:
        print("Failed to insert message into ui")  # noqa: T201

def get_database_cursor() -> None:
    database_connection = sqlite3.connect("demo.db")
    database_cursor = database_connection.cursor()
    table_check = database_cursor.execute("SELECT name FROM sqlite_master WHERE name='messages'")
    if table_check and not table_check.fetchone():
        database_cursor.execute("CREATE TABLE messages(message_id, version, item_id, location, quantity, transaction_datetime, transation_number, duplicate)")
    return (database_connection, database_cursor)

def init_subscription() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(config["project_id"], config["subscription_id"]) #`projects/{project_id}/subscriptions/{subscription_id}`

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        log_debug(f"Received {message}.")
        message_data = json.loads(message.data)
        message_attributes = message.attributes
        (database_connection, database_cursor) = get_database_cursor()
        duplicate = bool(len(database_cursor.execute("SELECT * FROM messages WHERE message_id=?", [str(message_data["message_id"])]).fetchall()))
        data = [
            message_data["message_id"],
            message_attributes["version"],
            message_data["item_id"],
            message_data["location"],
            message_data["quantity"],
            message_data["transation_datetime"],
            message_data["transaction_number"],
            duplicate,
        ]
        database_cursor.execute("INSERT INTO messages VALUES(?, ?, ?, ?, ?, ?, ?, ?)", data)
        database_connection.commit()
        reset_treeview()
        message.ack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback = callback)
    log_debug(f"Listening for messages on {subscription_path}..")

    with subscriber:
        try:
            while keep_subscription_alive:
                try:
                    streaming_pull_future.result(timeout = 10)
                except TimeoutError:
                    log_debug("Timeout hit, continuing stream if unsubscribe was not requested")
        except Exception:
            log_debug(traceback.format_exc())

        log_debug("Unsubscribing")
        streaming_pull_future.cancel()
        streaming_pull_future.result()
        log_debug("Unsubscribed")

def kill_subscription() -> None:
    global keep_subscription_alive
    log_debug("Unsubscribe Requested, thread will exit after timeout")
    keep_subscription_alive = False

def request_thread_run(thread) -> None:
    if init_thread and not init_thread.is_alive():
        thread.start()
    else:
        log_debug("Declining thread start request thread does not exist or is already running")

def clear_text() -> None:
    result_box.delete(0.0, tkinter.END)

def reset_treeview() -> None:
    database_treeview.delete(*database_treeview.get_children())
    insert_treeview_data(database_treeview)

def insert_treeview_data(treeview: tkinter.ttk.Treeview) -> None:
    (database_connection, database_cursor) = get_database_cursor()
    treeview_data = database_cursor.execute("SELECT * FROM messages").fetchall()
    for database_treeview_value in treeview_data:
        database_treeview.insert("", "end", text = "1", values = database_treeview_value)

def sort_treeview(treeview: tkinter.ttk.Treeview, column_name: str, descending: bool) -> None:
    data = [(treeview.set(item, column_name), item) for item in treeview.get_children("")]
    data.sort(reverse = descending)
    for index, (_, item) in enumerate(data):
        treeview.move(item, "", index)
    treeview.heading(column_name, command = lambda: sort_treeview(treeview, column_name, not descending))

root = tkinter.Tk()
root.title("Test Sub")

frame = tkinter.ttk.Frame(root, padding = 10)
frame.grid(sticky = "EWNS")

treeview_columns = ["message_id", "version", "item_id", "location", "quantity", "transaction_datetime", "transation_number", "duplicate"]
database_treeview = tkinter.ttk.Treeview(frame, columns = treeview_columns, show = "headings")
for i, treeview_column in enumerate(treeview_columns):
    database_treeview.column("#" + str(i + 1), width = len(treeview_column) * 10)
    database_treeview.heading(treeview_column, text = treeview_column.replace("_", " ").title(), command = lambda column = treeview_column: sort_treeview(database_treeview, column, False))
database_treeview.grid(column = 0, row = 0, columnspan = 3)

insert_treeview_data(database_treeview)

result_box = tkinter.Text(frame, height = 5)
result_box.grid(column = 0, row = 1, columnspan = 3, sticky = "EWNS")

init_thread = threading.Thread(target = init_subscription, daemon = True)
subscribe_button = tkinter.ttk.Button(frame, text = "Subscribe", command = lambda: request_thread_run(init_thread))
subscribe_button.grid(column = 0, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

unsubscribe_button = tkinter.ttk.Button(frame, text = "Unsubscribe", command = kill_subscription)
unsubscribe_button.grid(column = 1, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

clear_text_button = tkinter.ttk.Button(frame, text = "Clear Text", command = clear_text)
clear_text_button.grid(column = 2, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

root.update()
root.mainloop()
