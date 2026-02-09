import requests
import json
import logging

log = logging.getLogger(__name__)

def get_health_to_gw(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/health/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_health_to_is(INSIGHT_API_HOST, INSIGHT_API_KEY="test"):
    url = f"{INSIGHT_API_HOST}/health/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_status(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/status/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_version_to_gw(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/version/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_version_to_is(INSIGHT_API_HOST, INSIGHT_API_KEY="test"):
    url = f"{INSIGHT_API_HOST}/version/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_label(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/api/v1/label/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_product_info(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/product-info"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)
    
    # Log response headers and body
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_udi(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/api/v1/udi"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    response = requests.get(url)
    
    # Log response headers and body
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response