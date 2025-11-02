"""Init module for qtasks."""

from qtasks.plugins.depends import Depends
from qtasks.qtasks import QueueTasks
from qtasks.routers import AsyncRouter, SyncRouter
from qtasks.utils import shared_task
from qtasks.version import __version__
