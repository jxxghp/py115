# PY115

An API client of 115 cloud storage service.

## Example

```python
import py115
from py115.types import Credentail

# Connect to cloud
cloud = py115.connect(
    credential=Credential(
        uid='', cid='', seid=''
    )
)

# Get storage service
storage = cloud.storage()
# Get file list under root directory
for file in storage.list(dir_id='0'):
    print('File: %r' % file)

# Get offline service
offline = cloud.offline()
# Get task list
for task in offline.list():
    print('Task: %r' % task)
# Add task by download URLs
offline.add_url(
    'magnet:?xt=urn:btih:000123456789abcdef1151150123456789abcdef',
    'ed2k://|file|ED2k-file|115115115|1234567890abcdef1234567890abcdef|/',
    'https://dl.some-server.com/some/file.ext'
)

```