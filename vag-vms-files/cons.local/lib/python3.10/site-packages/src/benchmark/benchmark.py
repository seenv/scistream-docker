import abc
import json
from datetime import datetime

# Abstract base class for logging experiment entries
# abc.ABCMeta is a metaclass that is used to create abstract base classes in Python.
class ExperimentLogger(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def log_iteration(self, experiment_id, iteration, lower_bound, upper_bound, duration, frames_delivered, frames_missed, frame_size, packet_loss, cpu_usage):
        #parameters are specific for throughput
        pass

    @abc.abstractmethod
    def generate_report(self, experiment_id):
        pass
