# Python Pub/Sub Demo

## Setup

1. Set up the gcloud CLI: https://cloud.google.com/sdk/docs/install.

2. Set up ADC gcloud authentication: https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment.

3. Run `setup_venv.sh` and `setup_config.sh`.

    On Windows you may need to run the commands from this script individually.

4. Fill out the generated `config.env` file. Values with spaces may need to be wrapped in double quotes.

    `topic` is the topic name in Google Pub/Sub.

    `subscription_id` is the subscription name in Google Pub/Sub.

## Usage

1. Run `run_test_pub.sh` and `run_test_sub.sh` at the same time (two separate terminals).

2. Press `Subscribe` on the ui of `test_sub.py` to connect the subscriber.

3. Press `Publish` on the ui of `test_pub.py` to send a message.

    The `Message ID`, `Item ID`, `Location`, and `Quantity` fields in the publisher can be edited before publishing.

4. Once the subscriber receives a message, filtering and sorting can be done.

    Left click on the column headers to sort the columns ascending or descending.

    Right click on the column headers to open the filter dialog. Fill in any filtering information desired in the dialog.

    Boolean values can be sorted to show or hide `True` or `False`. Integers can be sorted with a min-max range. Strings can be filtered with regex matches (partial matches are used, append your query with `^` and prepend your query with `$` to only accept an exact match).
