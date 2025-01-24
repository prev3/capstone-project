python -m venv .env
source .env/bin/activate
python -m pip install google-cloud-pubsub python-dotenv
cp config_env_template.env config.env
