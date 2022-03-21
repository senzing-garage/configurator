#! /usr/bin/env python3

# -----------------------------------------------------------------------------
# configurator.py
# -----------------------------------------------------------------------------

# Import from standard library. https://docs.python.org/3/library/

import argparse
import json
import linecache
import logging
import os
import shutil
import signal
import string
import sys
import time
from enum import IntFlag
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen

# Import from https://pypi.org/

from flask import Flask, Response, json
from flask import request as flask_request
from flask import url_for
from flask_api import status

# Import Senzing libraries.

# Determine "Major" version of Senzing SDK.

senzing_sdk_version_major = None

# Import from Senzing.

try:
    from senzing import G2Config, G2ConfigMgr, G2Engine, G2EngineFlags, G2Exception, G2ModuleException
    senzing_sdk_version_major = 3

except:

    # Fall back to pre-Senzing-Python-SDK style of imports.

    try:
        from G2Config import G2Config
        from G2ConfigMgr import G2ConfigMgr
        from G2Engine import G2Engine
        from G2Exception import G2Exception, G2ModuleException

        # Create a class like what is seen in Senzing Version 3.

        class G2EngineFlags(IntFlag):
            G2_EXPORT_DEFAULT_FLAGS = G2Engine.G2_EXPORT_DEFAULT_FLAGS
        senzing_sdk_version_major = 2

    except:
        senzing_sdk_version_major = None

app = Flask(__name__)

__all__ = []
__version__ = "1.1.3"  # See https://www.python.org/dev/peps/pep-0396/
__date__ = '2019-09-06'
__updated__ = '2022-03-21'

SENZING_PRODUCT_ID = "5009"  # See https://github.com/Senzing/knowledge-base/blob/master/lists/senzing-product-ids.md
log_format = '%(asctime)s %(message)s'

# Working with bytes.

KILOBYTES = 1024
MEGABYTES = 1024 * KILOBYTES
GIGABYTES = 1024 * MEGABYTES

# Lists from https://www.ietf.org/rfc/rfc1738.txt

safe_character_list = ['$', '-', '_', '.', '+', '!', '*', '(', ')', ',', '"'] + list(string.ascii_letters)
unsafe_character_list = ['"', '<', '>', '#', '%', '{', '}', '|', '\\', '^', '~', '[', ']', '`']
reserved_character_list = [';', ',', '/', '?', ':', '@', '=', '&']

# The "configuration_locator" describes where configuration variables are in:
# 1) Command line options, 2) Environment variables, 3) Configuration files, 4) Default values

config = {}
configuration_locator = {
    "config_path": {
        "default": "/etc/opt/senzing",
        "env": "SENZING_CONFIG_PATH",
        "cli": "config-path"
    },
    "debug": {
        "default": False,
        "env": "SENZING_DEBUG",
        "cli": "debug"
    },
    "g2_database_url_generic": {
        "default": "sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db",
        "env": "SENZING_DATABASE_URL",
        "cli": "database-url"
    },
    "g2_internal_database": {
        "default": None,
        "env": "SENZING_INTERNAL_DATABASE",
        "cli": "internal-database"
    },
    "host": {
        "default": "0.0.0.0",
        "env": "SENZING_HOST",
        "cli": "host"
    },
    "port": {
        "default": 8253,
        "env": "SENZING_PORT",
        "cli": "port"
    },
    "sleep_time_in_seconds": {
        "default": 0,
        "env": "SENZING_SLEEP_TIME_IN_SECONDS",
        "cli": "sleep-time-in-seconds"
    },
    "subcommand": {
        "default": None,
        "env": "SENZING_SUBCOMMAND",
    },
    "support_path": {
        "default": "/opt/senzing/data",
        "env": "SENZING_SUPPORT_PATH",
        "cli": "support-path"
    }
}

# Enumerate keys in 'configuration_locator' that should not be printed to the log.

keys_to_redact = [
    "g2_database_url_generic",
    "g2_database_url_specific"
]

# Global cached objects

g2_configuration_manager_singleton = None
g2_engine_singleton = None
g2_config_singleton = None

# -----------------------------------------------------------------------------
# Define argument parser
# -----------------------------------------------------------------------------


