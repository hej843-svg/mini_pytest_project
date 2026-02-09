import requests
import json
import os  # os 모듈 추가
import logging

# 로거 설정
log = logging.getLogger()

def post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample, INSIGHT_API_KEY="test"):
    clean_CXR_IP = CXR_IP.replace('"', '')
    url = f"http://{clean_CXR_IP}:{CXR_APP_PORT}/api/v1/inference/"
    headers = {
        "Authorization": "Bearer " + INSIGHT_API_KEY
    }
    values = json.loads(updated_inference_json)
    
    # DCM 파일을 전송하기 위한 파일 딕셔너리 생성
    if os.path.isfile(test_sample):  # test_sample이 파일인지 확인
        files = {
            'dcm': open(test_sample, 'rb'),  # test_sample을 파일로 열기
        }
    else:
        log.error(f"Error: {test_sample} is not a valid file path.")
        return None
    
    #parameters 추가
    values['parameters'] = updated_inference_json

    values['source_type'] = "file"
    
    response_data = requests.post(url, data=values, headers=headers, files=files, timeout=40)  # 40초 timeout

    return response_data

def post_1S_inference_with_CPC(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_current, test_sample_previous, INSIGHT_API_KEY="test"):
    clean_CXR_IP = CXR_IP.replace('"', '')
    url = f"http://{clean_CXR_IP}:{CXR_APP_PORT}/api/v1/inference/"
    headers = {
        "Authorization": "Bearer " + INSIGHT_API_KEY
    }
    values = json.loads(updated_inference_json)
    
    # 파일 딕셔너리 생성
    files = {
            'dcm': open(test_sample_current, 'rb'),  # test_sample_current을 파일로 열기
            'previous_dcm': open(test_sample_previous, 'rb'),  # test_sample_previous을 파일로 열기
        }
    
    #parameters 추가
    values['parameters'] = updated_inference_json

    values['source_type'] = "file"
    
    response_data = requests.post(url, data=values, headers=headers, files=files, timeout=60)  # 60초 timeout

    return response_data

def post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample, INSIGHT_API_KEY="test"):
    clean_CXR_IP = CXR_IP.replace('"', '')
    url = f"http://{clean_CXR_IP}:{CXR_APP_PORT}/api/v1/inference/raw-data"
    headers = {
        "Authorization": "Bearer " + INSIGHT_API_KEY
    }
    values = json.loads(updated_inference_raw_data_json)
    
    # DCM 파일을 전송하기 위한 파일 딕셔너리 생성
    if os.path.isfile(test_sample):  # test_sample이 파일인지 확인
        files = {
            'dcm': open(test_sample, 'rb'),  # test_sample을 파일로 열기
        }
    else:
        print(f"Error: {test_sample} is not a valid file path.")
        return None

    # parameters 추가
    values['parameters'] = updated_inference_raw_data_json

    # TEST : updated_inference_raw_data_json 출력
    # log.info("updated_inference_raw_data_json: %s", updated_inference_raw_data_json)
    
    values['source_type'] = "file"

    response_data = requests.post(url, data=values, headers=headers, files=files, timeout=40)  # json에서 data로 변경

    return response_data
    
def post_1S_inference_raw_data_with_CPC(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_current, test_sample_previous, INSIGHT_API_KEY="test"):
    clean_CXR_IP = CXR_IP.replace('"', '')
    url = f"http://{clean_CXR_IP}:{CXR_APP_PORT}/api/v1/inference/raw-data"
    headers = {
        "Authorization": "Bearer " + INSIGHT_API_KEY
    }
    values = json.loads(updated_inference_raw_data_json)
    
    # 파일 딕셔너리 생성
    files = {
        'dcm': open(test_sample_current, 'rb'),
        'previous_dcm': open(test_sample_previous, 'rb'),
    }
    
    # parameters 추가
    values['parameters'] = updated_inference_raw_data_json

    values['source_type'] = "file"
    
    # TEST : updated_inference_raw_data_json 출력
    log.info("updated_inference_raw_data_json: %s", updated_inference_raw_data_json)

    response_data = requests.post(url, data=values, headers=headers, files=files, timeout=60)  # json에서 data로 변경

    return response_data