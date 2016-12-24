import click
from pdfquery import PDFQuery


def get_header_name(pdf):
    page_index = 0
    page_selector = 'LTPage[page_index="{}"]'.format(page_index)
    elem_selector = 'LTTextBoxHorizontal'
    bbox = (0, 794.732, 594, 806.334)
    bbox_selector = 'in_bbox("{},{},{},{}")'.format(*bbox)
    selector = "{} {}:{}".format(page_selector, elem_selector, bbox_selector)
    name_text = pdf.pq(selector)[0].text
    return(name_text.strip())

@click.command()
@click.argument('pdf_path', type=click.Path(exists=True, dir_okay=False))
def cli(pdf_path):
    pdf = PDFQuery(pdf_path)
    pdf.load()
    print(get_header_name(pdf))


if __name__ == '__main__':
    cli()