def get_parser():
    ''' Parse commandline arguments. '''

    subcommands = {
        'service': {
            "help": 'Receive HTTP requests.',
            "arguments": {
                "--config-path": {
                    "dest": "config_path",
                    "metavar": "SENZING_CONFIG_PATH",
                    "help": "Location of Senzing's configuration template. Default: /opt/senzing/g2/data"
                },
                "--database-url": {
                    "dest": "g2_database_url_generic",
                    "metavar": "SENZING_DATABASE_URL",
                    "help": "Information for connecting to database."
                },
                "--debug": {
                    "dest": "debug",
                    "action": "store_true",
                    "help": "Enable debugging. (SENZING_DEBUG) Default: False"
                },
                "--host": {
                    "dest": "host",
                    "metavar": "SENZING_HOST",
                    "help": "Host to listen on. Default: 0.0.0.0"
                },
                "--port": {
                    "dest": "port",
                    "metavar": "SENZING_PORT",
                    "help": "Port to listen on. Default: 8080"
                },
                "--support-path": {
                    "dest": "support_path",
                    "metavar": "SENZING_SUPPORT_PATH",
                    "help": "Location of Senzing's support. Default: /opt/senzing/g2/data"
                },
            },
        },
        'sleep': {
            "help": 'Do nothing but sleep. For Docker testing.',
            "arguments": {
                "--sleep-time-in-seconds": {
                    "dest": "sleep_time_in_seconds",
                    "metavar": "SENZING_SLEEP_TIME_IN_SECONDS",
                    "help": "Sleep time in seconds. DEFAULT: 0 (infinite)"
                },
            },
        },
        'version': {
            "help": 'Print version of configurator.py.',
        },
        'docker-acceptance-test': {
            "help": 'For Docker acceptance testing.',
        },
    }

    parser = argparse.ArgumentParser(prog="configurator.py", description="Perform Senzing configuration. For more information, see https://github.com/Senzing/configurator")
    subparsers = parser.add_subparsers(dest='subcommand', help='Subcommands (SENZING_SUBCOMMAND):')

    for subcommand_key, subcommand_values in subcommands.items():
        subcommand_help = subcommand_values.get('help', "")
        subcommand_arguments = subcommand_values.get('arguments', {})
        subparser = subparsers.add_parser(subcommand_key, help=subcommand_help)
        for argument_key, argument_values in subcommand_arguments.items():
            subparser.add_argument(argument_key, **argument_values)

    return parser

# -----------------------------------------------------------------------------
# Message handling
# -----------------------------------------------------------------------------

# 1xx Informational (i.e. logging.info())
# 3xx Warning (i.e. logging.warning())
# 5xx User configuration issues (either logging.warning() or logging.err() for Client errors)
# 7xx Internal error (i.e. logging.error for Server errors)
# 9xx Debugging (i.e. logging.debug())


MESSAGE_INFO = 100
MESSAGE_WARN = 300
MESSAGE_ERROR = 700
MESSAGE_DEBUG = 900

message_dictionary = {
    "100": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}I",
    "101": "Adding datasource '{0}'",
    "102": "Adding entity type '{0}'",
    "104": "CONFIG_DATA_ID: {0} plus datasources: {1}",
    "105": "CONFIG_DATA_ID: {0} passed validity tests.",
    "292": "Configuration change detected.  Old: {0} New: {1}",
    "293": "For information on warnings and errors, see https://github.com/Senzing/configurator#errors",
    "294": "Version: {0}  Updated: {1}",
    "295": "Sleeping infinitely.",
    "296": "Sleeping {0} seconds.",
    "297": "Enter {0}",
    "298": "Exit {0}",
    "299": "{0}",
    "300": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}W",
    "301": "SYS_CFG.CONFIG_DATA_ID: {0} did not pass initialization validation.",
    "302": "SYS_CFG.CONFIG_DATA_ID: {0} did not pass search validation.",
    "499": "{0}",
    "500": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}E",
    "695": "Unknown database scheme '{0}' in database url '{1}'",
    "696": "Bad SENZING_SUBCOMMAND: {0}.",
    "697": "No processing done.",
    "698": "Program terminated with error.",
    "699": "{0}",
    "700": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}E",
    "701": "Error '{0}' caused by {1} error '{2}'",
    "886": "G2Engine.addRecord() bad return code: {0}; JSON: {1}",
    "888": "G2Engine.addRecord() G2ModuleNotInitialized: {0}; JSON: {1}",
    "889": "G2Engine.addRecord() G2ModuleGenericException: {0}; JSON: {1}",
    "890": "G2Engine.addRecord() Exception: {0}; JSON: {1}",
    "891": "Original and new database URLs do not match. Original URL: {0}; Reconstructed URL: {1}",
    "892": "Could not initialize G2Product with '{0}'. Error: {1}",
    "893": "Could not initialize G2Hasher with '{0}'. Error: {1}",
    "894": "Could not initialize G2Diagnostic with '{0}'. Error: {1}",
    "895": "Could not initialize G2Audit with '{0}'. Error: {1}",
    "896": "Could not initialize G2ConfigMgr with '{0}'. Error: {1}",
    "897": "Could not initialize G2Config with '{0}'. Error: {1}",
    "898": "Could not initialize G2Engine with '{0}'. Error: {1}",
    "899": "{0}",
    "900": "senzing-" + SENZING_PRODUCT_ID + "{0:04d}D",
    "998": "Debugging enabled.",
    "999": "{0}",
}


