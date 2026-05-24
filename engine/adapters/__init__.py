from .greenhouse import fetch as fetch_greenhouse
from .lever import fetch as fetch_lever
from .ashby import fetch as fetch_ashby

ADAPTERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}
