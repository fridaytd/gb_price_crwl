from seleniumbase import SB

from app.processes import run

with SB(uc=True, locale="en", disable_js=True, headless=True) as sb:
    url = "https://gameboost.com/"
    sb.activate_cdp_mode(url)

    run(sb, 4)
