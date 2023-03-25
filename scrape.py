from argparse import ArgumentParser

from glints import Glints


def main():
    parser = ArgumentParser(
        prog="scraping.py",
        description="Scrape jobs with given criteria from Glints.com.",
        epilog="You can pass multiple parameters separated by space for job type and YoE. Example = 'intern fulltime freelance'.",
    )
    parser.add_argument(
        "title",
        help="Job title to be scraped.",
    )
    parser.add_argument(
        "-b",
        "--browser",
        required=True,
        metavar="browser name",
        choices=["chrome", "edge", "firefox", "safari"],
        help="The browser you want to use. Supported arguments = ['chrome', 'edge', 'firefox', 'safari'].",
    )
    parser.add_argument(
        "-t",
        "--type",
        metavar="job type",
        default="intern",
        choices=["intern", "fulltime", "parttime", "freelance"],
        help="What type of job to be scraped. Supported arguments = ['intern', 'fulltime', 'parttime', 'freelance']. Default = intern",
    )
    parser.add_argument(
        "-y",
        "--yoe",
        metavar="years of experience",
        default="<1",
        choices=["<1", "1-3", "3-5", "5-10", "10+"],
        help="YoE(Year of Experience) of the job to be scraped. Supported arguments = ['<1', '1-3', '3-5', '5-10', '10+']. Default = < 1.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="output file path",
        default="output.csv",
        help="Output file path. Supported file type = ['csv', 'xls', 'xlsx', 'json']. Default = output.csv",
    )
    parser.add_argument(
        "-r",
        "--remote",
        action="store_true",
        help="Include this argument if you want to scrape for remote only jobs.",
    )
    args = parser.parse_args()
    title = args.title
    browser = args.browser
    _type = args.type
    yoe = args.yoe
    output = args.output
    remote = args.remote
    if output.split(".")[-1] not in ["csv", "xlsx", "xls", "json"]:
        print(output.split(".")[-1])
        print(f"Unsupported output: {output}")
        return
    scrape = Glints(title, _type, yoe, remote)
    scrape_result = scrape.scrape(browser)
    print("DONE! Saving output...")
    print(scrape.save_output(scrape_result, output))


if __name__ == "__main__":
    main()
