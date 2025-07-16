"""Init module for qtasks."""

from qtasks.version import __version__

from qtasks.qtasks import QueueTasks
from qtasks.routers import Router

from qtasks.utils import shared_task
