import configparser
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

config = configparser.ConfigParser()
config_path = os.path.join(BASE_DIR, 'config.ini')
config.read(config_path)
main_cfg = config['declaranet']


