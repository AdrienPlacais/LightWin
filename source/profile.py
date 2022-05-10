#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 10 11:26:25 2022.

@author: placais
"""
import cProfile
import pstats

import os
import accelerator as acc

FILEPATH = os.path.abspath(
    "../data/faultcomp22/working/MYRRHA_Transi-100MeV.dat"
)
linac = acc.Accelerator(FILEPATH, "Working")

cProfile.runctx("linac.compute_transfer_matrices()", globals(), locals(),
                "Profile.prof")
s = pstats.Stats("Profile.prof")
s.strip_dirs().sort_stats("time").print_stats()