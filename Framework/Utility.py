import subprocess
import logging
import textwrap
from threading import Thread
from python_log_indenter import IndentedLoggerAdapter

logger = IndentedLoggerAdapter(logging.getLogger())


def reader(pipe, log_level, log_file=None):
    exception_list = [
        "Processing traces"
    ]

    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                if any(word in line for word in exception_list) or line in ['\n', '\r\n']:
                    logger.debug(line.strip())
                elif "JLSCA" in line:
                    logger.info(line.strip())
                else:
                    logger.log(log_level, line.strip())
                if log_file:
                    log_file.write(line.strip()+'\n')
    except:
        pass


def execute(system_command, log_file_cmd=None):
    """Execute a system command, passing STDOUT and STDERR to logger.

    Source: https://stackoverflow.com/a/4417735/2063031
    """
    logger.add()
    logger.add()
    logger.debug("Calling subprocess with cmd: {}".format(system_command))
    logger.add()
    process = subprocess.Popen(
        system_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if log_file_cmd:
        f = open(log_file_cmd, "w")
        t1 = Thread(target=reader, args=[process.stdout, logging.DEBUG, f])
        t2 = Thread(target=reader, args=[process.stderr, logging.ERROR, f])
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        process.stdout.close()
        return_code = process.wait()
        f.close()
        if return_code:
            raise subprocess.CalledProcessError(return_code, system_command)
    else:
        t1 = Thread(target=reader, args=[process.stdout, logging.DEBUG, None])
        t2 = Thread(target=reader, args=[process.stderr, logging.ERROR, None])
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, system_command)
    logger.sub()
    logger.sub()


class WrappedFixedIndentingLog(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', width=70, indent=4):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.wrapper = textwrap.TextWrapper(width=width, subsequent_indent=' '*indent)

    def format(self, record):
        return self.wrapper.fill(super().format(record))