def message(index, *args):
    index_string = str(index)
    template = message_dictionary.get(index_string, "No message for index {0}.".format(index_string))
    return template.format(*args)


def message_generic(generic_index, index, *args):
    index_string = str(index)
    return "{0} {1}".format(message(generic_index, index), message(index, *args))


def message_info(index, *args):
    return message_generic(MESSAGE_INFO, index, *args)


def message_warning(index, *args):
    return message_generic(MESSAGE_WARN, index, *args)


def message_error(index, *args):
    return message_generic(MESSAGE_ERROR, index, *args)


def message_debug(index, *args):
    return message_generic(MESSAGE_DEBUG, index, *args)


def get_exception():
    ''' Get details about an exception. '''
    exception_type, exception_object, traceback = sys.exc_info()
    frame = traceback.tb_frame
    line_number = traceback.tb_lineno
    filename = frame.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, line_number, frame.f_globals)
    return {
        "filename": filename,
        "line_number": line_number,
        "line": line.strip(),
        "exception": exception_object,
        "type": exception_type,
        "traceback": traceback,
    }

# -----------------------------------------------------------------------------
# Database URL parsing
# -----------------------------------------------------------------------------


def translate(map, astring):
    new_string = str(astring)
    for key, value in map.items():
        new_string = new_string.replace(key, value)
    return new_string


def get_unsafe_characters(astring):
    result = []
    for unsafe_character in unsafe_character_list:
        if unsafe_character in astring:
            result.append(unsafe_character)
    return result


def get_safe_characters(astring):
    result = []
    for safe_character in safe_character_list:
        if safe_character not in astring:
            result.append(safe_character)
    return result


def parse_database_url(original_senzing_database_url):
    ''' Given a canonical database URL, decompose into URL components. '''

    result = {}

    # Get the value of SENZING_DATABASE_URL environment variable.

    senzing_database_url = original_senzing_database_url

    # Create lists of safe and unsafe characters.

    unsafe_characters = get_unsafe_characters(senzing_database_url)
    safe_characters = get_safe_characters(senzing_database_url)

    # Detect an error condition where there are not enough safe characters.

    if len(unsafe_characters) > len(safe_characters):
        logging.error(message_error(730, unsafe_characters, safe_characters))
        return result

    # Perform translation.
    # This makes a map of safe character mapping to unsafe characters.
    # "senzing_database_url" is modified to have only safe characters.

    translation_map = {}
    safe_characters_index = 0
    for unsafe_character in unsafe_characters:
        safe_character = safe_characters[safe_characters_index]
        safe_characters_index += 1
        translation_map[safe_character] = unsafe_character
        senzing_database_url = senzing_database_url.replace(unsafe_character, safe_character)

    # Parse "translated" URL.

    parsed = urlparse(senzing_database_url)
    schema = parsed.path.strip('/')

    # Construct result.

    result = {
        'scheme': translate(translation_map, parsed.scheme),
        'netloc': translate(translation_map, parsed.netloc),
        'path': translate(translation_map, parsed.path),
        'params': translate(translation_map, parsed.params),
        'query': translate(translation_map, parsed.query),
        'fragment': translate(translation_map, parsed.fragment),
        'username': translate(translation_map, parsed.username),
        'password': translate(translation_map, parsed.password),
        'hostname': translate(translation_map, parsed.hostname),
        'port': translate(translation_map, parsed.port),
        'schema': translate(translation_map, schema),
    }

    # For safety, compare original URL with reconstructed URL.

    url_parts = [
        result.get('scheme'),
        result.get('netloc'),
        result.get('path'),
        result.get('params'),
        result.get('query'),
        result.get('fragment'),
    ]
    test_senzing_database_url = urlunparse(url_parts)
    if test_senzing_database_url != original_senzing_database_url:
        logging.warning(message_warning(891, original_senzing_database_url, test_senzing_database_url))

    # Return result.

    return result

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


