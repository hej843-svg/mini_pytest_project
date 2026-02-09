import requests
import json
import logging

log = logging.getLogger(__name__)

def put_config(updated_config_json, CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    """
    PUT /api/v1/config API 를 통해 config.json 을 업데이트하는 함수
    
    put_config 함수는 응답 status code 가 200 이 아닌 경우 실패 처리하기에,
    에러케이스 확인하는 용도로는 사용하지 않아야 합니다.
    
    :param updated_config_json: 테스트에 맞는 config 내용
    :param CXR_IP: CXR IP 주소
    :param CXR_APP_PORT: CXR 애플리케이션 포트
    :param INSIGHT_API_KEY: API 요청에 사용될 Bearer 토큰 (기본값은 "test")
    :return: API 응답
    """
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/api/v1/config/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    values = json.loads(updated_config_json)
    
    # TEST : 요청 파라미터 확인
    log.info(f"Request URL: {url}")
    log.info(f"Request headers: {headers}")
    log.info(f"Request body: {json.dumps(values, indent=1)}")
    
    response = requests.put(url, data=json.dumps(values,indent=1), headers=headers)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    # 상태 코드가 200이 아닐 경우 assertion failure 발생
    assert response.status_code == 200, f"Assertion Failed: Status code: {response.status_code}, Error: {response.text}"

    return response


def put_config_test(updated_config_json, CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    """
    PUT /api/v1/config API 를 통해 config.json 을 업데이트하는 함수
    
    put_config_test 함수는 응답 status code 가 200 이 아닌 경우에도 실패 처리하지않기에,
    에러케이스를 포함한 모든 케이스에서 사용이 가능합니다.
    
    :param updated_config_json: 테스트에 맞는 config 내용
    :param CXR_IP: CXR IP 주소
    :param CXR_APP_PORT: CXR 애플리케이션 포트
    :param INSIGHT_API_KEY: API 요청에 사용될 Bearer 토큰 (기본값은 "test")
    :return: API 응답
    """
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/api/v1/config/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
            "Content-Type": "application/json"
    }
    values = json.loads(updated_config_json)
    
    # TEST : 요청 파라미터 확인
    log.info(f"Request URL: {url}")
    log.info(f"Request headers: {headers}")
    log.info(f"Request body: {json.dumps(values, indent=1)}")
    
    response = requests.put(url, data=json.dumps(values,indent=1), headers=headers)

    # 응답 헤더와 바디 기록
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.text}")

    return response


def get_config_test(CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY="test"):
    """
    Function to retrieve configuration settings from the product via GET /api/v1/config API
    
    The get_config_test function does not fail when the response status code is not 200,
    so it can be used in all cases, including error cases.
    
    :param CXR_IP: CXR IP address
    :param CXR_APP_PORT: CXR application port
    :param INSIGHT_API_KEY: Bearer token used for API requests (default is "test")
    :return: API response
    """
    url = f"http://{CXR_IP}:{CXR_APP_PORT}/api/v1/config/"
    headers = {
            "Authorization": "Bearer " + INSIGHT_API_KEY,
    }
    
    # TEST : Verify request parameters
    log.info(f"Request URL: {url}")
    log.info(f"Request headers: {headers}")
    
    response = requests.get(url, headers=headers)

    # Log response headers and body
    log.info(f"Response Headers: {response.headers}")
    log.info(f"Response Body: {response.json()}")

    return response