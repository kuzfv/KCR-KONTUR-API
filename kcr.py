import os
import time
import requests
from requests import HTTPError
from datetime import datetime
from dataclasses import dataclass


APIKEY = os.getenv("KCR-APIKEY")
URL = "https://api.kontur.ru/kcr"
PLUG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00'
'\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00\tpHYs\x00\x00\x12t'
'\x00\x00\x12t\x01\xdef\x1fx\x00\x00\x00\x0cIDAT\x18Wc\x10\x15\x15\x05\x00\x00'
'\x82\x00@B \xdbC\x00\x00\x00\x00IEND\xaeB`\x82'


@dataclass
class Organization:
    inn: int
    kpp: int
    full_name: str


@dataclass
class Employee:
    firstname: str
    lastname: str
    middlename: str
    position: str
    inn: int = None
    snils: int = None
    phone: int = None
    email: str = None
    birth_date: str = None
    identity_document: dict = None


def search_issues(sortOrder: str = "desc", offset: int = 0, limit: int = 100,
                 **params) -> dict:
    """Поиск заявок. Описание параметров поиска доступно по ссылке https://clck.ru/35e6xt"""

    req = requests.get(f"{URL}/v1/issues",
                       headers={"X-KONTUR-APIKEY": APIKEY},
                       params=params)
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    return req.json()


