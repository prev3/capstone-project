# Python Pub/Sub Demo

## Setup

1. Set up the gcloud CLI: https://cloud.google.com/sdk/docs/install.

2. Set up ADC gcloud authentication: https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment.

3. Run `setup_venv.sh` and `setup_config.sh`.

    On Windows you may need to run the commands from this script individually.

4. Fill out the generated `config.env` file.

    `topic` is the topic name in Google Pub/Sub.

    `subscription_id` is the subscription name in Google Pub/Sub.

## Usage

1. Run `run_test_pub.sh` and `run_test_sub.sh` at the same time (two separate terminals).

2. Press `Subscribe` on the ui of `test_sub.py`.

3. Press `Publish` on the ui of `test_pub.py`.
