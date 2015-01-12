from __future__ import unicode_literals, print_function, division
from .environment import DEPENDENCY_URL
from .environment import PYPI_INDEX_HOST
from .environment import PYPI_INDEX_URL
from .environment import SHARE_DIR
from .environment import DEPENDENCY_DIR
from .environment import DEPENDENCY_INSTALL_DIR
from .environment import PYPI_ARCHIVE_DIR

from .environment import VEIL_ENV_TYPE
from .environment import VEIL_ENV_NAME
from .environment import CURRENT_OS
from .environment import SECURITY_CONFIG_FILE
from .environment import CURRENT_USER
from .environment import CURRENT_USER_GROUP

from .environment import VEIL_HOME
from .environment import VEIL_FRAMEWORK_HOME
from .environment import VEIL_ETC_DIR
from .environment import VEIL_VAR_DIR
from .environment import VEIL_EDITORIAL_DIR
from .environment import VEIL_BUCKETS_DIR
from .environment import VEIL_BUCKET_LOG_DIR
from .environment import VEIL_BUCKET_INLINE_STATIC_FILES_DIR
from .environment import VEIL_BUCKET_CAPTCHA_IMAGE_DIR
from .environment import VEIL_BUCKET_UPLOADED_FILES_DIR
from .environment import VEIL_DATA_DIR
from .environment import VEIL_LOG_DIR
from .environment import BASIC_LAYOUT_RESOURCES

from .environment import VEIL_BACKUP_ROOT

from .environment import VEIL_FRAMEWORK_CODEBASE
from .environment import get_application_codebase
from .environment import get_application_version
from .environment import get_application_sms_whitelist
from .environment import get_application_email_whitelist
from .environment import get_veil_framework_version

from .environment import veil_env
from .environment import veil_host
from .environment import veil_server
from .environment import get_veil_env
from .environment import get_veil_env_deployment_memo
from .environment import list_veil_hosts
from .environment import get_veil_host
from .environment import list_veil_servers
from .environment import get_veil_server
from .environment import get_current_veil_server
