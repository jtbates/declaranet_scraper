import datetime
from fnmatch import fnmatch
import hashlib
import io
import logging
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from unidecode import unidecode

from . import settings
from .database import Servant, Dependency
from .database import Declaration, decl_type_mapper_es
from .database import get_session, one_or_create, one_like


logger = logging.getLogger('declaranet.web')
#session = get_session()

JSF_URL = 'http://www.servidorespublicos.gob.mx/registro/consulta.jsf'
PDF_URL = 'http://www.servidorespublicos.gob.mx/consulta.pdf'


def get_driver():
    driver = webdriver.PhantomJS()
    return(driver)

#driver = get_driver()


def wait_for_condition(condition_expr, driver, time_to_wait=5):
    t0 = time.clock()
    script = "return {}".format(condition_expr)
    condition = False
    time_remains = True
    while not condition and time_remains:
        condition = driver.execute_script(script)
        if time_to_wait >= 0:
            elapsed = time.clock() - t0
            time_remains = elapsed < time_to_wait


def wait_for_jquery(driver, time_to_wait=1):
    jquery_cond = 'jQuery.active == 0'
    wait_for_condition(jquery_cond, driver=driver,
                       time_to_wait=time_to_wait)


def wait_for_ajax(driver, time_to_wait=5):
    primefaces_cond = 'PrimeFaces.ajax.Queue.isEmpty()'
    wait_for_condition(primefaces_cond, driver=driver,
                       time_to_wait=time_to_wait)
    wait_for_jquery(driver)


def get_jsessionid(driver):
    return(driver.get_cookie('JSESSIONID')['value'])


def get_request_cookies(driver):
    jsessionid = get_jsessionid(driver)
    cookies = dict(JSESSIONID=jsessionid)
    return(cookies)


def get_viewstate(driver):
    input_elem = driver.find_element_by_id('j_id1:javax.faces.ViewState:0')
    return(input_elem.get_attribute('value'))


def load_search_page(driver):
    driver.get(JSF_URL)

    # close welcome dialog
    driver.find_element_by_class_name('ui-icon-closethick').click()
    wait_for_jquery(driver=driver)


def search_for_name(search_name, driver):
    load_search_page(driver)

    # enter query and click search button
    driver.find_element_by_name('form:nombresConsulta').send_keys(search_name)
    driver.find_element_by_name('form:buscarCosnsulta').click()

    # wait for results
    wait_for_ajax(driver)

    # get result rows
    row_path = "//tbody[@id='form:tblResultadoConsulta_data']/tr"
    prows = driver.find_elements_by_xpath(row_path)
    if len(prows) > 0:
        # there is at least one result row
        # check if there is only one row indicating no matches: "Sin Datos"
        empty_class = 'ui-datatable-empty-message'
        if len(prows) == 1 and empty_class in prows[0].get_attribute('class'):
            return([])
        return(prows)
    else:
        # there are no result rows
        # this is an error
        error_elem = driver.find_element_by_class_name('ui-growl-title')
        error_text = error_elem.text
        # TODO? check that error is recognized?
        # errors encountered so far:
        # * "Proporciona el nombre correcto"
        # * "Campo nombre: proporciona 3 caracteres mínimo por nombre
        #    y/o apellido"
        # * "Campo Nombre: requiere un apellido"
        raise ValueError(error_text)


def process_person(prow, driver, session):
    dependency_elems = prow.find_elements_by_xpath(".//td/span")
    assert len(dependency_elems) == 1
    dependency = dependency_elems[0].text
    name_elems = prow.find_elements_by_xpath(".//td/a")
    assert len(name_elems) == 1
    name = unidecode(name_elems[0].text)

    # load the list of declarations for this person
    name_elems[0].click()
    rows_path = "//tbody[@id='form:tblResultado_data']/tr"
    decl_rows = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.XPATH, rows_path))
    )
    assert len(decl_rows) > 0

    # process the first declaration (last row) to check for the person
    # and dependency in the database, adding them as needed
    decl0_row = decl_rows[-1]
    decl0_dep, decl0_type, decl0_sent = process_decl_row(decl0_row)
    decl0_dep_q = Dependency(DEPENDENCY=decl0_dep)
    decl0_dep_map = one_or_create(decl0_dep_q, session)
    decl0_dep_id = decl0_dep_map.ID
    # the name in the interface may have ? characters in it
    # if so, get the name from database or PDF
    srv_q = Servant(NAME=name, DECL0_DEP_ID=decl0_dep_id,
                    DECL0_TYPE=decl0_type, DECL0_SENT=decl0_sent)
    pdf0 = None
    if '?' in name:
        srv_map = one_like(srv_q, session)
        if srv_map is None:
            pdf0 = get_declaration(decl0_row)
            pdfq0 = pdf.PDFQuery(pdf0)
            pdf0_name = unidecode(pdf.get_header_name(pdfq0))
            assert fnmatch(pdf0_name, name)
            name = pdf0_name
            srv_q.NAME = name
            session.add(srv_q)
            session.commit()
            srv_map = srq_q
        else:
            name = srv_map.NAME
    else:
        srv_map = one_or_create(srv_q, session)

    # if we've downloaded pdf0, save it now
    if pdf0:
        update_declaration(decl0_row, dependency=decl0_dep_map,
                           servant=srv_map, pdf=pdf0,
                           driver=driver, session=session)
        remaining_decl_rows = decl_rows[:-1]
    else:
        remaining_decl_rows = decl_rows

    # process the other declarations
    for decl_row in remaining_decl_rows:
        update_declaration(decl_row, servant=srv_map,
                           driver=driver, session=session)

    ## return to search results
    return_button = driver.find_element_by_id('form:buscar')
    return_button.click()
    wait_for_ajax(driver)


