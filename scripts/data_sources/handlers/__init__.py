# -*- coding: utf-8 -*-
"""
VertiFlow API Handlers - Connecteurs pour APIs externes
"""
from .rte_eco2mix_handler import RTEECO2MixHandler
from .electricity_maps_handler import ElectricityMapsHandler
from .openaq_handler import OpenAQHandler
from .openfarm_handler import OpenFarmHandler
from .fao_fpma_handler import FAOFPMAHandler

__all__ = [
    "RTEECO2MixHandler",
    "ElectricityMapsHandler",
    "OpenAQHandler",
    "OpenFarmHandler",
    "FAOFPMAHandler",
]
