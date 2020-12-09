# This script is a convenience shim that clones the [EXAMPLE] and
# [EXAMPLE-public-access] sections from samconfig.toml, changes the string
# "EXAMPLE" to a new environment name the user specifies, and writes the
# resulting toml sections to stdout. It can safely be used to append
# (`>>samconfig.toml`) to the config file, as the file is read and parsed
# before any output is produced hence there's no race condition. It doesn't
# modify any files itself.
#
# Invoke it like this:
#
# $ NEW_ENV_NAME=myenv python samconfig.toml.d/new-dev-env.py >>samconfig.toml

from tomlkit.toml_file import TOMLFile
import os
import re

env_name = os.environ["NEW_ENV_NAME"]
t = TOMLFile("samconfig.toml").read()

print()
print(f"[{env_name}]")
print(re.sub("EXAMPLE", env_name, t.item("EXAMPLE").as_string()))
print(re.sub("EXAMPLE", env_name, t.item("EXAMPLE-public-access").as_string()))
