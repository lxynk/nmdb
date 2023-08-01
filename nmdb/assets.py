from pathlib import Path

from clld.web.assets import environment

import nmdb


environment.append_path(
    Path(nmdb.__file__).parent.joinpath('static').as_posix(),
    url='/nmdb:static/')
environment.load_path = list(reversed(environment.load_path))