def process_decl_row(decl_row):
    row_path = ".//td/span[@class='dtDatosResp']"
    row_elems = decl_row.find_elements_by_xpath(row_path)
    assert len(row_elems) == 3
    dependency_str = row_elems[0].text
    decl_type_str = row_elems[1].text
    decl_type = decl_type_mapper_es[decl_type_str]
    date_sent_str = row_elems[2].text
    day, month, year = (int(e) for e in date_sent_str.split('/'))
    date_sent = datetime.date(year, month, day)

    cons_decl_elems = decl_row.find_elements_by_xpath(".//td/a/div")
    assert len(cons_decl_elems) == 1

    return((dependency_str, decl_type, date_sent))


def update_declaration(decl_row, servant, driver, session,
                       dependency=None, pdf=None, skip_existing=True):
    srv_id = servant.ID
    dep, decl_type, date_sent = process_decl_row(decl_row)

    if dependency:
        dep_id = dependency.ID
    else:
        dep_map = one_or_create(Dependency(DEPENDENCY=dep), session)
        dep_id = dep_map.ID

    decl_q = Declaration(SERVANT_ID=srv_id, DEPENDENCY_ID=dep_id,
                         TYPE=decl_type, SENT=date_sent)
    decl_map = one_or_create(decl_q, session)

    if not skip_existing or decl_map.PDF is None:
        log_str = "Getting PDF for declaration: {}; {}; {}; {}"
        log_str = log_str.format(servant.NAME, dep, decl_type, date_sent)
        logger.info(log_str)

        if pdf is None:
            pdf = get_declaration_pdf(decl_row, driver=driver)
        save_declaration_pdf(decl_map, pdf, session=session)


def get_declaration_pdf(decl_row, driver):
    # post declaration request form
    data_ri = decl_row.get_attribute('data-ri')
    cookies = get_request_cookies(driver)
    headers = {'Connection': 'keep-alive',
               'Faces-Request': 'partial/ajax',
               'X-Requested-With': 'XMLHttpRequest'
    }
    source_fs = "form:tblResultado:{}:j_idt68"
    execute_fs = "form:tblResultado:{}:j_idt68"
    self_fs = "form:tblResultado:{}:j_idt68"
    self_str = self_fs.format(data_ri)
    data = {'javax.faces.partial.ajax': 'true',
            'javax.faces.source': source_fs.format(data_ri),
            'javax.faces.partial.execute': execute_fs.format(data_ri),
            'javax.faces.partial.render': 'form:blckDcmnt',
            self_str: self_str,
            'javax.faces.ViewState': get_viewstate(driver)
    }
    resp1 = requests.post(JSF_URL, data=data, cookies=cookies)

    # get pdf
    resp_pdf = requests.get(PDF_URL, cookies=cookies)
    return(resp_pdf.content)


def hashbytes(data, hasher=hashlib.sha256(), blocksize=65536):
    with io.BytesIO(data) as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
        return(hasher.hexdigest())


def save_declaration_pdf(declaration, pdf, session):
    declaration.PDF = pdf
    declaration.SHA256 = hashbytes(pdf)
    session.commit()


def scrape_name(search_name, driver, session):
    pers_row_idx = 0
    while True:
        # get persons matching the search name
        # TODO: This might miss declarations if the search results are
        #   updated while scraping
        pers_rows = search_for_name(search_name, driver=driver)
        if pers_row_idx >= len(pers_rows):
            break
        pers_row = pers_rows[pers_row_idx]
        process_person(pers_row, driver=driver, session=session)
        pers_row_idx += 1

def scrape_names(search_names):
    driver = get_driver()
    session = get_session()
    try:
        for search_name in search_names:
            scrape_name(search_name, driver=driver, session=session)
    finally:
        driver.quit()
