import logging

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='a',
    filename='/data/log.log',
    encoding='utf-8'
)