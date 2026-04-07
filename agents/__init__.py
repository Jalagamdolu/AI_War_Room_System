"""
agents package
--------------
Exports all war-room agents for external consumption.
"""

from agents.data_analyst_agent import run as run_data_analyst
from agents.marketing_agent import run as run_marketing
from agents.product_manager_agent import run as run_product_manager
from agents.critic_agent import run as run_critic
from agents.evaluator_agent import run as run_evaluator

__all__ = [
    "run_data_analyst",
    "run_marketing",
    "run_product_manager",
    "run_critic",
    "run_evaluator",
]
