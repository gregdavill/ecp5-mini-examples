#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Josh Johnson <josh@joshajohnson.com>
# Copyright (c) 2021 Greg Davill <greg.davill@gmail.com>
#
# SPDX-License-Identifier: BSD-2-Clause

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.dfu import DFUProg

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk16", 0, Pins("B9"),  IOStandard("LVCMOS33")),
    ("rst_n", 0, Pins("R8"), IOStandard("LVCMOS33")),

    # Buttons
    ("usr_btn", 0, Pins("T6"), IOStandard("LVCMOS33")),

    # Leds
    ("user_led", 0, Pins("B1 B2"), IOStandard("LVCMOS33")),
    ("led", 1, Pins("R14 T14 T132 R13 M6 M5 R5 T4"), IOStandard("LVCMOS33")), # Anodes (0 -> 7)
    ("led", 2, Pins("R12 P12 N12"), IOStandard("LVCMOS33")), # Cathodes via FET (R,G,B)

    # HyperRAM
    ("hyperram", 0,
        Subsignal("dq", Pins("A6 C4 A7 B7 A8 B6 D4 A5"), IOStandard("LVCMOS18")),
        Subsignal("rwds", Pins("A4"), IOStandard("LVCMOS18")),
        Subsignal("cs_n", Pins("A3"), IOStandard("LVCMOS18")),
        Subsignal("rst_n", Pins("B4"), IOStandard("LVCMOS18")),
        Subsignal("clk", Pins("A2"), IOStandard("LVCMOS18D")),
        Misc("SLEWRATE=FAST")
    ),

    # USB
    ("usb", 0,
        Subsignal("d_p", Pins("C8")),
        Subsignal("d_n", Pins("C9")),
        Subsignal("pullup", Pins("E8")),
        IOStandard("LVCMOS33")
    ),

    # SPIFlash
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("N8"), IOStandard("LVCMOS33")),
        #Subsignal("clk",  Pins("N9"), IOStandard("LVCMOS33")),
        Subsignal("dq",   Pins("T7 T8 M7 N7"), IOStandard("LVCMOS33")),
    ),

    ("spiflash", 0,
        Subsignal("cs_n", Pins("N8"), IOStandard("LVCMOS33")),
        #Subsignal("clk",  Pins("N9"), IOStandard("LVCMOS33")), # Note: CLK is bound using USRMCLK block
        Subsignal("miso", Pins("T7"), IOStandard("LVCMOS33")),
        Subsignal("mosi", Pins("UT8"), IOStandard("LVCMOS33")),
        Subsignal("wp",   Pins("M7"), IOStandard("LVCMOS33")),
        Subsignal("hold", Pins("N7"), IOStandard("LVCMOS33")),
    ),

    # SDCard
    ("spisdcard", 0,
        Subsignal("clk",  Pins("C10")),
        Subsignal("mosi", Pins("B10"), Misc("PULLMODE=UP")),
        Subsignal("cs_n", Pins("A11"), Misc("PULLMODE=UP")),
        Subsignal("miso", Pins("A10"), Misc("PULLMODE=UP")),
        Misc("SLEWRATE=FAST"),
        IOStandard("LVCMOS33"),
    ),

    ("sdcard", 0,
        Subsignal("clk",  Pins("C10")),
        Subsignal("cmd",  Pins("D10"), Misc("PULLMODE=UP")),
        Subsignal("data", Pins("B10 A10 B11 A11"), Misc("PULLMODE=UP")),
        IOStandard("LVCMOS33"), Misc("SLEWRATE=FAST")
    ),
]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
    # PMOD signal number:
    #          1   2   3   4   7   8   9   10
    ("PMODA", "R15 P16 M13 L13 T15 R16 N14 L12"),
    ("PMODB", "L16 H12 G12 J16 L15 H13 G13 J15"),
    ("PMODC", "G16 F16 D16 C16 H15 G15 E15 C15"),
    ("PMODD", "F15 B16 D13 B12 E16 B15 E13 C12"),
    ("PMODE", "F2  C1  C3  E3  E1  C2  D3  F3"),
    ("PMODF", "J1  G1  F1  G5  J2  H2  G2  G4"),
    ("PMODG", "N1  K4  L1  H5  P2  K5  L2  H4"),
    ("PMODH", "R4  P4  R2  P1  T3  R3  T2  R1"),
]
# Platform -----------------------------------------------------------------------------------------

class Platform(LatticePlatform):
    default_clk_name   = "clk16"
    default_clk_period = 1e9/16e6

    def __init__(self, device="12F", toolchain="trellis", **kwargs):
        LatticePlatform.__init__(self, "LFE5U-12F-8CABGA256", io=_io, connectors=_connectors,
            toolchain=toolchain, **kwargs)

    def create_programmer(self):
        return DFUProg(vid="1d50", pid="614b")

    def do_finalize(self, fragment):
        LatticePlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk16", loose=True), 1e9/16e6)