def get_g2_database_url_specific(generic_database_url):
    ''' Given a canonical database URL, transform to the specific URL. '''

    result = ""
    parsed_database_url = parse_database_url(generic_database_url)
    scheme = parsed_database_url.get('scheme')

    # Format database URL for a particular database.

    if scheme in ['mysql']:
        result = "{scheme}://{username}:{password}@{hostname}:{port}/?schema={schema}".format(**parsed_database_url)
    elif scheme in ['postgresql']:
        result = "{scheme}://{username}:{password}@{hostname}:{port}:{schema}/".format(**parsed_database_url)
    elif scheme in ['db2']:
        result = "{scheme}://{username}:{password}@{schema}".format(**parsed_database_url)
    elif scheme in ['sqlite3']:
        result = "{scheme}://{netloc}{path}".format(**parsed_database_url)
    elif scheme in ['mssql']:
        result = "{scheme}://{username}:{password}@{schema}".format(**parsed_database_url)
    else:
        logging.error(message_error(695, scheme, generic_database_url))

    return result


def get_configuration(args):
    ''' Order of precedence: CLI, OS environment variables, INI file, default. '''
    result = {}

    # Copy default values into configuration dictionary.

    for key, value in list(configuration_locator.items()):
        result[key] = value.get('default', None)

    # "Prime the pump" with command line args. This will be done again as the last step.

    for key, value in list(args.__dict__.items()):
        new_key = key.format(subcommand.replace('-', '_'))
        if value:
            result[new_key] = value

    # Copy OS environment variables into configuration dictionary.

    for key, value in list(configuration_locator.items()):
        os_env_var = value.get('env', None)
        if os_env_var:
            os_env_value = os.getenv(os_env_var, None)
            if os_env_value:
                result[key] = os_env_value

    # Copy 'args' into configuration dictionary.

    for key, value in list(args.__dict__.items()):
        new_key = key.format(subcommand.replace('-', '_'))
        if value:
            result[new_key] = value

    # Add program information.

    result['program_version'] = __version__
    result['program_updated'] = __updated__
    result['senzing_sdk_version_major'] = senzing_sdk_version_major

    # Special case: subcommand from command-line

    if args.subcommand:
        result['subcommand'] = args.subcommand

    # Special case: Change boolean strings to booleans.

    booleans = [
        'debug'
    ]
    for boolean in booleans:
        boolean_value = result.get(boolean)
        if isinstance(boolean_value, str):
            boolean_value_lower_case = boolean_value.lower()
            if boolean_value_lower_case in ['true', '1', 't', 'y', 'yes']:
                result[boolean] = True
            else:
                result[boolean] = False

    # Special case: Change integer strings to integers.

    integers = [
        'sleep_time_in_seconds'
    ]
    for integer in integers:
        integer_string = result.get(integer)
        result[integer] = int(integer_string)

    # Special case: Determine absolute paths.

    paths = [
        'config_path',
        'support_path',
    ]
    for path in paths:
        relative_path = result.get(path)
        if relative_path:
            result[path] = os.path.abspath(relative_path)

    # Special case:  Tailored database URL
    # If requested, prepare internal database.

    if config.get('g2_internal_database'):
        g2_internal_database_path = config.get('g2_internal_database')
        g2_internal_database_directory = os.path.dirname(g2_internal_database_path)

        try:
            os.makedirs(g2_internal_database_directory)
        except FileExistsError:
            pass

        shutil.copyfile("/var/opt/senzing/g2/data/G2C.db", g2_internal_database_path)
        config['g2_database_url_specific'] = "sqlite3://na:na@{0}".format(g2_internal_database_path)
    else:
        result['g2_database_url_specific'] = get_g2_database_url_specific(result.get("g2_database_url_generic"))
    return result


def validate_configuration(config):
    ''' Check aggregate configuration from commandline options, environment variables, config files, and defaults. '''

    user_warning_messages = []
    user_error_messages = []

    # Perform subcommand specific checking.

    subcommand = config.get('subcommand')

    if subcommand in ['service']:

        if not config.get('support_path'):
            user_error_messages.append(message_error(414))

    # Log warning messages.

    for user_warning_message in user_warning_messages:
        logging.warning(user_warning_message)

    # Log error messages.

    for user_error_message in user_error_messages:
        logging.error(user_error_message)

    # Log where to go for help.

    if len(user_warning_messages) > 0 or len(user_error_messages) > 0:
        logging.info(message_info(293))

    # If there are error messages, exit.

    if len(user_error_messages) > 0:
        exit_error(697)


