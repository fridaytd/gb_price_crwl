from seleniumbase import SB

from app.processes import run
from app import logger, config
from app.sheet.models import RowRun


def run_in_loop(sb):
    run_indexes = RowRun.get_run_indexes(
        sheet_id=config.SPREADSHEET_KEY, sheet_name=config.SHEET_NAME, col_index=1
    )
    logger.info(f"Run indexes: {run_indexes}")
    for index in run_indexes:
        try:
            run(sb, index)
        except Exception as e:
            logger.exception(e)


def main():
    with SB(uc=True, locale="en", disable_js=True, headless=True) as sb:
        url = "https://gameboost.com/"
        sb.activate_cdp_mode(url)
        while True:
            try:
                run_in_loop(sb)
            except Exception as e:
                logger.exception(e)


if __name__ == "__main__":
    main()
