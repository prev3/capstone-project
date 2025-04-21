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

active_filter = {
    "int": None,
    "str": None,
    "bool": None,
}

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

def clear_log() -> None:
    result_box.delete(0.0, tkinter.END)

def reset_treeview() -> None:
    database_treeview.delete(*database_treeview.get_children())
    insert_treeview_data(database_treeview)

def insert_treeview_data(database_treeview: tkinter.ttk.Treeview) -> None:
    (database_connection, database_cursor) = get_database_cursor()
    treeview_data = database_cursor.execute("SELECT * FROM messages").fetchall()
    for database_treeview_value in treeview_data:
        value_tags = ["duplicate"] if database_treeview_value[-1] else []
        database_treeview.insert("", "end", text = "1", values = database_treeview_value, tags = value_tags)

def sort_treeview(treeview: tkinter.ttk.Treeview, column_name: str, descending: bool) -> None:
    data = [(treeview.set(item, column_name), item) for item in treeview.get_children("")]

    i = 0
    while i < len(data):
        if data[i][0].isdigit():
            data[i] = (int(data[i][0]), data[i][1])
        i += 1

    data.sort(reverse = descending)
    for index, (_, item) in enumerate(data):
        treeview.move(item, "", index)
    treeview.heading(column_name, command = lambda: sort_treeview(treeview, column_name, not descending))

def reset_filter() -> None:
    active_filter = {
        "int": None,
        "str": None,
        "bool": None,
    }

def show_filter_menu(event: tkinter.Event) -> None:
    column_number_str = database_treeview.identify_column(event.x)
    row_number_str = database_treeview.identify_row(event.y) # empty string if in header
    print(column_number_str, row_number_str)
    if len(row_number_str) == 0:
        filter_dialog(column_number_str)

column_types = {
    "#1": int,
    "#2": int,
    "#3": int,
    "#4": str,
    "#5": int,
    "#6": str,
    "#7": int,
    "#8": bool,
}

def filter_dialog(column_number_str) -> None:
    column_type = column_types[column_number_str]
    print(column_number_str, column_type)
    dialog = tkinter.Toplevel()
    dialog.wm_title("Window")

    rows_used = 0

    if column_type == int:
        int_min_label = tkinter.Label(dialog, text = "Min:")
        int_min_label.grid(column = 0, row = 0, ipady = 0, pady = 5, sticky = "EWNS")
        int_min_entry = tkinter.Entry(dialog)
        int_min_entry.insert(0, "")
        int_min_entry.grid(column = 1, row = 0, ipady = 0, pady = 5, sticky = "EWNS")

        int_max_label = tkinter.Label(dialog, text = "Max:")
        int_max_label.grid(column = 0, row = 1, ipady = 0, pady = 5, sticky = "EWNS")
        int_max_entry = tkinter.Entry(dialog)
        int_max_entry.insert(0, "")
        int_max_entry.grid(column = 1, row = 1, ipady = 0, pady = 5, sticky = "EWNS")

        rows_used = 2

        filter_button = tkinter.ttk.Button(dialog, text="Filter", command=lambda: apply_filter_int(dialog, column_number_str, int_min_entry.get(), int_max_entry.get()))
        filter_button.grid(row=rows_used, column=0)

    elif column_type == str:
        regex_query_label = tkinter.Label(dialog, text = "Regex:")
        regex_query_label.grid(column = 0, row = 0, ipady = 0, pady = 5, sticky = "EWNS")
        regex_query_entry = tkinter.Entry(dialog)
        regex_query_entry.insert(0, "")
        regex_query_entry.grid(column = 1, row = 0, ipady = 0, pady = 5, sticky = "EWNS")

        rows_used = 1

        filter_button = tkinter.ttk.Button(dialog, text="Filter", command=lambda: apply_filter_str(dialog, column_number_str, regex_query_entry.get()))
        filter_button.grid(row=rows_used, column=0)

    elif column_type == bool:
        true_button_result = tkinter.IntVar()
        true_button = tkinter.Checkbutton(dialog, text="True", variable=true_button_result)
        true_button.grid(column = 0, row = 0, ipady = 0, pady = 5, sticky = "EWNS")

        false_button_result = tkinter.IntVar()
        false_button = tkinter.Checkbutton(dialog, text="False", variable=false_button_result)
        false_button.grid(column = 0, row = 1, ipady = 0, pady = 5, sticky = "EWNS")

        rows_used = 2

        filter_button = tkinter.ttk.Button(dialog, text="Filter", command=lambda: apply_filter_bool(dialog, column_number_str, true_button_result, false_button_result))
        filter_button.grid(row=rows_used, column=0)

    cancel_button = tkinter.ttk.Button(dialog, text="Cancel", command=dialog.destroy)
    cancel_button.grid(row=rows_used, column=1)

def apply_filter_int(dialog, column_number_str, int_min, int_max):
    dialog.destroy()

def apply_filter_str(dialog, column_number_str, regex_string):
    dialog.destroy()

def apply_filter_bool(dialog, column_number_str, true_filter, false_filter):
    dialog.destroy()

root = tkinter.Tk()
root.title("Test Sub")

frame = tkinter.ttk.Frame(root, padding = 10)
frame.grid(sticky = "EWNS")

treeview_frame = tkinter.ttk.Frame(frame)
treeview_frame.grid(columnspan = 4, sticky = "EWNS")

treeview_columns = ["message_id", "version", "item_id", "location", "quantity", "transaction_datetime", "transation_number", "duplicate"]
database_treeview = tkinter.ttk.Treeview(treeview_frame, columns = treeview_columns, show = "headings")
for i, treeview_column in enumerate(treeview_columns):
    database_treeview.column("#" + str(i + 1), width = len(treeview_column) * 10)
    database_treeview.heading(treeview_column, text = treeview_column.replace("_", " ").title(), command = lambda column = treeview_column: sort_treeview(database_treeview, column, False))
    database_treeview.bind("<Button-3>", show_filter_menu)
database_treeview.grid(column = 0, row = 0, sticky = "EWNS")
insert_treeview_data(database_treeview)
database_treeview.tag_configure("duplicate", background="yellow")

treeview_scrollabar = tkinter.ttk.Scrollbar(treeview_frame, orient = "vertical", command = database_treeview.yview)
treeview_scrollabar.grid(column = 1, row = 0, sticky = "EWNS")
database_treeview.configure(yscrollcommand = treeview_scrollabar.set)

result_box = tkinter.Text(frame, height = 5)
result_box.grid(column = 0, row = 1, columnspan = 3, sticky = "EWNS")

init_thread = threading.Thread(target = init_subscription, daemon = True)
subscribe_button = tkinter.ttk.Button(frame, text = "Subscribe", command = lambda: request_thread_run(init_thread))
subscribe_button.grid(column = 0, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

unsubscribe_button = tkinter.ttk.Button(frame, text = "Unsubscribe", command = kill_subscription)
unsubscribe_button.grid(column = 1, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

clear_log_button = tkinter.ttk.Button(frame, text = "Clear Log", command = clear_log)
clear_log_button.grid(column = 2, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

reset_view_button = tkinter.ttk.Button(frame, text = "Reset View", command = reset_treeview)
reset_view_button.grid(column = 3, row = 2, ipady = 25, pady = 5, sticky = "EWNS")

root.update()
root.mainloop()