def redact_configuration(config):
    ''' Return a shallow copy of config with certain keys removed. '''
    result = config.copy()
    for key in keys_to_redact:
        try:
            result.pop(key)
        except:
            pass
    return result

# -----------------------------------------------------------------------------
# Class: G2Client
# -----------------------------------------------------------------------------


class G2Client:

    def __init__(self, config, g2_engine, g2_configuration_manager, g2_config):
        self.config = config
        self.g2_config = g2_config
        self.g2_configuration_manager = g2_configuration_manager
        self.g2_engine = g2_engine
        self.senzing_sdk_version_major = config.get("senzing_sdk_version_major")

        # Must run after instance variable are set.

        self.datasources = self.get_datasources()
        self.entity_types = self.datasources.copy()


    def add_datasources(self, datasources):
        ''' Add a data source to G2 configuration. '''

        config_handle = self.get_config_handle()

        # Add data sources to configuration.

        for datasource in datasources:
            self.g2_config.addDataSource(config_handle, datasource)
            logging.info(message_info(101, datasource))

        config_id = self.get_default_config_id()
        configuration_comment = message(104, config_id, datasources)

        # Push configuration to database.

        self.persist_configuration(config_handle, configuration_comment)

    def get_config_handle(self):
        ''' Get configuration handle from new or existing "default" configuration. '''

        # Determine if a default configuration exists.

        config_id_bytearray = bytearray()
        self.g2_configuration_manager.getDefaultConfigID(config_id_bytearray)

        # Find the "config_handle" of the configuration,  creating a new configuration if needed.

        if config_id_bytearray:
            config_id_int = int(config_id_bytearray)
            configuration_bytearray = bytearray()
            self.g2_configuration_manager.getConfig(config_id_int, configuration_bytearray)
            configuration_json = configuration_bytearray.decode()
            config_handle = self.g2_config.load(configuration_json)
        else:
            config_handle = self.g2_config.create()

        return config_handle

    def get_datasources(self):
        ''' Determine datasources already defined. '''

        config_handle = self.get_config_handle()

        # Get list of existing datasources.

        datasources_bytearray = bytearray()
        return_code = self.g2_config.listDataSources(config_handle, datasources_bytearray)
        datasources_dictionary = json.loads(datasources_bytearray.decode())
        return datasources_dictionary.get('DSRC_CODE', [])

    def get_default_config_id(self):
        ''' Get the current configuration id.  SYS_CFG.CONFIG_DATA_ID'''
        configuration_id_bytearray = bytearray()
        self.g2_configuration_manager.getDefaultConfigID(configuration_id_bytearray)
        return configuration_id_bytearray.decode()

    def get_g2_configuration_dictionary(self):
        ''' Construct a dictionary in the form of the old ini files. '''

        result = {
            "PIPELINE": {
                "SUPPORTPATH": self.config.get("support_path"),
                "CONFIGPATH": self.config.get("config_path")
            },
            "SQL": {
                "CONNECTION": self.config.get("g2_database_url_specific"),
            }
        }
        return result

    def get_g2_configuration_json(self):
        ''' Return a JSON string with Senzing configuration. '''
        return json.dumps(self.get_g2_configuration_dictionary())

    def persist_configuration(self, config_handle, configuration_comment=""):
        ''' Save configuration to the Senzing G2 database. '''

        # Get JSON string with new datasource added.

        configuration_bytearray = bytearray()
        return_code = self.g2_config.save(config_handle, configuration_bytearray)
        configuration_json = configuration_bytearray.decode()

        # Add configuration to G2 database SYS_CFG table.

        configuration_id_bytearray = bytearray()
        self.g2_configuration_manager.addConfig(configuration_json, configuration_comment, configuration_id_bytearray)

        # Test configuration.

        is_good_configuration = self.test_configuration(configuration_id_bytearray)
        if not is_good_configuration:
            logging.warning(message_warning(301, configuration_id_bytearray.decode()))
            return

        # Set Default configuration.

        self.g2_configuration_manager.setDefaultConfigID(configuration_id_bytearray)

        # Re-initialize G2 engine.

        self.g2_engine.reinit(configuration_id_bytearray)

    def test_configuration(self, configuration_id):
        result = True

        # Test engine initialization.

        g2_engine_name = "Test g2_engine"
        g2_configuration_json = self.get_g2_configuration_json()
        g2_engine = G2Engine()

        try:
            g2_engine.initWithConfigID(g2_engine_name, g2_configuration_json, configuration_id, self.config.get('debug', False))
        except G2Exception as err:
            result = False
            logging.warning(message_warning(301, g2_configuration_json, err))

        # Test engine search.

        data = {}
        data_as_json = json.dumps(data)
        flags = G2EngineFlags.G2_EXPORT_DEFAULT_FLAGS
        response_bytearray = bytearray()

        try:
            g2_engine.searchByAttributes(data_as_json, flags, response_bytearray)
        except G2Exception as err:
            result = False
            logging.warning(message_warning(302, flags, err))

        # Log a successful result.

        if result:
            logging.info(message_info(105, configuration_id.decode()))

        # Epilog.

        return result

