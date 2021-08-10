
#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Josh Johnson <josh@joshajohnson.com>
# Copyright (c) 2021 Greg Davill <greg.davill@gmail.com>
#
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import argparse

from migen import *
from migen.genlib.misc import WaitTimer
from migen.genlib.resetsync import AsyncResetSynchronizer

from platform import ecp5_mini

from litehyperbus.core.hyperbus import HyperRAM

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, with_usb_pll=True):
        self.rst = Signal()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys = ClockDomain()

        # # #

        # Clk / Rst
        clk16 = platform.request("clk16")
        rst_n = platform.request("usr_btn", loose=True)
        if rst_n is None: rst_n = 1

        # Power on reset
        por_count = Signal(12, reset=2**12-1)
        por_done  = Signal()
        self.comb += self.cd_por.clk.eq(clk16)
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # PLL
        self.submodules.pll = pll = ECP5PLL()
        self.comb += pll.reset.eq(~por_done | ~rst_n | self.rst)
        pll.register_clkin(clk16, 16e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

        # USB PLL
        if with_usb_pll:
            self.clock_domains.cd_usb_12 = ClockDomain()
            self.clock_domains.cd_usb_48 = ClockDomain()
            usb_pll = ECP5PLL()
            self.submodules += usb_pll
            self.comb += usb_pll.reset.eq(~por_done)
            usb_pll.register_clkin(clk16, 16e6)
            usb_pll.create_clkout(self.cd_usb_48, 48e6)
            usb_pll.create_clkout(self.cd_usb_12, 12e6)

        # FPGA Reset (press usr_btn for 1 second to fallback to bootloader)
        reset_timer = WaitTimer(int(16e6))
        reset_timer = ClockDomainsRenamer("por")(reset_timer)
        self.submodules += reset_timer
        self.comb += reset_timer.wait.eq(~rst_n)
        self.comb += platform.request("rst_n").eq(~reset_timer.done)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    mem_map = {
        "hyperram": 0x20000000,
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, device="12F", sys_clk_freq=int(48e6), toolchain="trellis", **kwargs):
        platform = ecp5_mini.Platform(device=device, toolchain=toolchain)

        # Serial -----------------------------------------------------------------------------------
        kwargs["uart_name"] = "usb_acm" # Enforce UART to USB-ACM
        # Defaults to USB ACM through ValentyUSB.
        os.system("git clone https://github.com/litex-hub/valentyusb -b hw_cdc_eptri")
        sys.path.append("valentyusb")
        

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on ECP5 Mini",
            ident_version  = True,
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # HyperRam ---------------------------------------------------------------------------------
        self.submodules.hyperram = HyperRAM(platform.request("hyperram"))
        self.register_mem("hyperram", self.mem_map["hyperram"], self.hyperram.bus, 8*1024*1024)

        # Leds -------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)
        self.add_csr("leds")

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on ECP5 Mini")
    parser.add_argument("--build",              action="store_true", help="Build bitstream")
    parser.add_argument("--load",               action="store_true", help="Load bitstream")
    parser.add_argument("--toolchain",          default="trellis",   help="FPGA toolchain: trellis (default) or diamond")
    parser.add_argument("--device",             default="12F",       help="ECP5 device (default: 12F)")
    parser.add_argument("--sys-clk-freq",       default=48e6,        help="System clock frequency (default: 48Mhz)")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(toolchain=args.toolchain,
        device       = args.device,
        sys_clk_freq = int(float(args.sys_clk_freq)),
        **soc_core_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()