def get_issue(issue_id: str) -> dict:
    """Получение информации о заявке"""

    req = requests.get(f"{URL}/v1/issues/{issue_id}",
                       headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    return req.json()


def create_issue(employee: Employee, organization: Organization,
                 certificate_template: str, subject_type: str = "naturalPerson",
                 use_areas: list = [], non_exportable: bool = False,
                 csp_info: str = "cryptoPro", crypto_pro_license: bool = False,
                 dss_app: str = "myDss") -> dict:
    """Создать заявку"""

    payload = {
        "certificateTemplateInfo": {
            "type": certificate_template,
            "useAreas": use_areas,
            "nonExportable": non_exportable
            },
        "subjectInfo": {
            "type": subject_type,
            "inn": employee.inn if subject_type == "naturalPerson" else organization.inn,
            "lastname": employee.lastname,
            "firstname": employee.firstname,
            "middlename": employee.middlename,
            "email": employee.email,
            "phone": employee.phone,
            "organizationInfo": {
                "kpp": "string",
                "position": employee.position,
                "unit": "string",
                "employeeInn": employee.inn
                } if subject_type != "naturalPerson" else None
            },
        "cspInfo": {
            "type": csp_info,
            "addCryptoProLicense": crypto_pro_license,
            "dssApplication": dss_app if csp_info == "dss" else None
            }
        }
    print(payload)

    req = requests.post(f"{URL}/v1/issues",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        json=payload)
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    return req.json()


def create_renew_issue(issue_id: str, for_natural_person: bool = False) -> dict:
    """Создать заявку на перевыпуск"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/renew",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        params={"forNaturalPerson": for_natural_person})
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    return req.json()


def validate_issue(issue_id: str) -> dict:
    """Отправить заявку на проверку"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/validate",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def decline_issue(issue_id: str) -> dict:
    """Отклонить одобренную заявку"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/decline",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def forward_to_cabinet(issue_id: str) -> dict:
    """Направить заявку в личный кабинет"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/forward-to-cabinet",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def retrieve_from_cabinet(issue_id: str) -> dict:
    """Вернуть заявку из личного кабинета"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/retrieve-from-cabinet",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def upload_certificate_request(issue_id: str, request_path: str, certificate_request_type: str = "dss") -> dict:
    """Загрузить запрос на выпуск сертификата"""

    content_type = {"xml": "xml", "json": "json", "req": "x.req"}.get(request_path.split('.')[-1])
    with open(request_path, "rb") as request:
        req = requests.post(f"{URL}/v1/issues/{issue_id}/upload-certificate-request",
                            headers={"X-KONTUR-APIKEY": APIKEY,
                                     "Content-Type": f"application/{content_type}",
                                     "Content-Length": os.path.getsize(request_path)},
                            params={"certificateRequestType": certificate_request_type},
                            data=request.read())
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return req.json()


def download_certificate(issue_id: str) -> dict:
    """Скачать файл сертификата"""

    issue_info = get_issue(issue_id).get("subjectInfo")
    req = requests.post(f"{URL}/v1/issues/{issue_id}/download-certificate",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    with open(f"./{issue_info['lastname']} {issue_info['firstname']} {issue_info['middlename']}.cer", "wb") as certificate:
        certificate.write(req.content)
        return {}


def delete_issue(issue_id: str) -> dict:
    """Удалить заявку"""
    
    req = requests.delete(f"{URL}/v1/issues/{issue_id}",
                          headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def change_issue(employee: Employee, organization: Organization,
                 certificate_template: str, subject_type: str = "naturalPerson",
                 use_areas: list = [], non_exportable: bool = False,
                 csp_info: str = "cryptoPro", crypto_pro_license: bool = False,
                 dss_app: str = "myDss") -> dict:
    """Изменить данные в заявке"""

    payload = {
        "certificateTemplateInfo": {
            "type": certificate_template,
            "useAreas": use_areas,
            "nonExportable": non_exportable
            },
        "subjectInfo": {
            "type": subject_type,
            "inn": employee.inn if subject_type == "naturalPerson" else organization.inn,
            "lastname": employee.lastname,
            "firstname": employee.firstname,
            "middlename": employee.middlename,
            "email": employee.email,
            "phone": employee.phone,
            "organizationInfo": {
                "kpp": "string",
                "position": employee.position,
                "unit": "string",
                "employeeInn": employee.inn
                } if subject_type != "naturalPerson" else None
            },
        "cspInfo": {
            "type": csp_info,
            "addCryptoProLicense": crypto_pro_license,
            "dssApplication": dss_app if csp_info == "dss" else None
            }
        }

    req = requests.patch(f"{URL}/v1/issues",
                         headers={"X-KONTUR-APIKEY": APIKEY},
                         json=payload)
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def delete_subject_identification(issue_id: str) -> dict:
    """Удалить отметку об удостоверения личности"""

    req = requests.delete(f"{URL}/v1/issues/{issue_id}/subject-identification",
                          headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def add_subject_identification(issue_id: str, identified_by: str,
                               identification_subject_type: str = "headOfOrganization") -> dict:
    """Добавить отметку об удостоверении личности"""

    payload = {
        "identificationSubjectType": identification_subject_type,
        "identifiedBy": identified_by
        }

    req = requests.put(f"{URL}/v1/issues/{issue_id}/subject-identification",
                       headers={"X-KONTUR-APIKEY": APIKEY},
                       json=payload)
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def add_or_update_note(issue_id: str, text: str) -> dict:
    """Добавить или обновить заметку"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/note",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        json={"content": text})
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    return req.json()


def delete_note(issue_id: str) -> dict:
    """Удалить заметку"""

    req = requests.delete(f"{URL}/v1/issues/{issue_id}/note",
                          headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def download_document_page(issue_id: str, document_type: str, page_id: str,
                           document_format="png") -> dict:
    """Скачать страницу документа"""

    issue_info = get_issue(issue_id).get("subjectInfo")
    req = requests.get(f"{URL}/v1/issues/{issue_id}/documents/{document_type}/pages/{page_id}")
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    with open(f"./{document_type} {issue_info['lastname']} {issue_info['firstname']}"
              f"{issue_info['middlename']}.{document_format}", "wb") as document:
        document.write(req.content)
        return {}


def sign_document(issue_id: str, sms_code: "str") -> dict:
    """Подписать документ простой электронной подписью"""

    payload = {
        "confirmationInfo": {
            "smsCode": sms_code
            }
        }
    req = requests.post(f"{URL}/v1/issues/{issue_id}/documents/releaseStatement/sign",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        json=payload)
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def upload_document(issue_id: str, document_type: str, document_path: str,
                    use_plug: bool = True) -> dict:
    """Загрузить документ"""

    if not use_plug:
        with open(document_path, "rb") as file:
            document = file.read()
    types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
             "gif": "image/gif", "pdf": "application/pdf"}
    req = requests.post(f"{URL}/v1/issues/{issue}/documents/{doctype}/pages",
                        headers={"X-KONTUR-APIKEY": APIKEY,
                                 "Content-Type": types[document_path.split('.')[-1]],
                                 "Content-Length": os.path.getsize(document_path)},
                        data=PLUG if use_plug else document)
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def delete_document(issue_id: str, document_type: str) -> dict:
    """Удалить документ"""

    req = requests.delete(f"{URL}/v1/issues/{issue_id}/documents/{document_type}",
                          headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}
    