# -----------------------------------------------------------------------------
# Class: G2Initializer
# -----------------------------------------------------------------------------


class G2Initializer:

    def __init__(self, g2_configuration_manager, g2_config):
        self.g2_config = g2_config
        self.g2_configuration_manager = g2_configuration_manager

    def initialize(self):
        ''' Initialize the G2 database. '''

        # Determine of a default/initial G2 configuration already exists.

        default_config_id_bytearray = bytearray()
        try:
            return_code = self.g2_configuration_manager.getDefaultConfigID(default_config_id_bytearray)
        except Exception as err:
            raise Exception("G2ConfigMgr.getDefaultConfigID({0}) failed".format(default_config_id_bytearray)) from err
        if return_code != 0:
            raise Exception("G2ConfigMgr.getDefaultConfigID({0}) return code {1}".format(default_config_id_bytearray, return_code))

        # If a default configuration exists, there is nothing more to do.

        if default_config_id_bytearray:
            return

        # If there is no default configuration, create one in the 'configuration_bytearray' variable.

        config_handle = self.g2_config.create()
        configuration_bytearray = bytearray()
        try:
            return_code = self.g2_config.save(config_handle, configuration_bytearray)
        except Exception as err:
            raise Exception("G2Confg.save({0}, {1}) failed".format(config_handle, configuration_bytearray)) from err
        if return_code != 0:
            raise Exception("G2Confg.save({0}, {1}) return code {2}".format(config_handle, configuration_bytearray, return_code))

        self.g2_config.close(config_handle)

        # Save configuration JSON into G2 database.

        config_comment = "Initial configuration."
        new_config_id = bytearray()
        try:
            return_code = self.g2_configuration_manager.addConfig(configuration_bytearray.decode(), config_comment, new_config_id)
        except Exception as err:
            raise Exception("G2ConfigMgr.addConfig({0}, {1}, {2}) failed".format(configuration_bytearray.decode(), config_comment, new_config_id)) from err
        if return_code != 0:
            raise Exception("G2ConfigMgr.addConfig({0}, {1}, {2}) return code {3}".format(configuration_bytearray.decode(), config_comment, new_config_id, return_code))

        # Set the default configuration ID.

        try:
            return_code = self.g2_configuration_manager.setDefaultConfigID(new_config_id)
        except Exception as err:
            raise Exception("G2ConfigMgr.setDefaultConfigID({0}) failed".format(new_config_id)) from err
        if return_code != 0:
            raise Exception("G2ConfigMgr.setDefaultConfigID({0}) return code {1}".format(new_config_id, return_code))

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------


def create_signal_handler_function(args):
    ''' Tricky code.  Uses currying technique. Create a function for signal handling.
        that knows about "args".
    '''

    def result_function(signal_number, frame):
        logging.info(message_info(298, args))
        sys.exit(0)

    return result_function


def bootstrap_signal_handler(signal, frame):
    sys.exit(0)


def entry_template(config):
    ''' Format of entry message. '''
    debug = config.get("debug", False)
    config['start_time'] = time.time()
    if debug:
        final_config = config
    else:
        final_config = redact_configuration(config)
    config_json = json.dumps(final_config, sort_keys=True)
    return message_info(297, config_json)


def exit_template(config):
    ''' Format of exit message. '''
    debug = config.get("debug", False)
    stop_time = time.time()
    config['stop_time'] = stop_time
    config['elapsed_time'] = stop_time - config.get('start_time', stop_time)
    if debug:
        final_config = config
    else:
        final_config = redact_configuration(config)
    config_json = json.dumps(final_config, sort_keys=True)
    return message_info(298, config_json)


def exit_error(index, *args):
    ''' Log error message and exit program. '''
    logging.error(message_error(index, *args))
    logging.error(message_error(698))
    sys.exit(1)


def exit_silently():
    ''' Exit program. '''
    sys.exit(0)

# -----------------------------------------------------------------------------
# Senzing services.
# -----------------------------------------------------------------------------


