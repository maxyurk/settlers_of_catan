import logging
import time


class ScorePrintingFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith('|')

logging.basicConfig(level=logging.INFO,
                    format='%(relativeCreated)-6d | %(levelname)-2s | %(message)s')
logger = logging.getLogger()
logger.addFilter(ScorePrintingFilter())

fileLogger = logging.getLogger('file logger')
fileLogger.addHandler(logging.FileHandler('results_{:.3f}.txt'.format(time.time())))
