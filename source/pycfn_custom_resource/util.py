#==============================================================================
# Copyright 2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#==============================================================================

# Changes from original pycfn_custom_resource:
#
#   Changed/updated imports.
#
#   Updated exception syntax for Python 3.

from botocore.vendored.requests.exceptions import ConnectionError, HTTPError, Timeout, SSLError
import logging
import random
import time

log = logging.getLogger()


class RemoteError(IOError):
    retry_modes = frozenset(['TERMINAL', 'RETRIABLE', 'RETRIABLE_FOREVER'])

    def __init__(self, code, msg, retry_mode='RETRIABLE'):
        super(RemoteError, self).__init__(code, msg)
        if not retry_mode in RemoteError.retry_modes:
            raise ValueError("Invalid retry mode: %s" % retry_mode)
        self.retry_mode = retry_mode


def _extract_http_error(resp):
    if resp.status_code == 503:
        retry_mode = 'RETRIABLE_FOREVER'
    elif resp.status_code < 500 and resp.status_code not in (404, 408):
        retry_mode = 'TERMINAL'
    else:
        retry_mode = 'RETRIABLE'

    return RemoteError(resp.status_code, u"HTTP Error %s : %s" % (resp.status_code, resp.text), retry_mode)


def exponential_backoff(max_tries, max_sleep=20):
    """
    Returns a series of floating point numbers between 0 and min(max_sleep, 2^i-1) for i in 0 to max_tries
    """
    return [random.random() * min(max_sleep, (2 ** i - 1)) for i in range(0, max_tries)]


def extend_backoff(durations, max_sleep=20):
    """
    Adds another exponential delay time to a list of delay times
    """
    durations.append(random.random() * min(max_sleep, (2 ** len(durations) - 1)))


def retry_on_failure(max_tries=5, http_error_extractor=_extract_http_error):
    def _decorate(f):
        def _retry(*args, **kwargs):
            durations = exponential_backoff(max_tries)
            for i in durations:
                if i > 0:
                    log.debug(u"Sleeping for %f seconds before retrying", i)
                    time.sleep(i)

                try:
                    return f(*args, **kwargs)
                except SSLError as e:
                    log.exception(u"SSLError")
                    raise RemoteError(None, str(e), retry_mode='TERMINAL')
                except ConnectionError as e:
                    log.exception(u"ConnectionError")
                    last_error = RemoteError(None, str(e))
                except HTTPError as e:
                    last_error = http_error_extractor(e.response)
                    if last_error.retry_mode == 'TERMINAL':
                        raise last_error
                    elif last_error.retry_mode == 'RETRIABLE_FOREVER':
                        extend_backoff(durations)

                    log.exception(last_error.strerror)
                except Timeout as e:
                    log.exception(u"Timeout")
                    last_error = RemoteError(None, str(e))
            else:
                raise last_error
        return _retry
    return _decorate