def get_g2_configuration_dictionary(config):
    ''' Construct a dictionary in the form of the old ini files. '''
    result = {
        "PIPELINE": {
            "SUPPORTPATH": config.get("support_path"),
            "CONFIGPATH": config.get("config_path")
        },
        "SQL": {
            "CONNECTION": config.get("g2_database_url_specific"),
        }
    }
    return result


def get_g2_configuration_json(config):
    ''' Return a JSON string with Senzing configuration. '''
    return json.dumps(get_g2_configuration_dictionary(config))


def get_g2_config(config, g2_config_name="configurator-G2-config"):
    ''' Get the G2Config resource. '''
    global g2_config_singleton

    if g2_config_singleton:
        return g2_config_singleton

    try:
        g2_configuration_json = get_g2_configuration_json(config)
        result = G2Config()

        # Backport methods from earlier Senzing versions.

        if config.get('senzing_sdk_version_major') == 2:
            result.addDataSource = result.addDataSourceV2
            result.addEntityType = result.addEntityTypeV2
            result.init = result.initV2
            result.listDataSources = result.listDataSourcesV2
            result.listDataSources = result.listDataSourcesV2

        # Initialize G2ConfigMgr.

        result.init(g2_config_name, g2_configuration_json, config.get('debug', False))
    except G2ModuleException as err:
        exit_error(897, g2_configuration_json, err)

    g2_config_singleton = result
    return result


def get_g2_configuration_manager(config, g2_configuration_manager_name="configurator-G2-configuration-manager"):
    ''' Get the G2ConfigMgr resource. '''
    global g2_configuration_manager_singleton

    if g2_configuration_manager_singleton:
        return g2_configuration_manager_singleton

    try:
        g2_configuration_json = get_g2_configuration_json(config)
        result = G2ConfigMgr()

        # Backport methods from earlier Senzing versions.

        if config.get('senzing_sdk_version_major') == 2:
            result.init = result.initV2

        # Initialize G2ConfigMgr.

        result.init(g2_configuration_manager_name, g2_configuration_json, config.get('debug', False))
    except G2ModuleException as err:
        exit_error(896, g2_configuration_json, err)

    g2_configuration_manager_singleton = result
    return result


def get_g2_engine(config, g2_engine_name="configurator-G2-engine"):
    ''' Get the G2Engine resource. '''
    global g2_engine_singleton

    if g2_engine_singleton:
        return g2_engine_singleton

    try:
        g2_configuration_json = get_g2_configuration_json(config)
        result = G2Engine()

        # Backport methods from earlier Senzing versions.

        if config.get('senzing_sdk_version_major') == 2:
            result.init = result.initV2
            result.reinit = result.reinitV2
            result.initWithConfigID = result.initWithConfigIDV2
            result.searchByAttributes = result.searchByAttributesV2

        # Initialize G2Engine.

        result.init(g2_engine_name, g2_configuration_json, config.get('debug', False))
    except G2ModuleException as err:
        exit_error(898, g2_configuration_json, err)

    g2_engine_singleton = result
    return result


def get_g2_client(config):
    ''' Get the G2Client resource. '''

    # Create G2 configuration objects.

    g2_config = get_g2_config(config)
    g2_configuration_manager = get_g2_configuration_manager(config)

    # Initialize G2 database.

    g2_initializer = G2Initializer(g2_configuration_manager, g2_config)
    try:
        g2_initializer.initialize()
    except Exception as err:
        logging.error(message_error(701, err, type(err.__cause__), err.__cause__))

    # Create G2 engine object.

    g2_engine = get_g2_engine(config)

    # Create g2_client object.

    return G2Client(config, g2_engine, g2_configuration_manager, g2_config)

# -----------------------------------------------------------------------------
# Worker functions
# -----------------------------------------------------------------------------


def get_config():
    ''' Singleton pattern for config. '''
    return config


def common_prolog(config):
    ''' Common steps for most do_* functions. '''
    validate_configuration(config)
    logging.info(entry_template(config))

# -----------------------------------------------------------------------------
# Flask @app.routes
# -----------------------------------------------------------------------------


@app.route("/datasources", methods=['GET'])
def http_get_datasources():

    # Create g2_client object.

    config = get_config()
    g2_client = get_g2_client(config)

    # Get results from Senzing G2.

    response = g2_client.get_datasources()

    # Craft the HTTP response.

    response_pretty = json.dumps(response, sort_keys=True)
    response_status = status.HTTP_200_OK
    mimetype = 'application/json'
    return Response(response=response_pretty, status=response_status, mimetype=mimetype)