def delete_document_page(issue_id: str, document_type: str, page_id: str) -> dict:
    """Удалить страницу документа"""

    req = requests.delete(f"{URL}/v1/issues/{issue_id}/documents/{document_type}/pages/{page_id}",
                          headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def create_document(issue_id: str, document_type: str, document_requisites: dict,
                    action: str = "add") -> dict:
    """Создать документ"""

    assert action in ("add", "delete"), "'action' must be 'add' or 'delete' only"

    if action == "delete":
        payload = {"requisitesToDelete": [requisite.get("type") for requisite in document_requisites]}
    else:
        payload = {"requisitesToAddOrUpdate": document_requisites}
    req = requests.put(f"{URL}/v1/issues/{issue_id}/documents/{document_type}",
                       headers={"X-KONTUR-APIKEY": APIKEY},
                       json=payload)
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def get_document_template(issue_id: str, template_type: str = "releaseStatement") -> dict:
    """Получить шаблон документа"""

    document_mapping = {"releaseStatement": "Заявление на выпуск",
                        "signingAuthority": "Подтверждение права подписи",
                        "warrantWithUseAreas": "Доверенность с областями применения",
                        "applicantWarrant": "Доверенность на получение",
                        "recallStatement": "Заявление на отзыв",
                        "receipt": "Расписка в получении",
                        "phoneChangeStatement": "Заявление на смену телефона",
                        "certificateCopy": "Копия сертификата"}

    issue_info = get_issue(issue_id).get("subjectInfo")
    req = requests.post(f"{URL}/v1/issues/{issue_id}/templates/{template_type}",
                        headers={"X-KONTUR-APIKEY": APIKEY})
    if req.status_code != 200:
        raise HTTPError(f"{req.text}")
    with open(f"./{document_mapping[template_type]} {issue_info['lastname']} {issue_info['firstname'][0]} "
              f"{issue_info['middlename'][0]}.pdf", "wb") as template:
        template.write(req.content)
        return {}


def create_esia_confirmation_request(issue_id: str, snils: str, birth_date: str) -> dict:
    """Создать запрос на подтверждение через ЕСИА"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/confirmation-requests",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        json={"operationToConfirm": "signingReleaseStatementWithEsia",
                              "parameters": {"snilsNumber": snils,
                                             "birthDate": birth_date}})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def create_sms_confirmation_request(issue_id: str) -> dict:
    """Создать запрос на подтверждение через СМС"""

    req = requests.post(f"{URL}/v1/issues/{issue_id}/confirmation-requests",
                        headers={"X-KONTUR-APIKEY": APIKEY},
                        json={"operationToConfirm": "signingReleaseStatement"})
    if req.status_code != 204:
        raise HTTPError(f"{req.text}")
    return {}


def issue_events(prev_id: str = "", break_time_sec: int = 2):
    """Лента событий"""

    def get_time_log() -> str:
        """Время события"""
        
        return datetime.now().strftime("%d.%m %H:%M:%S")

    while True:
        req = requests.get(f"{URL}/v1/issue-events",
                           params={"prevId": prev_id},
                           headers={"X-KONTUR-APIKEY": APIKEY})
        if req.status_code != 200:
            raise HTTPError(f"{req.text}")
        response = req.json()
        if not response['events']:
            time.sleep(break_time_sec)
            continue
        if prev_id == response["lastId"]:
            time.sleep(5)
        else:
            prev_id = response["lastId"]
            time.sleep(break_time_sec)


if __name__ == "__main__":
  ...
