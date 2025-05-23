"""Define general-use fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def raw_ads_filecontent() -> str:
    """Return the expected content of :file:`ads.dat` as fixture."""
    return """\
;------------------------------------
; TraceWin Version: 2.23.1.3
; OS: Win10 (64-bit)
; Date: Fri Oct 20 14:31:57 2023
; User: FBOULY
; Computer: LPSC5003W
;------------------------------------

FIELD_MAP_PATH field_maps_1D


; Section #1

LATTICE 10 0
FREQ 352.2
; Lattice #1
QUAD 200 5.66763 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -5.67474 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 153.171 30 0 1.55425 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 156.892 30 0 1.55425 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #2
QUAD 200 5.77341 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -5.77854 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 161.635 30 0 1.56423 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 165.455 30 0 1.56423 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #3
QUAD 200 5.88548 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -5.8887 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 170.302 30 0 1.58277 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 174.225 30 0 1.58277 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #4
QUAD 200 6.00491 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.00611 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 179.184 30 0 1.61061 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -176.785 30 0 1.61061 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #5
QUAD 200 6.13264 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.13169 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -171.709 30 0 1.64871 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -167.564 30 0 1.64871 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #6
QUAD 200 6.2697 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.2664 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -162.363 30 0 1.69848 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -158.097 30 0 1.69848 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #7
QUAD 200 6.41732 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.41151 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -152.764 30 0 1.76166 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -148.37 30 0 1.76166 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #8
QUAD 200 6.57683 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.56822 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -142.895 30 0 1.84058 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -138.365 30 0 1.84058 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #9
QUAD 200 6.75 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.73832 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -132.739 30 0 1.93836 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -128.062 30 0 1.93836 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #10
QUAD 200 6.93885 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -6.92363 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -122.274 30 0 2.05912 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -117.441 30 0 2.05912 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #11
QUAD 200 7.14589 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -7.12669 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -111.478 30 0 2.20843 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -106.476 30 0 2.20843 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #12
QUAD 200 7.37411 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -7.35026 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -100.324 30 0 2.39391 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -95.1385 30 0 2.39391 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #13
QUAD 200 7.62724 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -7.59793 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -88.7799 30 0 2.6261 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -83.3954 30 0 2.6261 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #14
QUAD 200 7.91009 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -7.8743 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -76.8119 30 0 2.92002 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -71.2082 30 0 2.92002 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #15
QUAD 200 8.14173 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.10217 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -64.4418 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -59.0461 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #16
QUAD 200 8.33793 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.29682 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -52.5802 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -47.6137 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #17
QUAD 200 8.53248 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.4903 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -41.6677 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -37.1053 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #18
QUAD 200 8.72541 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.68258 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -31.6441 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -27.4559 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #19
QUAD 200 8.91692 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.87376 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -22.4407 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -18.595 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #20
QUAD 200 9.10703 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -9.06375 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -13.9863 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -10.4517 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #21
QUAD 200 9.29547 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -9.25235 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -6.2112 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 -2.95793 30 0 3.03726 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0
; Lattice #22
QUAD 200 8.6485 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
QUAD 200 -8.72307 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 589.42 30 0 0 0
FIELD_MAP 100 415.16 -2.9999 30 0 2.90098 0 0 Simple_Spoke_1D 0
DRIFT 264.84 30 0 0 0
FIELD_MAP 100 415.16 3.8378 30 0 2.90005 0 0 Simple_Spoke_1D 0
DRIFT 505.42 30 0 0 0
DRIFT 150 100 0 0 0


; Section #2

LATTICE 10 0
FREQ 352.2
; Lattice #23
QUAD 300 5.15203 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.13556 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 151.401 40 0 4.2 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 158 40 0 4.2 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #24
QUAD 300 5.13243 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.13255 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 163.76 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 169.702 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #25
QUAD 300 5.18235 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.17568 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 176.595 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -177.801 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #26
QUAD 300 5.21587 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.2037 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -171.343 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -166.12 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #27
QUAD 300 5.2326 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.2162 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -160.132 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -155.306 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #28
QUAD 300 5.23241 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.21293 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -149.791 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -145.357 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #29
QUAD 300 5.21573 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.19414 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -140.299 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -136.239 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #30
QUAD 300 5.18274 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.15986 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -131.611 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -127.898 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #31
QUAD 300 5.13384 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.11034 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -123.666 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -120.272 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #32
QUAD 300 5.06951 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -5.04588 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -116.4 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -113.293 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #33
QUAD 300 4.99017 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.9668 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -109.747 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -106.9 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #34
QUAD 300 4.89615 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.87333 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -103.645 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -101.031 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #35
QUAD 300 4.78793 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.7659 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -98.0371 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -95.6314 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #36
QUAD 300 4.66617 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.64505 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -92.8715 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -90.6522 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #37
QUAD 300 4.60135 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.58096 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -88.1015 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -86.0491 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #38
QUAD 300 4.52845 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.50885 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -83.686 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -81.7832 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #39
QUAD 300 4.44756 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.42879 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -79.5883 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -77.8199 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #40
QUAD 300 4.35888 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.34099 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -75.7763 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -74.1289 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #41
QUAD 300 4.26274 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.24573 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -72.2216 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -70.6834 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #42
QUAD 300 4.54689 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -4.52923 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -68.8991 40 0 4.45899 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -67.4597 40 0 4.45899 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0
; Lattice #43
QUAD 300 3.69404 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 300 -3.70134 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 642.1 40 0 0 0
FIELD_MAP 100 636 -68 40 0 4.48 0 0 Double_spoke 0
DRIFT 464.2 40 0 0 0
FIELD_MAP 100 636 -68 40 0 4.47996 0 0 Double_spoke 0
DRIFT 552.1 40 0 0 0
DRIFT 150 100 0 0 0