@app.route("/datasources", methods=['POST'])
def http_post_datasources():

    # Get the HTTP POST body as dictionary.

    payload = flask_request.get_data(as_text=True)
    payload_dictionary = json.loads(payload)

    # Create g2_client object.

    config = get_config()
    g2_client = get_g2_client(config)

    # Determine what new datasources need to be created.

    existing_datasources = g2_client.get_datasources()
    new_datasources = [item for item in payload_dictionary if item not in existing_datasources]
    not_needed_datasources = [item for item in payload_dictionary if item in existing_datasources]

    # Create the new datasources.

    g2_client.add_datasources(new_datasources)

    # Craft the HTTP response.

    response = {
        "existingDatasources": not_needed_datasources,
        "createdDatasources": new_datasources
    }

    response_pretty = json.dumps(response, sort_keys=True)
    response_status = status.HTTP_201_CREATED
    mimetype = 'application/json'
    return Response(response=response_pretty, status=response_status, mimetype=mimetype)

# -----------------------------------------------------------------------------
# do_* functions
#   Common function signature: do_XXX(args)
# -----------------------------------------------------------------------------


def do_docker_acceptance_test(args):
    ''' For use with Docker acceptance testing. '''

    # Get context from CLI, environment variables, and ini files.

    config = get_configuration(args)

    # Prolog.

    logging.info(entry_template(config))

    # Epilog.

    logging.info(exit_template(config))


def do_service(args):
    ''' Run a Flask application to handle HTTP calls. '''

    # Get context from CLI, environment variables, and ini files.

    config = get_configuration(args)
    common_prolog(config)

    host = config.get('host')
    port = config.get('port')
    debug = config.get('debug')

    # Prime the pump.

    handle_post_resolver([])
    g2_engine = get_g2_engine(config)
    g2_engine.primeEngine()

    # Run the service application.

    app.run(host=host, port=port, debug=debug, threaded=False)

    # Epilog.

    logging.info(exit_template(config))


def do_sleep(args):
    ''' Sleep.  Used for debugging. '''

    # Get context from CLI, environment variables, and ini files.

    config = get_configuration(args)

    # Prolog.

    logging.info(entry_template(config))

    # Pull values from configuration.

    sleep_time_in_seconds = config.get('sleep_time_in_seconds')

    # Sleep.

    if sleep_time_in_seconds > 0:
        logging.info(message_info(296, sleep_time_in_seconds))
        time.sleep(sleep_time_in_seconds)

    else:
        sleep_time_in_seconds = 3600
        while True:
            logging.info(message_info(295))
            time.sleep(sleep_time_in_seconds)

    # Epilog.

    logging.info(exit_template(config))


def do_version(args):
    ''' Log version information. '''

    logging.info(message_info(294, __version__, __updated__))

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


if __name__ == "__main__":

    # Configure logging. See https://docs.python.org/2/library/logging.html#levels

    log_level_map = {
        "notset": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "fatal": logging.FATAL,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    log_level_parameter = os.getenv("SENZING_LOG_LEVEL", "info").lower()
    log_level = log_level_map.get(log_level_parameter, logging.INFO)
    logging.basicConfig(format=log_format, level=log_level)
    logging.debug(message_debug(998))

    # Trap signals temporarily until args are parsed.

    signal.signal(signal.SIGTERM, bootstrap_signal_handler)
    signal.signal(signal.SIGINT, bootstrap_signal_handler)

    # Parse the command line arguments.

    subcommand = os.getenv("SENZING_SUBCOMMAND", None)
    parser = get_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        subcommand = args.subcommand
    elif subcommand:
        args = argparse.Namespace(subcommand=subcommand)
    else:
        parser.print_help()
        if len(os.getenv("SENZING_DOCKER_LAUNCHED", "")):
            subcommand = "sleep"
            args = argparse.Namespace(subcommand=subcommand)
            do_sleep(args)
        exit_silently()

    # Catch interrupts. Tricky code: Uses currying.

    signal_handler = create_signal_handler_function(args)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Set global config for use by Flask.

    config = get_configuration(args)

    # Transform subcommand from CLI parameter to function name string.

    subcommand_function_name = "do_{0}".format(subcommand.replace('-', '_'))

    # Test to see if function exists in the code.

    if subcommand_function_name not in globals():
        logging.warning(message_warning(696, subcommand))
        parser.print_help()
        exit_silently()

    # Tricky code for calling function based on string.

    globals()[subcommand_function_name](args)
