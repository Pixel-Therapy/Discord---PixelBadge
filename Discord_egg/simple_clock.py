# Adapted from PrettyClock
# Thx to Sebastius

import rgb, machine, time
from default_icons import animation_connecting_wifi, icon_no_wifi
import config
from util import connect_wifi

connect_wifi()
rgb.clear()
rtc = machine.RTC()
timezone = machine.nvs_getstr("system", "timezone")
if timezone is None:
    timezone = "CET-1CEST-2,M3.5.0/02:00:00,M10.5.0/03:00:00"
machine.RTC().timezone(timezone)

while rtc.now()[0] == 1970:
    rtc.ntp_sync("pool.ntp.org")

tmold = 70
rgb.background((0, 0, 0))
rgb.clear()
rgb.framerate(1)

# main loop
def update_clock(force_draw=False):
    """
    Args:
        force_draw (bool, optional): redraw regardless of minute change. Defaults to False.
    """
    global tmold
    th = rtc.now()[3]
    tm = rtc.now()[4]
    sth = "%02d" % th
    stm = "%02d" % tm
    if tm != tmold or force_draw:
        rgb.clear()
        rgb.brightness(config.clock_brightness)
        rgb.text(sth, config.clock_color, (3, 0))
        rgb.text(stm, config.clock_color, (18, 0))
        tmold = tm


if __name__ == "__main__":
    update_clock(True)
    while True:
        update_clock()
        time.sleep(1)