; Section #3

LATTICE 14 0
FREQ 704.4
; Lattice #44
QUAD 400 3.9645 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -3.91645 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -109.097 45 0 0.803979 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -106.695 45 0 0.84498 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -120 45 0 1.29932 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -116.82 45 0 1.29998 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #45
QUAD 400 4.62544 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -4.63099 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -105.774 45 0 1.71708 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -104.185 45 0 1.71708 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -102.637 45 0 1.71708 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -101.127 45 0 1.71708 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #46
QUAD 400 5.38291 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -5.39062 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -98.9401 45 0 2.69547 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -96.4561 45 0 2.69547 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -94.0397 45 0 2.69547 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -91.6845 45 0 2.69547 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #47
QUAD 400 5.68269 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -5.68983 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -88.3 45 0 3.80457 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -84.8365 45 0 3.80457 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -81.4769 45 0 3.80457 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -78.2103 45 0 3.80457 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #48
QUAD 400 5.85187 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -5.85552 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -73.6469 45 0 4.03215 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -70.0732 45 0 4.03215 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -66.616 45 0 4.03215 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -63.2638 45 0 4.03215 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #49
QUAD 400 6.02053 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.0201 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -58.5853 45 0 4.3369 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -54.8906 45 0 4.3369 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -51.327 45 0 4.3369 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -47.8825 45 0 4.3369 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #50
QUAD 400 6.20912 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.2039 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -43.0766 45 0 4.74254 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -39.2479 45 0 4.74254 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -35.5678 45 0 4.74254 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -32.0232 45 0 4.74254 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #51
QUAD 400 6.42204 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.41104 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -27.0753 45 0 5.28486 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -23.0966 45 0 5.28486 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -19.2877 45 0 5.28486 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -15.6342 45 0 5.28486 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #52
QUAD 400 6.66488 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.64677 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 -10.5267 45 0 6.01926 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -6.37824 45 0 6.01926 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 -2.42592 45 0 6.01926 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 1.347 45 0 6.01926 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #53
QUAD 400 5.87516 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
; DRIFT 200 100 0 0 0
QUAD 400 -5.83345 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 6.59 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 10.715 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 14.629 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 18.349 45 0 6.67386 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #54
QUAD 400 6.16521 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
; DRIFT 200 100 0 0 0
QUAD 400 -6.09335 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 23.431 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 27.073 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 30.528 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 33.812 45 0 6.67386 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #55
QUAD 400 6.13033 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
; DRIFT 200 100 0 0 0
QUAD 400 -6.10707 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 38.306 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 41.514 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 44.56 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 47.457 45 0 6.67386 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #56
QUAD 400 6.77629 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.74251 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 51.43 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 54.259 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 56.948 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 59.507 45 0 6.67386 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0
; Lattice #57
QUAD 400 6.56535 100 0 0 0 0 0 0
DRIFT 200 100 0 0 0
QUAD 400 -6.53244 100 0 0 0 0 0 0
DRIFT 150 100 0 0 0
DRIFT 385 45 0 0 0
FIELD_MAP 100 1050 63.028 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 65.528 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 67.909 45 0 6.67386 0 0 beta065_1D 0
DRIFT 130 45 0 0 0
FIELD_MAP 100 1050 70.177 45 0 6.67386 0 0 beta065_1D 0
DRIFT 445 45 0 0 0
DRIFT 150 100 0 0 0

END
"""


@pytest.fixture
def ads_dat_path(tmp_path: Path, raw_ads_filecontent: str) -> Path:
    """Write example content to a temporary file."""
    ads_path = tmp_path / "ads.dat"
    ads_path.write_text(raw_ads_filecontent, encoding="utf-8")
    return ads_path
