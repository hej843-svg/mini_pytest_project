import os
import re
import pydicom
from datetime import datetime, timezone, timedelta
from time import sleep
import time
import subprocess
import logging
import json
from easydict import EasyDict as edict
from requests_toolbelt.multipart.decoder import MultipartDecoder
from utils import cxr_config
from utils import cxr_1S_inference
from pydicom.tag import Tag
from pydicom.multival import MultiValue
import pytest_check as check
import os
import configparser
import paramiko
import base64
from utils.error_mapping import error_mapping
from PIL import Image

# 로거 설정
log = logging.getLogger()

# pytest.ini 파일에서 설정 읽기
config = configparser.ConfigParser()
ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pytest.ini')
files_read = config.read(ini_path)

if files_read:
    log.info("설정 파일이 성공적으로 읽혔습니다:", files_read)
    # DEFAULT 섹션에 있는 모든 키-값 쌍 출력
    log.info("DEFAULT 섹션 내용:")
    for key, value in config['DEFAULT'].items():
        log.info(f"{key} = {value}")
else:
    log.error("설정 파일을 읽지 못했습니다. 파일 경로를 확인하세요.")

# 환경 변수
CXR_IP = config.get('DEFAULT', 'CXR_IP').strip('"')  # CXR IP 주소
CXR_APP_PORT = config.getint('DEFAULT', 'CXR_APP_PORT')  # CXR 애플리케이션 포트
CXR_SCP_PORT = config.getint('DEFAULT', 'CXR_SCP_PORT')  # CXR SCP 포트
CXR_TOKEN = config.get('DEFAULT', 'CXR_TOKEN').strip('"')  # CXR 토큰
CXR_GW_CONFIG_PATH = config.get('DEFAULT', 'CXR_GW_CONFIG_PATH').strip('"')  # CXR GW 설정 폴더 경로
CXR_IS_CONFIG_PATH = config.get('DEFAULT', 'CXR_IS_CONFIG_PATH').strip('"')  # CXR IS 설정 폴더 경로
CXR_GW_LOG_PATH = config.get('DEFAULT', 'CXR_GW_LOG_PATH').strip('"')  # CXR GW log file path
CXR_IS_LOG_PATH = config.get('DEFAULT', 'CXR_IS_LOG_PATH').strip('"')  # CXR IS log file path
INSIGHT_API_HOST = config.get('DEFAULT', 'INSIGHT_API_HOST').strip('"')  # Inference server url
INSIGHT_API_KEY = config.get('DEFAULT', 'INSIGHT_API_KEY').strip('"')  # Insight API 키
DICOM_STORAGE_IP = config.get('DEFAULT', 'DICOM_STORAGE_IP').strip('"')  # DICOM 저장소 IP
DICOM_STORAGE_ROOT_PATH = config.get('DEFAULT', 'DICOM_STORAGE_ROOT_PATH').strip('"')  # DICOM 저장소 루트 경로

DCMTK_ROOT_PATH = config.get('DEFAULT', 'DCMTK_ROOT_PATH').strip('"')  # DICOM 라이브러리 경로
RESULT_DIR = config.get('DEFAULT', 'RESULT_DIR').strip('"')  # 복사해올 TestData 및 분석 결과 저장할 위치 지정
TEMP_FOLDER = config.get('DEFAULT', 'TEMP_FOLDER').strip('"')  # 임시 폴더 이름
SEND_FOLDER = config.get('DEFAULT', 'SEND_FOLDER').strip('"')  # 전송 폴더 이름
PYTHON_ROOT_PATH = config.get('DEFAULT', 'PYTHON_ROOT_PATH').strip('"')  # Python 설치 경로

SOURCE_IP = config.get('DEFAULT', 'SOURCE_IP').strip('"')  # 원본 Dicom 소스 IP 주소
DEST_IP = config.get('DEFAULT', 'DEST_IP').strip('"')  # 결과 Dicom 수신을 위한 IP 입력 
DEST_PORT = config.getint('DEFAULT', 'DEST_PORT')  # 결과 Dicom 수신을 위한 Storescp Port 입력
DEST_AETITLE = config.get('DEFAULT', 'DEST_AETITLE').strip('"')  # -aet 값 입력
DEST_HL7_IP = config.get('DEFAULT', 'DEST_HL7_IP').strip('"')  # hl7 수신을 위한 IP 입력
DEST_HL7_PORT = config.getint('DEFAULT', 'DEST_HL7_PORT')  # hl7 수신을 위한 Port 입력
FROWARD_DEST_IP = config.get('DEFAULT', 'FROWARD_DEST_IP').strip('"')  # Foward 기능 : 원본 dicom 전송을 위한 IP 입력
FROWARD_DEST_PORT = config.getint('DEFAULT', 'FROWARD_DEST_PORT')  # Foward 기능 : 원본 dicom 전송을 위한 Port 입력
FROWARD_DEST_AETITLE = config.get('DEFAULT', 'FROWARD_DEST_AETITLE').strip('"')  # Foward 기능 : 원본 dicom 전송을 위한 -aet 값 입력

SSH_PORT = config.getint('DEFAULT', 'SSH_PORT')
SSH_USER_NAME = config.get('DEFAULT', 'SSH_USER_NAME').strip('"')
SSH_USER_PASSWORD = config.get('DEFAULT', 'SSH_USER_PASSWORD').strip('"')

# 테스트에 필요한 변수
date_time = datetime.now().strftime("%Y%m%d_%H%M%S")
base_time = datetime.now(timezone(timedelta(hours=9)))

def dimse_pre_process(test_id, test_data, updates):
    """
    DIMSE 테스트 전 전처리 함수
    
    :param test_id: 테스트 케이스 ID
    :param test_data: 테스트 데이터 파일명
    :param updates: 설정 변경 사항
    :return: 결과 폴더 경로
    """
    # Pre Processing 1 : Make result directory and copy test data
    result_dir_path = make_result_directory(RESULT_DIR, date_time, SEND_FOLDER, test_id)
    copy_test_data(result_dir_path, DICOM_STORAGE_IP, DICOM_STORAGE_ROOT_PATH, test_data)

    # Pre Processing 2 : storescp, hl7 rcv 실행
    terminate_storescp_process(DEST_PORT)
    run_storescp(DCMTK_ROOT_PATH, result_dir_path, DEST_AETITLE, DEST_PORT, test_id)
    terminate_hl7rcv_process(DEST_HL7_PORT)
    run_hl7rcv(DEST_HL7_PORT, result_dir_path)
    
    # Pre Processing 3 : Change Settings in APP (설정)
    updated_config = update_config_setting(updates)
    cxr_config.put_config(updated_config, CXR_IP, CXR_APP_PORT, INSIGHT_API_KEY)
    
    return result_dir_path

def pre_process_1S_inference(test_id, test_data, updates):
    """
    1 step inference 테스트 전 전처리 함수
    
    :param test_id: 테스트 케이스 ID
    :param test_data: 테스트 데이터 파일명
    """
    # Pre Processing 1 : Make result directory and copy test data
    result_dir_path = make_result_directory(RESULT_DIR, date_time, SEND_FOLDER, test_id)
    copy_test_data(result_dir_path, DICOM_STORAGE_IP, DICOM_STORAGE_ROOT_PATH, test_data)
    
    # Pre Processing 3 : Set the inference API's parameters
    updated_inference_json = update_inference_setting(updates)
    
    return result_dir_path, updated_inference_json
    
def pre_process_1S_inference_raw_data(test_id, test_data, updates):
    """
    1 step inference raw data 테스트 전 전처리 함수
    
    :param test_id: 테스트 케이스 ID
    :param test_data: 테스트 데이터 파일명
    """
    # Pre Processing 1 : Make result directory and copy test data
    result_dir_path = make_result_directory(RESULT_DIR, date_time, SEND_FOLDER, test_id)
    copy_test_data(result_dir_path, DICOM_STORAGE_IP, DICOM_STORAGE_ROOT_PATH, test_data)
    
    # Pre Processing 3 : Set the inference API's parameters
    updated_inference_raw_data_json = update_inference_raw_data_setting(updates)
    
    return result_dir_path, updated_inference_raw_data_json

def pre_preocess_common_api(test_id):
    """
    common API 테스트 전 전처리 함수
    
    :param test_id: 테스트 케이스 ID
    """
    # Pre Processing 1 : Make result directory 
    result_dir_path = make_result_directory(RESULT_DIR, date_time, SEND_FOLDER, test_id)
    
    return result_dir_path  

def is_grayscale_sc(file_path):
    """
    주어진 DICOM 파일이 Grayscale SC (Secondary Capture Image)인지 판단하는 함수.

    :param file_path: DICOM 파일 경로
    :return: True if it's a Grayscale SC file, otherwise False
    """
    try:
        ds = pydicom.dcmread(file_path)
        
        log.info(f"DICOM 파일 읽기: {file_path}")
        
        # 조건 체크
        is_secondary_capture = ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.7"  # MediaStorageSOPClassUID
        is_samples_per_pixel_1 = ds.SamplesPerPixel == 1  # SamplesPerPixel
        is_photometric_interpretation_monochrome2 = ds.PhotometricInterpretation == "MONOCHROME2"  # PhotometricInterpretation

        # 모든 조건이 맞으면 Grayscale SC 파일
        if is_secondary_capture and is_samples_per_pixel_1 and is_photometric_interpretation_monochrome2:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error reading DICOM file: {e}")
        return False

def sc_type(file_path):
    """
    주어진 DICOM 파일의 SC type을 확인하는 함수.

    :param file_path: DICOM 파일 경로
    :return: SC type
    """
    try:
        ds = pydicom.dcmread(file_path)
        return ds.get((0x0011, 0x1003)).value
    except Exception as e:
        print(f"Error reading DICOM file: {e}")
        return None

def output_type_check(result_dir_path, test_data):
    """
    결과 파일들의 타입을 확인하는 함수.
    test_data와 같은 파일명을 가진 파일을 제외하고 모든 파일의 타입을 확인합니다.

    :param result_dir_path: 결과 파일이 저장된 전체 경로
    :param test_data: 제외할 테스트 데이터 파일명
    :return: 결과 파일의 타입별 개수를 담은 딕셔너리
    """
    # 결과 타입별 카운트를 저장할 딕셔너리
    result_counts = {
        "sc_map": 0,
        "sc_report": 0,
        "sc_additional": 0,
        "gsps": 0,
        "sr": 0,
        "hl7": 0,
        "unknown": 0
    }
    
    # result_dir_path에서 하위 폴더가 있는지 확인
    has_subfolder = any(os.path.isdir(os.path.join(result_dir_path, f)) for f in os.listdir(result_dir_path))

    if has_subfolder:
        # 하위 폴더가 있는 경우, 하위 폴더를 제외
        result_files = [f for f in os.listdir(result_dir_path) 
                        if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]
    else:
        # 하위 폴더가 없는 경우, test_data와 동일한 파일명을 가진 파일을 제외
        result_files = [f for f in os.listdir(result_dir_path) 
                        if os.path.isfile(os.path.join(result_dir_path, f)) and f != test_data]
    
    log.info(f"result_files: {result_files}")
    
    try:
        # 각 파일의 타입 체크
        for file_name in result_files:
            file_path = os.path.join(result_dir_path, file_name)
            
            try:
                # HL7 파일 체크
                if file_name.endswith('.hl7'):
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')
                        lines = content.split("\r")
                        if lines:
                            first_line = lines[0].strip()
                            hl7_pattern = r'^MSH\|\^\~\\\&\|.+\|.+\|\|\|\d+\|\|.+\|.+\|.+\|.+\|\|\|\|\|\|UNICODE UTF-8$'
                            if re.match(hl7_pattern, first_line):
                                result_counts["hl7"] += 1
                                continue
                    except Exception as e:
                        log.error(f"Error checking HL7 file: {e}")
                        result_counts["unknown"] += 1
                        continue

                # DICOM 파일 체크
                ds = pydicom.dcmread(file_path)
                media_storage = ds.file_meta.MediaStorageSOPClassUID if hasattr(ds, 'file_meta') else None
                
                if media_storage is not None:
                    # Secondary Capture Image인 경우
                    if media_storage == "1.2.840.10008.5.1.4.1.1.7":  # SecondaryCaptureImageStorage
                        sc_type = ds.get((0x0011, 0x1003))
                        if sc_type is not None:
                            sc_type_value = sc_type.value
                            if "SC_MAP" in sc_type_value:
                                result_counts["sc_map"] += 1
                            elif "SC_REPORT" in sc_type_value:
                                result_counts["sc_report"] += 1
                            elif "SC_ADDITIONAL" in sc_type_value:
                                result_counts["sc_additional"] += 1
                            else:
                                result_counts["unknown"] += 1
                        else:
                            result_counts["unknown"] += 1
                    
                    # Grayscale Softcopy Presentation State인 경우
                    elif media_storage == "1.2.840.10008.5.1.4.1.1.11.1":  # GrayscaleSoftcopyPresentationStateStorage
                        result_counts["gsps"] += 1
                    
                    # Basic Text SR인 경우
                    elif media_storage == "1.2.840.10008.5.1.4.1.1.88.11":  # BasicTextSRStorage
                        result_counts["sr"] += 1
                    else:
                        result_counts["unknown"] += 1
                else:
                    result_counts["unknown"] += 1

            except Exception as e:
                log.error(f"Error checking file {file_name}: {e}")
                result_counts["unknown"] += 1
        
        # 결과 로깅
        total_files = len(result_files)
        log.info(f"Total files found: {total_files}")
        for file_type, count in result_counts.items():
            if count > 0:
                log.info(f"{file_type}: {count} files")
        
        return result_counts

    except Exception as e:
        log.error(f"Error accessing directory: {e}")
        return result_counts

def check_result_file_count(result_dir_path, test_data):
    """
    결과 파일의 개수를 확인하는 함수.
    test_data와 같은 파일명을 가진 파일(원본 dicom 파일)을 제외하고 모든 파일의 개수를 반환합니다.

    :param result_dir_path: 결과 파일이 저장된 경로
    :param test_data: 제외할 테스트 데이터 파일명
    :return: 결과 파일의 개수
    """
    
    # result_dir_path에서 하위 폴더가 있는지 확인
    has_subfolder = any(os.path.isdir(os.path.join(result_dir_path, f)) for f in os.listdir(result_dir_path))

    if has_subfolder:
        # 하위 폴더가 있는 경우, 하위 폴더를 제외
        result_files = [f for f in os.listdir(result_dir_path) 
                        if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]
    else:
        # 하위 폴더가 없는 경우, test_data와 동일한 파일명을 가진 파일을 제외
        result_files = [f for f in os.listdir(result_dir_path) 
                        if os.path.isfile(os.path.join(result_dir_path, f)) and f != test_data]
    
    log.info(f"result_files: {result_files}")
    
    try:
        file_count = len(result_files)
        
        if file_count == 0:
            log.info("No result files found")
        else:
            log.info(f"Found {file_count} result files")
            
        return file_count

    except Exception as e:
        log.error(f"Error checking result files: {e}")
        return 0

def get_result_file_path(result_dir_path, test_data):
    """
    결과 파일들의 파일명으로 각 결과물 종류별 path 구하는 함수.
    :param result_dir_path: 결과 파일이 저장된 경로
    :param test_data: 제외할 테스트 데이터 파일명
    :return: 각 종류에 맞는 결과 파일들의 path 리스트
    """
    has_subfolder = any(os.path.isdir(os.path.join(result_dir_path, f)) for f in os.listdir(result_dir_path))

    if has_subfolder:
        # 하위 폴더가 있는 경우, 하위 폴더를 제외하고 파일 목록 가져오기
        result_files = [f for f in os.listdir(result_dir_path) 
                            if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]
    else:
        # 하위 폴더가 없는 경우, test_data와 동일한 파일명을 가진 파일을 제외
        result_files = [f for f in os.listdir(result_dir_path) 
                        if os.path.isfile(os.path.join(result_dir_path, f)) and f != test_data]
            
    # 각 결과물 종류별 path를 저장할 리스트
    sc_files = []
    gsps_files = []
    sr_files = []
    hl7_files = []

    # 각 결과물 종류별 path 구하기
    for file_name in result_files:
        file_path = os.path.join(result_dir_path, file_name)
        if 'SC' in file_name:
            sc_files.append(file_path)  # SC 파일 경로 저장
        elif 'PSg' in file_name:
            gsps_files.append(file_path)  # GSPS 파일 경로 저장
        elif 'SR' in file_name:
            sr_files.append(file_path)  # SR 파일 경로 저장
        elif 'hl7' in file_name:
            hl7_files.append(file_path)  # HL7 파일 경로 저장

    return {
        "sc_files": sc_files,
        "gsps_files": gsps_files,
        "sr_files": sr_files,
        "hl7_files": hl7_files
    }

def make_result_directory(local_storage_path, datetime_str, send_folder, suffix_id):
    """
    새로운 결과 폴더를 생성하는 함수.
    
    :param local_storage_path: 로컬 저장 경로
    :param datetime_str: 날짜 시간 문자열
    :param send_folder: 전송 폴더 이름
    :param suffix_id: 접미사 ID
    """
    
    dir_path = f"{local_storage_path}/{datetime_str}_{send_folder}_{suffix_id}"
    os.makedirs(dir_path, exist_ok=True)  # exist_ok=True는 폴더가 이미 있으면 예외를 발생시키지 않음
    log.info(f"Directory created: {dir_path}")
    return dir_path

def dcmsend_to_app(cxr_ip, cxr_scp_port, dest_ae_title, sample_folder):
    """
    DICOM 파일을 서버로 전송하는 함수
    :param cxr_ip: DICOM 서버 IP
    :param cxr_scp_port: DICOM 서버 포트
    :param received_aet: AETitle
    :param sample_folder: 전송하고자 하는 DICOM 파일이 있는 폴더
    """
    
    # 최하위 서브폴더 찾기
    while True:
        subfolders = [f for f in os.listdir(sample_folder) if os.path.isdir(os.path.join(sample_folder, f))]
        if subfolders:
            # sample_folder를 최하위 서브폴더로 업데이트
            sample_folder = os.path.join(sample_folder, subfolders[0])  # 첫 번째 하위 폴더를 사용
            log.info(f"Updated sample_folder: {sample_folder}")
        else:
            break  # 더 이상 하위 폴더가 없으면 종료

    file_list = [f for f in os.listdir(sample_folder) if os.path.isfile(os.path.join(sample_folder, f))]
    
    log.info(f"file_list: {file_list}")

    # DICOM 파일 전송 (dcmsend 실행 후 대기)
    for filename in file_list:
        file_path = os.path.join(sample_folder, filename)
        try:
            cmd = [
                "dcmsend",
                "-to", str(180), "-ta", str(180), "-td", str(600),
                str(cxr_ip), str(cxr_scp_port), str(file_path),
                "--aetitle", str(dest_ae_title)
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 실행 완료될 때까지 대기
            stdout, stderr = process.communicate()
            exit_code = process.returncode

            if exit_code == 0:
                log.info(f"[dcmsend] {filename} sent to {cxr_ip}:{cxr_scp_port}")
            else:
                log.error(f"Error sending {filename}: {stderr.decode()}")

        except Exception as e:
            log.error(f"Error sending {filename}: {e}")
            return

def copy_test_data(result_dir_path, dicom_storage_ip, remote_folder_path, test_data):
    """
    scp 명령어를 사용하여 원격 서버에서 로컬로 데이터를 복사하는 함수.
    
    :param result_dir_path: 로컬 저장 경로
    :param dicom_storage_ip: 원격 DICOM 서버 IP
    :param remote_folder_path: 원격 폴더 경로
    :param test_data: 테스트 데이터 파일명 또는 폴더 경로
    """
    local_folder_path = None  # 기본값으로 None으로 초기화

    # test_data에 슬래시가 없는 경우 확인
    if '/' not in test_data:
        # 단일 파일인 경우, 원격 경로에서 파일을 복사
        scp_command = f"sshpass -p '1q2w3e4r%t' scp -v -o PreferredAuthentications=password lunit@{dicom_storage_ip}:{remote_folder_path}/{test_data} {result_dir_path}"

    else:
        # 폴더 경로인 경우, 폴더를 생성하고 그 안에 파일을 복사
        folder_path = os.path.dirname(test_data)  # 폴더 경로 추출
        local_folder_path = os.path.join(result_dir_path, folder_path.lstrip('/'))  # 로컬 폴더 경로 생성
        os.makedirs(local_folder_path, exist_ok=True)  # 폴더 생성

        # 원격 경로에서 파일을 복사
        scp_command = f"sshpass -p '1q2w3e4r%t' scp -v -o PreferredAuthentications=password -r lunit@{dicom_storage_ip}:{remote_folder_path}/{test_data} {local_folder_path}"

    try:
        # SCP 명령어 실행
        process_scp = subprocess.Popen(scp_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process_scp.communicate()

        # 출력 및 오류 처리
        if stdout:
            log.info(stdout.decode())
        if stderr:
            for line in stderr.decode().splitlines():
                line = line.strip()
                if not line:
                    continue

                # 무해한 메시지 분류
                if ("Executing: program" in line and "sftp" in line) or \
                "debug1:" in line or \
                "OpenSSH_" in line or \
                "Warning: Permanently added" in line:
                    log.debug(f"[SCP harmless] {line}")
                elif "No such file" in line or "Permission denied" in line:
                    log.error(f"[SCP ERROR] {line}")
                else:
                    log.warning(f"[SCP stderr] {line}")

        # 명령어 실행 대기
        process_scp.wait()
        log.info(f"Data copied successfully to {local_folder_path if local_folder_path else result_dir_path}")
        
    except Exception as e:
        log.error(f"Error during SCP execution: {e}")

def run_storescp(dcmtk_root_path, local_storage_path, dest_aetitle, dest_port, auto_tc_id):
    """
    storescp 명령어를 실행한 후, 백그라운드에서 실행되도록 유지하고 다음 코드로 진행하는 함수.
    
    :param dcmtk_root_path: dcmtk 라이브러리 경로
    :param local_storage_path: 로컬 저장 경로
    :param dest_aetitle: 수신 프로세스의 AETitle
    :param dest_port: 수신 프로세스의 포트 번호
    :param auto_tc_id: 테스트 케이스 ID
    """
    storescp_command = f"{dcmtk_root_path}/storescp +xa +uf -xs -od {local_storage_path}/ --aetitle {dest_aetitle} {dest_port} -fe _{auto_tc_id}.dcm &"

    try:
        #프로세스를 백그라운드에서 실행하고, 표준 출력과 오류 출력을 무시
        process_storescp = subprocess.Popen(
            storescp_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        log.info(f"storescp started successfully: PID {process_storescp.pid}")

    except Exception as e:
        log.error(f"Error executing command: {storescp_command}", exc_info=e)

def terminate_storescp_process(dest_port):
    """
    주어진 dest_port로 실행 중인 storescp 프로세스를 찾아 종료하는 함수.
    
    :param dest_port: 종료할 storescp 프로세스를 찾기 위한 포트 번호
    """
    # storescp pid 검색 명령어
    search_pid_command = f"pgrep -f 'storescp.*{dest_port}'"
    try:
        # 프로세스 검색
        process_search_pid = subprocess.Popen(search_pid_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid, _ = process_search_pid.communicate()
        pid = pid.decode().strip()

        # pid가 발견되면 프로세스를 종료
        if pid:
            kill_command = f"kill -9 {pid} 2>&1"
            process_kill = subprocess.Popen(kill_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process_kill.communicate()

            # 에러 출력 로그
            if stderr:
                log.error(stderr.decode())
            if stdout:
                log.info(stdout.decode())

            exit_code = process_kill.returncode
            if exit_code != 0:
                log.error(f"Command {kill_command} failed with exit code {exit_code}")
            else:
                # 프로세스가 성공적으로 종료되었는지 확인
                check_process_command = f"ps -p {pid}"
                process_check = subprocess.Popen(check_process_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                check_stdout, check_stderr = process_check.communicate()

                if check_stdout:
                    log.error(f"Process with PID {pid} is still running after kill command.")
                else:
                    log.info(f"Process with PID {pid} has been successfully terminated.")

        else:
            log.warning(f"No storescp process found running on port {dest_port}.")

    except Exception as e:
        log.error(f"Error executing command: {search_pid_command} or kill command", exc_info=e)

def terminate_hl7rcv_process(hl7rcv_port):
    """
    주어진 hl7rcv_port로 실행 중인 hl7rcv 프로세스를 찾아 종료하는 함수.
    
    :param hl7rcv_port: 종료할 hl7rcv 프로세스를 찾기 위한 포트 번호
    """
    search_pid_command = f"pgrep -f 'hl7rcv.*{hl7rcv_port}'"
    try:
        process_search_pid = subprocess.Popen(search_pid_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid, _ = process_search_pid.communicate()
        pid = pid.decode().strip()
        
        if pid:
            kill_command = f"kill -9 {pid} 2>&1"
            process_kill = subprocess.Popen(kill_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process_kill.communicate()
            
            if stderr:
                log.error(stderr.decode())
                
            exit_code = process_kill.returncode
            if exit_code != 0:
                log.error(f"Command {kill_command} failed with exit code {exit_code}")
                
    except Exception as e:
        log.error(f"Error executing command: {search_pid_command} or kill command", exc_info=e)

def run_hl7rcv(dest_hl7_port, result_dir_path):
    """
    hl7rcv 프로세스를 실행한 후, 백그라운드에서 실행되도록 유지하고 다음 코드로 진행하는 함수.

    :param dest_hl7_port: hl7rcv 프로세스를 실행할 포트 번호
    :param result_dir_path: 결과 디렉토리 경로
    """
    
    hl7rcv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'hl7rcv')    
    hl7rcv_command = f"{hl7rcv_path}/hl7rcv --directory {result_dir_path} -b {dest_hl7_port} &"

    try:
        # 프로세스를 백그라운드에서 실행하고, 표준 출력과 오류 출력을 무시
        process_hl7rcv = subprocess.Popen(
            hl7rcv_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        log.info(f"hl7rcv started successfully: PID {process_hl7rcv.pid}")

    except Exception as e:
        log.error(f"Error executing command: {hl7rcv_command}", exc_info=e)

class ParamesUpdater:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), 'cxr_app_config.json')
        self.config = self.load_config()

    def load_config(self):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return edict(data)

    def update_config(self, updates):
        self._update_dict(self.config, updates)

    def _update_dict(self, original, updates):
        # 업데이트 적용
        def recursive_update(d, u):
            """재귀적으로 기존 딕셔너리를 업데이트"""
            for k, v in u.items():
                if isinstance(v, dict) and isinstance(d.get(k, {}), dict):
                    d[k] = recursive_update(d.get(k, {}), v)
                elif isinstance(v, list) and isinstance(d.get(k, []), list):
                    # 리스트 내부 딕셔너리 업데이트 (일치하는 키 기준)
                    for i, update_item in enumerate(v):
                        if isinstance(update_item, dict) and i < len(d[k]):
                            d[k][i] = recursive_update(d[k][i], update_item)
                        else:
                            d[k].append(update_item)
                else:
                    d[k] = v
            return d
        
        updated_config = recursive_update(self.config, edict(updates))
    
        return updated_config
    
    def get_config_as_json(self):
        return json.dumps(self.config, ensure_ascii=False).replace('True', 'true').replace('False', 'false')
        
def update_config_setting(updates):
    """
    각 테스트를 실행하기 전 테스트에 맞는 config 내용으로 config api의 body를 설정하는 함수.
    
    :param updates: 테스트에 맞는 config 내용
    :return: config 업데이트 json 결과
    """
    try:
        # True, False 값을 소문자로 변환
        for key, value in updates.items():
            if isinstance(value, bool):
                updates[key] = str(value).lower()  # True/False를 문자열로 변환하여 소문자로 설정

        updater = ParamesUpdater()
        updater.update_config(updates)
        config_json = updater.get_config_as_json()
        log.info("Config 설정 업데이트 성공")
        return config_json
    except Exception as e:
        log.error(f"Config 설정 업데이트 실패: {str(e)}")
        raise

# 1 step inference raw data 파라미터 업데이트
class InferenceRawDataUpdater:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), 'cxr_1S_inference_raw_data_params.json')
        self.config = self.load_config()

    def load_config(self):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return edict(data)
    
    def update_config(self, updates):
        self._update_dict(self.config, updates)
        
    def _update_dict(self, original, updates):
        for key, value in updates.items():
            if isinstance(value, dict):
                original[key] = self._update_dict(original.get(key, {}), value)
            else:
                original[key] = value
        return original
    
    def get_config_as_json(self):
        return json.dumps(self.config)
    
def update_inference_raw_data_setting(updates):
    """
    1 step inference raw data 파라미터 업데이트
    
    :param updates: 1 step inference raw data 파라미터 업데이트 내용
    :return: 1 step inference raw data 파라미터 업데이트 json 결과
    """
    updater = InferenceRawDataUpdater()
    updater.update_config(updates)
    return updater.get_config_as_json()

# 1 step inference 파라미터 업데이트
class InferenceUpdater:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), 'cxr_1S_inference_params.json')
        self.config = self.load_config()

    def load_config(self):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return edict(data)
    
    def update_config(self, updates):
        self._update_dict(self.config, updates)
        
    def _update_dict(self, original, updates):
        for key, value in updates.items():
            if isinstance(value, dict):
                original[key] = self._update_dict(original.get(key, {}), value)
            else:
                original[key] = value
        return original
    
    def get_config_as_json(self):
        return json.dumps(self.config)
    
def update_inference_setting(updates):
    """
    1 step inference 파라미터 업데이트
    
    :param updates: 1 step inference 파라미터 업데이트 내용
    :return: 1 step inference 파라미터 업데이트 json 결과
    """
    updater = InferenceUpdater()
    updater.update_config(updates)
    return updater.get_config_as_json()

def save_response_body_to_file(response_body, response_headers, result_dir_path):
    """
    1 step inference api 응답 내용을 결과 파일로 저장하는 함수
    
    :param response_body: 1 step inference api 응답 내용
    :param response_headers: 1 step inference api 응답 헤더
    :param result_dir_path: 결과 파일 저장 경로
    """
    content_type = response_headers.get('Content-Type', '')
    
    if 'multipart' in content_type:
        # Get boundary from Content-Type
        boundary = content_type.split('boundary=')[1]
        # Handle multipart response using the raw bytes and boundary
        decoder = MultipartDecoder(response_body, content_type, 'utf-8')
        for idx, part in enumerate(decoder.parts):
            content_disposition = part.headers[b'Content-Disposition'].decode()
            filename = content_disposition.split('filename=')[1].strip('"')
            filename = result_dir_path + "/" + filename
            with open(filename, 'wb') as f:
                f.write(part.content)
    else:
        # Handle single response
        filename = response_headers.get('Content-Disposition').split('filename=')[1].strip('"')
        filename = result_dir_path + "/" + filename
        with open(filename, 'wb') as f:
            f.write(response_body)

def convert_tag_to_tuple(tag_number):
    """태그 번호를 문자열에서 2-튜플 형식으로 변환하는 함수.
    
    :param tag_number: 태그 번호
    :return: 2-튜플로 변환된 태그 번호
    """
    if isinstance(tag_number, str):
        # 문자열 형식의 태그를 2-튜플로 변환
        parts = tag_number.split(',')
        if len(parts) == 2:
            tag_number = (int(parts[0], 16), int(parts[1], 16))

    return tag_number  # 변환된 태그를 반환

def no_private_tag_check(result_dir_path, test_data, tag_number):
    """
    DICOM 파일에서 특정 Private Tag가 존재하지 않는지 확인하는 함수
    
    :param result_dir_path: 결과물 폴더 경로 또는 결과물 파일 경로
    :param test_data: 원본 dicom 파일 이름
    :param tag_number: 확인할 태그 번호
    :return: 태그가 존재하지 않으면 True, 존재하면 False 및 존재하는 파일 리스트
    """
    # result_dir_path가 디렉토리인지 확인
    if os.path.isfile(result_dir_path):
        # 파일인 경우, 해당 파일만 검사
        file_list = [os.path.basename(result_dir_path)]
    elif os.path.isdir(result_dir_path):
        has_subfolder = any(os.path.isdir(os.path.join(result_dir_path, f)) for f in os.listdir(result_dir_path))
        if has_subfolder:
            # 하위 폴더가 있는 경우, 하위 폴더를 제외하고 파일 목록 가져오기
            file_list = [f for f in os.listdir(result_dir_path) 
                                if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]
        else:
            # 하위 폴더가 없는 경우, 결과물 파일 경로에서 원본 dicom 파일과 hl7 파일은 제외
            file_list = [f for f in os.listdir(result_dir_path) if os.path.isfile(os.path.join(result_dir_path, f)) and f.endswith('.dcm') and not f.startswith(test_data)]
    
    log.debug(f"no_private_tag_check's file list: {file_list}")
    
    # tag_number를 2-튜플 형식으로 변환
    tag_number_tuple = convert_tag_to_tuple(tag_number)

    # 태그 번호에 해당하는 태그가 존재하는지 확인
    files_with_tag = []  # 태그가 존재하는 파일 리스트 초기화
    for file in file_list:
        # result_dir_path가 파일인 경우와 디렉토리인 경우를 구분하여 처리
        file_path = result_dir_path if os.path.isfile(result_dir_path) else os.path.join(result_dir_path, file)
        ds = pydicom.dcmread(file_path, force=True)
        if tag_number_tuple in ds:
            log.debug(f"{file} 파일에 {tag_number} 태그가 존재합니다.")
            files_with_tag.append(file)  # 태그가 존재하는 파일 추가

    if files_with_tag:
        return False, files_with_tag  # 태그가 존재하는 파일 리스트 반환
    return True, []  # 태그가 존재하지 않으면 True와 빈 리스트 반환

def parse_tag_path(tag_path_str):
    """
    문자열 경로를 [Tag(...), Tag(...)] 형식으로 변환
    예: '0070,0001>0070,0008>0070,0006'
    """
    parts = tag_path_str.split(">")
    tag_list = []
    for part in parts:
        g, e = part.strip().split(",")
        tag = Tag(int(g, 16), int(e, 16))
        tag_list.append(tag)
        
    return tag_list

def get_all_values_recursive(dataset, tag_path):
    """
    중첩된 시퀀스를 따라 모든 값을 리스트로 수집
    """
    if not tag_path:
        return []

    tag = tag_path[0]

    if tag not in dataset:
        log.warning(f"Tag {tag} not found in dataset.")
        return []

    elem = dataset[tag]

    if len(tag_path) == 1:
        return [elem.value]

    remaining_path = tag_path[1:]
    values = []

    if elem.VR == "SQ":
        for item in elem.value:
            if isinstance(item, pydicom.dataset.Dataset):
                values.extend(get_all_values_recursive(item, remaining_path))

    return values

def check_dicom_tags(result_path, expected_tag_dict, test_data):
    """
    기대하는 태그 경로와 값을 확인하고, 일치 여부 반환
    result_path가 디렉토리일 경우 모든 파일을 검사하고, 파일일 경우 해당 파일만 검사합니다.
    단, test_data와 동일한 파일명을 가진 파일을 제외하거나 result_dir_path에 하위 폴더가 있는 경우 하위 폴더를 제외
    
    :param result_path: 결과물 파일 경로 또는 디렉토리 경로
    :param expected_tag_dict: {"0070,0001>0070,0008>0070,0006": "POINT"}
    :return: {tag 경로: True/False}
    """
    
    result = {}

    # result_path가 디렉토리인지 확인
    if os.path.isdir(result_path):
        # 디렉토리인 경우, 하위 폴더가 있는지 확인
        has_subfolder = any(os.path.isdir(os.path.join(result_path, f)) for f in os.listdir(result_path))

        if has_subfolder:
            # 하위 폴더가 있는 경우, 하위 폴더를 제외하고 파일 목록 가져오기
            result_files = [f for f in os.listdir(result_path) 
                            if os.path.isfile(os.path.join(result_path, f)) and f != os.path.basename(test_data)]
        else:
            # 하위 폴더가 없는 경우, test_data와 동일한 파일명을 가진 파일을 제외
            result_files = [f for f in os.listdir(result_path) 
                            if os.path.isfile(os.path.join(result_path, f)) and f != test_data]
        
        for file_name in result_files:
            file_path = os.path.join(result_path, file_name)
            try:
                dcm = pydicom.dcmread(file_path, force=True)

                for tag_path_str, expected_value in expected_tag_dict.items():
                    tag_path = parse_tag_path(tag_path_str)
                    found_values = get_all_values_recursive(dcm, tag_path)
                    actual_str_list = []
                    if found_values:  # found_values가 비어있지 않은지 확인
                        for raw in found_values:
                            if isinstance(raw, (MultiValue, list)):
                                actual_str_list.append("\\".join(str(v) for v in raw))
                            elif raw is not None:
                                actual_str_list.append(str(raw))
                    else:
                        log.warning(f"No values found for tag path: {tag_path_str}")

                    log.debug(f"[DEBUG] Path:     {tag_path_str}")
                    log.debug(f"[DEBUG] Expected: {expected_value}")
                    log.debug(f"[DEBUG] Found:    {actual_str_list}")

                    match = expected_value in actual_str_list
                    result[tag_path_str] = result.get(tag_path_str, []) + [match]

            except Exception as e:
                log.error(f"Error reading DICOM file {file_path}: {e}")

    else:
        # 파일인 경우, 해당 파일만 검사
        try:
            dcm = pydicom.dcmread(result_path, force=True)

            for tag_path_str, expected_value in expected_tag_dict.items():
                tag_path = parse_tag_path(tag_path_str)
                found_values = get_all_values_recursive(dcm, tag_path)
                actual_str_list = []
                if found_values:  # found_values가 비어있지 않은지 확인
                    for raw in found_values:
                        if isinstance(raw, (MultiValue, list)):
                            actual_str_list.append("\\".join(str(v) for v in raw))
                        elif raw is not None:
                            actual_str_list.append(str(raw))
                else:
                    log.warning(f"No values found for tag path: {tag_path_str}")

                log.debug(f"[DEBUG] Path:     {tag_path_str}")
                log.debug(f"[DEBUG] Expected: {expected_value}")
                log.debug(f"[DEBUG] Found:    {actual_str_list}")

                match = expected_value in actual_str_list
                result[tag_path_str] = match

        except Exception as e:
            log.error(f"Error reading DICOM file {result_path}: {e}")

    return result

def extract_tag_values(result_dir_path, tag_path_str, test_data):
    """
    test_data와 같은 파일명을 가진 파일(원본 dicom 파일)을 제외한 DICOM 파일들의 프라이빗 태그 값을 확인하는 함수.
    
    :param result_dir_path: 결과물 파일 경로
    :param tag_path: 태그 경로
    :param test_data: 원본 dicom 파일 이름
    :return: 태그 값
    """
    
    result = {}

    # result_dir_path가 파일인지 확인
    if os.path.isfile(result_dir_path):
        # 파일인 경우, 해당 파일만 검사
        try:
            dcm = pydicom.dcmread(result_dir_path, force=True)
            tag_path = parse_tag_path(tag_path_str)            
            found_values = get_all_values_recursive(dcm, tag_path)
            result[result_dir_path] = found_values
            # log.debug(f"[DEBUG] Extracted {tag_path} tag value: {found_values[:100]}")
        except Exception as e:
            log.error(f"Error reading DICOM file {result_dir_path}: {e}")
            return None
    
    # result_dir_path 디렉토리인지 확인
    elif os.path.isdir(result_dir_path):
        # 디렉토리인 경우, 하위 폴더가 있는지 확인
        has_subfolder = any(os.path.isdir(os.path.join(result_dir_path, f)) for f in os.listdir(result_dir_path))

        if has_subfolder:
            # 하위 폴더가 있는 경우, 하위 폴더를 제외하고 파일 목록 가져오기
            result_files = [f for f in os.listdir(result_dir_path) 
                            if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]
        else:
            # 하위 폴더가 없는 경우, test_data와 동일한 파일명을 가진 파일을 제외
            result_files = [f for f in os.listdir(result_dir_path) 
                            if os.path.isfile(os.path.join(result_dir_path, f)) and f != test_data]
        
        log.info(f"[DEBUG] result_files: {result_files}")
        
        for file_name in result_files:
            file_path = os.path.join(result_dir_path, file_name)
            dcm = pydicom.dcmread(file_path, force=True)
            tag_path = parse_tag_path(tag_path_str)
            
            log.debug(f"[DEBUG] tag_path: {tag_path}")
            log.debug(f"[DEBUG] tag_path_str: {tag_path_str}")
            
            found_values = get_all_values_recursive(dcm, tag_path)
            result[file_name] = found_values
            # log.debug(f"[DEBUG] Extracted {tag_path} tag value: {found_values[:100]}")
            
    else:
        log.error(f"Invalid result_dir_path: {result_dir_path}")
        return None
    
    # log.debug(f"[DEBUG] Extracted Result: {result}")
    return result

def change_dicom_tags_for_ignoreDuplicateSop(test_id, result_dir_path, test_data):
    """
    DICOM 파일의 태그를 수정하고, 서버로 전송하는 함수
    
    :param test_id: 테스트 케이스 ID
    :param result_dir_path: 결과물 파일 경로
    :param test_data: 원본 dicom 파일 이름
    :return: 태그 수정 결과
    """
    
    # test_data에 슬래시가 1개 이상 포함된 경우
    if '/' in test_data:
        # 마지막 서브폴더 경로 추출
        last_subfolder = os.path.dirname(test_data)
        full_folder_path = os.path.join(result_dir_path, last_subfolder)

        # full_folder_path 안의 모든 파일을 file_list에 추가
        file_list = [f for f in os.listdir(full_folder_path) if os.path.isfile(os.path.join(full_folder_path, f))]
    else:
        # test_data에 슬래시가 없는 경우 기존 로직 유지
        file_list = [f for f in os.listdir(result_dir_path) if os.path.isfile(os.path.join(result_dir_path, f)) and f != os.path.basename(test_data)]

    log.info(f"file_list: {file_list}")
    
    try:
        # 날짜 기반 ID 생성
        today = datetime.now().strftime('%Y%m%d%H%M%S')
        accession_number = f"Bulk1{datetime.now().strftime('%d%H%M%S')}"
        study_uid = f"222.2.840.1140891.0.0.{today}"

        # DICOM 파일 목록 가져오기
        if not file_list:
            log.error("No DICOM files found in the sample folder!")
            return

        # DICOM 태그 일괄 변경 (모든 파일에 동일 적용)
        for filename in file_list:
            file_path = os.path.join(result_dir_path, filename)
            try:
                ds = pydicom.dcmread(file_path, force=True)

                # 공통 태그 수정 (모든 파일 동일)
                ds.PatientID = test_id
                ds.AccessionNumber = accession_number  # 모든 파일 동일한 AccessionNumber
                ds.StudyInstanceUID = f"{study_uid}.1.0"  # 모든 파일 동일한 StudyInstanceUID
                ds.SeriesInstanceUID = f"{study_uid}.2.0"  # 모든 파일 동일한 SeriesInstanceUID
                
                ds.save_as(file_path)

            except Exception as e:
                log.error(f"Error modifying common DICOM fields in {filename}: {e}")
                return

        # SOPInstanceUID만 개별적으로 변경
        for count, filename in enumerate(file_list):
            file_path = os.path.join(result_dir_path, filename)
            try:
                ds = pydicom.dcmread(file_path, force=True)

                # SOPInstanceUID만 개별적으로 변경
                ds.SOPInstanceUID = f"{study_uid}.3.{count}"

                ds.save_as(file_path)
                log.info(f"Modified SOPInstanceUID: {filename} (SOPInstanceUID: {ds.SOPInstanceUID})")

            except Exception as e:
                log.error(f"Error modifying SOPInstanceUID in {filename}: {e}")
                return
            
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        

# Assertions 공통 함수
def score_json_assertions(result_data):
    """
    score json 응답에 관한 검증 함수

    :param result_data: score json 파일 경로
    :return: score 응답 검증 결과
    """
    
    # result_data가 파일 경로인지 확인
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            file_path = json.load(f)  # JSON 파일 내용 읽기
            
    # score, score.atelectasis, score.calcification, score.cardiomegaly, score.consolidation, score.fibrosis, score.fracture_acute, score.mediastinal_widening, score.nodule, score.pleural_effusion, score.pneumoperitoneum, score.pneumothorax' check in result json
    check.equal('score' in file_path, True, "score key is missing in the response")
    check.equal('atelectasis' in file_path['score'], True, "score.atelectasis key is missing in the response")
    check.equal('calcification' in file_path['score'], True, "score.calcification key is missing in the response")
    check.equal('cardiomegaly' in file_path['score'], True, "score.cardiomegaly key is missing in the response")
    check.equal('consolidation' in file_path['score'], True, "score.consolidation key is missing in the response")
    check.equal('fibrosis' in file_path['score'], True, "score.fibrosis key is missing in the response")
    check.equal('fracture_acute' in file_path['score'], True, "score.fracture_acute key is missing in the response")
    check.equal('mediastinal_widening' in file_path['score'], True, "score.mediastinal_widening key is missing in the response")
    check.equal('nodule' in file_path['score'], True, "score.nodule key is missing in the response")
    check.equal('pleural_effusion' in file_path['score'], True, "score.pleural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in file_path['score'], True, "score.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in file_path['score'], True, "score.pneumothorax key is missing in the response")
    
    # metascore, metascore.abnormality_score, metascore.tb_screening_score, metascore.all_findings_under_thresholds check in result json
    check.equal('metascore' in file_path, True, "metascore key is missing in the response")
    check.equal('abnormality_score' in file_path['metascore'], True, "metascore.abnormality_score key is missing in the response")
    check.equal('tb_screening_score' in file_path['metascore'], True, "metascore.tb_screening_score key is missing in the response")
    check.equal('all_findings_under_thresholds' in file_path['metascore'], True, "metascore.all_findings_under_thresholds key is missing in the response")
    
    # thresholds, thresholds.atelectasis, thresholds.calcification, thresholds.cardiomegaly, thresholds.consolidation, thresholds.fibrosis, thresholds.fracture_acute, thresholds.mediastinal_widening, thresholds.nodule, thresholds.pleural_effusion, thresholds.pneumoperitoneum, thresholds.pneumothorax, thresholds.tuberculosis check in result json 
    check.equal('thresholds' in file_path, True, "thresholds key is missing in the response")
    check.equal('atelectasis' in file_path['thresholds'], True, "thresholds.atelectasis key is missing in the response")
    check.equal('calcification' in file_path['thresholds'], True, "thresholds.calcification key is missing in the response")
    check.equal('cardiomegaly' in file_path['thresholds'], True, "thresholds.cardiomegaly key is missing in the response")
    check.equal('consolidation' in file_path['thresholds'], True, "thresholds.consolidation key is missing in the response")
    check.equal('fibrosis' in file_path['thresholds'], True, "thresholds.fibrosis key is missing in the response")
    check.equal('fracture_acute' in file_path['thresholds'], True, "thresholds.fracture_acute key is missing in the response")
    check.equal('mediastinal_widening' in file_path['thresholds'], True, "thresholds.mediastinal_widening key is missing in the response")
    check.equal('nodule' in file_path['thresholds'], True, "thresholds.nodule key is missing in the response")
    check.equal('pleural_effusion' in file_path['thresholds'], True, "thresholds.pleural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in file_path['thresholds'], True, "thresholds.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in file_path['thresholds'], True, "thresholds.pneumothorax key is missing in the response")
    check.equal('tuberculosis' in file_path['thresholds'], True, "thresholds.tuberculosis key is missing in the response")

def report_json_assertions(result_data):
    """
    report json 응답에 관한 검증 함수

    :param result_data: 1 step inference raw-data 응답 내용
    :return: report 응답 검증 결과
    """
    # result_data가 파일 경로인지 확인
    if os.path.isfile(result_data):
        with open(result_data, 'r') as f:
            result_data = json.load(f)  # JSON 파일 내용 읽기
    
    # report, report.atelectasis, report.calcification, report.cardiomegaly, report.consolidation, report.fibrosis, report.mediastinal_widening, report.nodule, report.plural_effusion, report.pneumoperitoneum, report.pneumothorax, report.fracture_acute, report.tuberculosis, title, note, caution check in result json
    check.equal('report' in result_data, True, "report key is missing in the response")
    check.equal('atelectasis' in result_data['report'], True, "report.atelectasis key is missing in the response")
    check.equal('calcification' in result_data['report'], True, "report.calcification key is missing in the response")
    check.equal('cardiomegaly' in result_data['report'], True, "report.cardiomegaly key is missing in the response")
    check.equal('consolidation' in result_data['report'], True, "report.consolidation key is missing in the response")
    check.equal('fibrosis' in result_data['report'], True, "report.fibrosis key is missing in the response")
    check.equal('mediastinal_widening' in result_data['report'], True, "report.mediastinal_widening key is missing in the response")
    check.equal('nodule' in result_data['report'], True, "report.nodule key is missing in the response")
    check.equal('pleural_effusion' in result_data['report'], True, "report.plural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in result_data['report'], True, "report.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in result_data['report'], True, "report.pneumothorax key is missing in the response")
    check.equal('fracture_acute' in result_data['report'], True, "report.fracture_acute key is missing in the response")
    check.equal('tuberculosis' in result_data['report'], True, "report.tuberculosis key is missing in the response")
    
    check.equal('title' in result_data, True, "report.title key is missing in the response")  

    check.equal('note' in result_data, True, "report.note key is missing in the response")  

    check.equal('caution' in result_data, True, "report.caution key is missing in the response")  
    
def grayscale_json_assertions(result_data):
    """
    grayscale json 응답에 관한 검증 함수

    :param result_data: 1 step inference 응답 내용
    :return: grayscale json 응답 검증 결과
    """
    # result_data가 파일 경로인지 확인
    if os.path.isfile(result_data):
        with open(result_data, 'r') as f:
            result_data = json.load(f)  # JSON 파일 내용 읽기
    
    # "result, result.frontal.findings, result.frontal,scores, result.frontal.thresholds, message" check in result json
    check.equal('result' in result_data, True, "result key is missing in the result")
    check.equal('frontal' in result_data['result'], True, "frontal key is missing in the result")
    check.equal('findings' in result_data['result']['frontal'], True, "result.frontal.findings key is missing in the result")
    check.equal('scores' in result_data['result']['frontal'], True, "result.frontal.scores key is missing in the result")
    check.equal('thresholds' in result_data['result']['frontal'], True, "result.frontal.thresholds key is missing in the result")
    check.equal('message' in result_data, True, "message key is missing in the result")
    
    # findings 구조 확인
    # findings가 비어있지 않다면 findgins key 아래에 있는 모든 list item에 "contours, annotation, lesions, area, center" key가 있는지 확인
    for item in result_data['result']['frontal']['findings']:
        check.equal('contours' in item, True, "contours key is missing in the item")
        check.equal('annotation' in item, True, "annotation key is missing in the item")
        check.equal('lesions' in item, True, "lesions key is missing in the item")
        check.equal('area' in item, True, "area key is missing in the item")
        check.equal('center' in item, True, "center key is missing in the item")
    
    # findings가 비어있지 않다면 lesions.prob key의 value는 모두 0.15 이상인지 확인
    for item in result_data['result']['frontal']['findings']:
        check.equal('lesions' in item, True, "lesions key is missing in the item")
        # 각 lesions 항목에 대해 prob 키 확인
        for lesion in item['lesions']:
            check.equal('prob' in lesion, True, "prob key is missing in the lesions")
            check.equal(lesion['prob'] >= 0.15, True, "lesions.prob key's value is not 0.15 or more")
    
    # scores 구조 확인
    # "abnormality_score, cardiomegaly, mediastinal_widening, tb_detection_score" key가 있는지 확인
    check.equal('abnormality_score' in result_data['result']['frontal']['scores'], True, "abnormality_score key is missing in the scores")
    check.equal('cardiomegaly' in result_data['result']['frontal']['scores'], True, "cardiomegaly key is missing in the scores")
    check.equal('mediastinal_widening' in result_data['result']['frontal']['scores'], True, "mediastinal_widening key is missing in the scores")
    check.equal('tb_detection_score' in result_data['result']['frontal']['scores'], True, "tb_detection_score key is missing in the scores")

def color_json_assertions(result_data):
    """
    color json 응답에 관한 검증 함수

    :param result_data: 1 step inference 응답 내용
    :return: color json 응답 검증 결과
    """
    # result_data가 파일 경로인지 확인
    if os.path.isfile(result_data):
        with open(result_data, 'r') as f:
            result_data = json.load(f)  # JSON 파일 내용 읽기
            
    # "result, result.frontal.pos_map, result.frontal,scores, result.frontal.thresholds, message" check in result json
    check.equal('result' in result_data, True, "result key is missing in the result")
    check.equal('frontal' in result_data['result'], True, "frontal key is missing in the result")
    check.equal('pos_map' in result_data['result']['frontal'], True, "result.frontal.pos_map key is missing in the result")
    check.equal('scores' in result_data['result']['frontal'], True, "result.frontal.scores key is missing in the result")
    check.equal('thresholds' in result_data['result']['frontal'], True, "result.frontal.thresholds key is missing in the result")
    check.equal('message' in result_data, True, "message key is missing in the result")
    
    # pos_map 구조 확인
    # pos_map 하위에 "atelectasis, calcification, consolidation, fibrosis, nodule, pleural_effusion, pneumoperitoneum, pneumothorax, tuberculosis" key가 있는지 확인
    check.equal('atelectasis' in result_data['result']['frontal']['pos_map'], True, "atelectasis key is missing in the pos_map")
    check.equal('calcification' in result_data['result']['frontal']['pos_map'], True, "calcification key is missing in the pos_map")
    check.equal('consolidation' in result_data['result']['frontal']['pos_map'], True, "consolidation key is missing in the pos_map")
    check.equal('fibrosis' in result_data['result']['frontal']['pos_map'], True, "fibrosis key is missing in the pos_map")
    check.equal('nodule' in result_data['result']['frontal']['pos_map'], True, "nodule key is missing in the pos_map")
    check.equal('pleural_effusion' in result_data['result']['frontal']['pos_map'], True, "pleural_effusion key is missing in the pos_map")
    check.equal('pneumoperitoneum' in result_data['result']['frontal']['pos_map'], True, "pneumoperitoneum key is missing in the pos_map")
    check.equal('pneumothorax' in result_data['result']['frontal']['pos_map'], True, "pneumothorax key is missing in the pos_map")
    check.equal('tuberculosis' in result_data['result']['frontal']['pos_map'], True, "tuberculosis key is missing in the pos_map")
    # post_map 하위에 "cardiomegaly, mediastinal_widening" key가 없는지 확인
    check.equal('cardiomegaly' not in result_data['result']['frontal']['pos_map'], True, "cardiomegaly key is present in the pos_map")
    check.equal('mediastinal_widening' not in result_data['result']['frontal']['pos_map'], True, "mediastinal_widening key is present in the pos_map")
    
    # scores 하위에 "abnormality_score, cardiomegaly, mediastinal_widening, tb_detection_score" key가 있는지 확인
    check.equal('abnormality_score' in result_data['result']['frontal']['scores'], True, "abnormality_score key is missing in the scores")
    check.equal('cardiomegaly' in result_data['result']['frontal']['scores'], True, "cardiomegaly key is present in the scores")
    check.equal('mediastinal_widening' in result_data['result']['frontal']['scores'], True, "mediastinal_widening key is present in the scores")
    check.equal('tb_detection_score' in result_data['result']['frontal']['scores'], True, "tb_detection_score key is missing in the scores")

def combined_json_assertions(result_data):
    """
    combined json 응답에 관한 검증 함수

    :param result_data: 1 step inference 응답 내용
    :return: combined json 응답 검증 결과
    """
    grayscale_json_assertions(result_data)
    color_json_assertions(result_data)

def is_jpg_file(result, response_headers):
    """
    JPG 파일 응답에 관한 검증 함수

    :param result: 1 step inference 응답 내용
    :param response_headers: 응답 헤더
    :return: JPG 파일 응답 검증 결과
    """
    # result가 JPG 형식인지 확인
    check.equal(isinstance(result, bytes), True, "The result is not in bytes format.")  # result가 bytes 형식인지 확인
    # JPG 형식인지 확인 (첫 3바이트가 JPG 파일의 시작 바이트)
    check.equal(result[:3] == b'\xff\xd8\xff', True, "The result is not a valid JPG file.")  # JPG 파일의 시작 바이트 확인
    # 응답 헤더의 Content-Type 확인
    check.equal(response_headers.get('Content-Type') == 'image/jpeg', True, "The Content-Type is not 'image/jpeg'.")  # Content-Type 확인
    
def is_normal_result(result_dir_path, test_data):
    """
    결과물 파일이 NORMAL tag를 가지고 있는 파일인지 확인 하는 함수
    단, 원본 dicom 파일과 hl7 파일은 확인 대상에서 제외

    :param result_dir_path: 결과물 파일 경로
    :param test_data: 원본 dicom 파일 이름
    :return: normal 결과를 가지고 있지 않은 파일명들의 리스트
    """
    # 결과물 파일 경로에서 원본 dicom 파일과 hl7 파일은 제외
    file_list = [f for f in os.listdir(result_dir_path) if os.path.isfile(os.path.join(result_dir_path, f)) and f.endswith('.dcm') and not f.startswith(test_data)]
    
    # normal 결과를 가지고 있지 않은 파일명 리스트
    non_normal_files = []

    # 결과물 파일들의 0009,1009 태그 값이 NORMAL 인지 확인
    for file in file_list:
        # DICOM 파일 열기
        ds = pydicom.dcmread(os.path.join(result_dir_path, file))
        # 0009,1009 태그 값 확인
        tag_value = ds.get((0x0009, 0x1009)).value  # 태그를 튜플로 가져오기
        if tag_value is None or tag_value != 'NORMAL':
            non_normal_files.append(file)
            
    return non_normal_files

def normal_flagging_score_json_assertions(result_data):
    """
    normal flagging 활성화 시 score json 응답에 관한 검증 함수

    :param result_data: score json 파일 경로
    :return: score 응답 검증 결과
    """

    # score0.json 파일이 존재하고 실제 파일인지 확인 후 JSON 파일 내용 읽기
    if os.path.isfile(result_data):
        with open(result_data, 'r', encoding='utf-8') as f:
            result_data = json.load(f) 
    else:
        print(f"{result_data} 파일이 존재하지 않거나 올바른 파일이 아닙니다.")

    # score, score.atelectasis, score.calcification, score.cardiomegaly, score.consolidation, score.fibrosis, score.fracture_acute, score.mediastinal_widening, score.nodule, score.pleural_effusion, score.pneumoperitoneum, score.pneumothorax, score.normal_flagging' check in result json
    check.equal('score' in result_data, True, "score key is missing in the response")
    check.equal('atelectasis' in result_data['score'], True, "score.atelectasis key is missing in the response")
    check.equal('calcification' in result_data['score'], True, "score.calcification key is missing in the response")
    check.equal('cardiomegaly' in result_data['score'], True, "score.cardiomegaly key is missing in the response")
    check.equal('consolidation' in result_data['score'], True, "score.consolidation key is missing in the response")
    check.equal('fibrosis' in result_data['score'], True, "score.fibrosis key is missing in the response")
    check.equal('fracture_acute' in result_data['score'], True, "score.fracture_acute key is missing in the response")
    check.equal('mediastinal_widening' in result_data['score'], True, "score.mediastinal_widening key is missing in the response")
    check.equal('nodule' in result_data['score'], True, "score.nodule key is missing in the response")
    check.equal('pleural_effusion' in result_data['score'], True, "score.pleural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in result_data['score'], True, "score.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in result_data['score'], True, "score.pneumothorax key is missing in the response")
    check.equal('normal_flagging' in result_data['score'], True, "score.normal_flagging key is missing in the response")

    
    # metascore, metascore.abnormality_score, metascore.tb_screening_score, metascore.all_findings_under_thresholds check in result json
    check.equal('metascore' in result_data, True, "metascore key is missing in the response")
    check.equal('abnormality_score' in result_data['metascore'], True, "metascore.abnormality_score key is missing in the response")
    check.equal('tb_screening_score' in result_data['metascore'], True, "metascore.tb_screening_score key is missing in the response")
    check.equal('all_findings_under_thresholds' in result_data['metascore'], True, "metascore.all_findings_under_thresholds key is missing in the response")
    
    # thresholds, thresholds.atelectasis, thresholds.calcification, thresholds.cardiomegaly, thresholds.consolidation, thresholds.fibrosis, thresholds.fracture_acute, thresholds.mediastinal_widening, thresholds.nodule, thresholds.pleural_effusion, thresholds.pneumoperitoneum, thresholds.pneumothorax, thresholds.normal_flagging, thresholds.tuberculosis check in result json 
    check.equal('thresholds' in result_data, True, "thresholds key is missing in the response")
    check.equal('atelectasis' in result_data['thresholds'], True, "thresholds.atelectasis key is missing in the response")
    check.equal('calcification' in result_data['thresholds'], True, "thresholds.calcification key is missing in the response")
    check.equal('cardiomegaly' in result_data['thresholds'], True, "thresholds.cardiomegaly key is missing in the response")
    check.equal('consolidation' in result_data['thresholds'], True, "thresholds.consolidation key is missing in the response")
    check.equal('fibrosis' in result_data['thresholds'], True, "thresholds.fibrosis key is missing in the response")
    check.equal('fracture_acute' in result_data['thresholds'], True, "thresholds.fracture_acute key is missing in the response")
    check.equal('mediastinal_widening' in result_data['thresholds'], True, "thresholds.mediastinal_widening key is missing in the response")
    check.equal('nodule' in result_data['thresholds'], True, "thresholds.nodule key is missing in the response")
    check.equal('pleural_effusion' in result_data['thresholds'], True, "thresholds.pleural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in result_data['thresholds'], True, "thresholds.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in result_data['thresholds'], True, "thresholds.pneumothorax key is missing in the response")
    check.equal('normal_flagging' in result_data['thresholds'], True, "thresholds.normal_flagging key is missing in the response")
    check.equal('tuberculosis' in result_data['thresholds'], True, "thresholds.tuberculosis key is missing in the response")

def normal_flagging_report_json_assertions(result_data):
    """
    normal flagging 활성화 시 report json 응답에 관한 검증 함수

    :param result_data: report json 파일 경로
    :return: report 응답 검증 결과
    """

    # report0.json 파일이 존재하고 실제 파일인지 확인 후 JSON 파일 내용 읽기
    if os.path.isfile(result_data):
        with open(result_data, 'r', encoding='utf-8') as f:
            result_data = json.load(f) 
    else:
        print(f"{result_data} 파일이 존재하지 않거나 올바른 파일이 아닙니다.")

    # report, report.atelectasis, report.calcification, report.cardiomegaly, report.consolidation, report.fibrosis, report.mediastinal_widening, report.nodule, report.plural_effusion, report.pneumoperitoneum, report.pneumothorax, report.fracture_acute, report.tuberculosis, title, note, caution check in result json
    check.equal('report' in result_data, True, "report key is missing in the response")
    check.equal('atelectasis' in result_data['report'], True, "report.atelectasis key is missing in the response")
    check.equal('calcification' in result_data['report'], True, "report.calcification key is missing in the response")
    check.equal('cardiomegaly' in result_data['report'], True, "report.cardiomegaly key is missing in the response")
    check.equal('consolidation' in result_data['report'], True, "report.consolidation key is missing in the response")
    check.equal('fibrosis' in result_data['report'], True, "report.fibrosis key is missing in the response")
    check.equal('mediastinal_widening' in result_data['report'], True, "report.mediastinal_widening key is missing in the response")
    check.equal('nodule' in result_data['report'], True, "report.nodule key is missing in the response")
    check.equal('pleural_effusion' in result_data['report'], True, "report.plural_effusion key is missing in the response")
    check.equal('pneumoperitoneum' in result_data['report'], True, "report.pneumoperitoneum key is missing in the response")
    check.equal('pneumothorax' in result_data['report'], True, "report.pneumothorax key is missing in the response")
    check.equal('fracture_acute' in result_data['report'], True, "report.fracture_acute key is missing in the response")
    check.equal('tuberculosis' in result_data['report'], True, "report.tuberculosis key is missing in the response")
    
    check.equal('title' in result_data, True, "report.title key is missing in the response")  
    
    check.equal('note' in result_data, True, "report.note key is missing in the response")  

    check.equal('caution' in result_data, True, "report.caution key is missing in the response")  

def check_error_response_body(response_body):
    """
    API 실패 시 응답 내용에 관한 검증 함수

    :param response_body: 오류 응답 내용
    """
    # 오류 응답 내용에 관한 검증
    actual_message = response_body.get("message")
    actual_status = response_body.get("status")
    actual_code = response_body.get("code")
    actual_insight_error_code = response_body.get("insight_error_code")
    
    # error_mapping에서 해당 메시지에 대한 매핑 찾기
    error_info = error_mapping.get(actual_message)
    
    # error_info가 없는 경우 실패 처리
    check.equal(error_info is not None, True, f"Unrecognized error message: {actual_message}. Please check the error_mapping.py file.")
    
    # error_info가 있는 경우, status, code, insight_error_code가 일치하는지 확인
    if error_info:
        check.equal(error_info["expected_status"], actual_status, f"Expected status {error_info['expected_status']} but got {actual_status}")
        check.equal(error_info["expected_code"], actual_code, f"Expected code {error_info['expected_code']} but got {actual_code}")
        check.equal(error_info["expected_insight_error_code"], actual_insight_error_code, f"Expected insight_error_code {error_info['expected_insight_error_code']} but got {actual_insight_error_code}")

def compare_hl7_file_with_expected(hl7_file_path, expected_fields):
     """
     HL7 파일을 읽고 세그먼트를 파싱한 뒤,
     기대값 딕셔너리와 완전 일치하는지 검증하는 함수.
 
     MSH 세그먼트는 HL7 규약에 따라 MSH.1 = '|' 로 처리합니다.
 
     :param hl7_file_path: HL7 메시지를 포함하는 파일 경로
     :param expected_fields: 기대값 딕셔너리 (예: {"MSH.1.2": "^~\\&", "OBX.2.5": "92.87"})
     """
 
     # 1. 파일 읽기
     try:
         with open(hl7_file_path, "r", encoding="utf-8") as f:
             hl7_str = f.read()
     except Exception as e:
         raise RuntimeError(f"HL7 파일을 읽을 수 없습니다: {hl7_file_path} ({e})")
 
     # 2. 줄바꿈 통일 및 분리
     hl7_str = hl7_str.replace("\r", "\n")
     lines = [line.strip() for line in hl7_str.strip().split("\n") if line]
 
     field_map = {}         # 예: {"MSH.1.3": "Lunit", "OBX.2.5": "92.87"}
     segment_counter = {}   # 세그먼트 등장 순서 추적용
 
     for line in lines:
         parts = line.split("|")
         seg_type = parts[0]
 
         # MSH는 MSH.1이 필드 구분자 그 자체이므로 수동으로 삽입
         if seg_type == "MSH":
             fields = ["|"] + parts[1:]  # MSH.1 = '|', MSH.2 = '^~\\&', ...
         else:
             fields = parts[1:]         # 일반 세그먼트는 2번째부터 필드 시작
 
         # 세그먼트별 순서 추적 (MSH.1, OBX.2 등)
         segment_counter.setdefault(seg_type, 1)
         seg_index = segment_counter[seg_type]
 
         # 각 필드를 고유 키로 저장 (예: OBX.2.5)
         for i, value in enumerate(fields, start=1):
             key = f"{seg_type}.{seg_index}.{i}"
             field_map[key] = value
 
         segment_counter[seg_type] += 1
 
     # 3. 기대값 비교 (모든 값이 완전히 일치해야 통과)
     for key, expected_value in expected_fields.items():
         actual_value = field_map.get(key)
         check.equal(
             actual_value,
             expected_value,
             f"Mismatch at {key}: expected '{expected_value}', got '{actual_value}'"
         )

def check_jpg_map_type(result_file_path):
    """
    JPG 이미지의 가로 세로 비율에 따라 map_type을 반환하는 함수.

    :param result_file_path: JPG 이미지 파일 경로
    :return: 'report', 'additional', 또는 'map' 중 하나
    """
    try:
        with Image.open(result_file_path) as img:
            width, height = img.size  # 이미지의 가로와 세로 크기 가져오기
            log.info(f"Image dimensions: {width}x{height}")

            # 가로 세로 비율에 따른 map_type 결정
            if width == 1500 and height == 1700:
                return 'report'
            elif width == 1200 and height == 1100:
                return 'additional'
            elif width == 1200 and height != 1100:
                return 'map'
            else:
                log.warning(f"Unexpected dimensions: {width}x{height}. Returning unknown map type.")
                return 'unknown'

    except Exception as e:
        log.error(f"Error checking JPG map type for {result_file_path}: {e}")
        return 'unknown'  # 오류 발생 시 기본값으로 'unknown' 반환

def check_jpg_color_type(result_file_path):
    """
    JPG 파일의 색상 타입을 확인하는 함수.

    :param result_file_path: JPG 파일 경로
    :return: 'color' 또는 'grayscale'
    """
    try:
        # JPG 파일 열기
        img = Image.open(result_file_path)
        log.debug(f"Image mode: {img.mode}")
        
        # 색상 타입 확인
        if img.mode == 'RGB':
            return 'color'
        elif img.mode == 'L':
            return 'grayscale'
        else:
            return 'unknown'
    except Exception as e:
        log.error(f"Error checking JPG color type for {result_file_path}: {e}")
        return 'unknown'
    
def check_output_type_counts(result_counts, expected_counts):
    """
    output_type_check 함수의 결과를 검증하는 공통 함수.
    반복되는 check.equal 문장들을 단순화합니다.
    
    :param result_counts: output_type_check 함수에서 반환된 결과 딕셔너리
    :param expected_counts: 기대하는 결과 딕셔너리 (예: {"sc_map": 1, "sc_report": 1, "gsps": 0, "sr": 0, "hl7": 0, "unknown": 0})
    """
    # 파일 타입별 메시지 매핑
    file_type_messages = {
        "sc_map": "SC map file",
        "sc_report": "SC report file", 
        "sc_additional": "Additional SC file",
        "gsps": "GSPS file",
        "sr": "BasicTextSR file",
        "hl7": "HL7 file",
        "unknown": "unknown file"
    }
    
    # 각 파일 타입에 대해 검증 수행
    for file_type, expected_count in expected_counts.items():
        if file_type in result_counts:
            actual_count = result_counts[file_type]
            message = f"Mismatch in expected number of {file_type_messages.get(file_type, file_type)} in the results"
            check.equal(actual_count, expected_count, message)
        else:
            log.warning(f"File type '{file_type}' not found in result_counts. Available types: {list(result_counts.keys())}")
            check.equal(0, expected_count, f"Expected {file_type} count not found in results")

def check_expected_logs(expected_logs, component, timeout=60):
    """
    Check for expected log messages in a remote log file.
    
    This function connects to a remote server via SSH and monitors a log file
    for specific expected log messages. It reads the log file in real-time
    and checks if all expected log messages appear within the specified timeout.
    
    :param expected_logs: List of expected log messages to search for
    :param component: Components you want to check
    :param timeout: Maximum time to wait for logs in seconds (default: 60)
    :return: True if all expected logs are found, False otherwise
    """
    today_str = datetime.now().strftime("%Y%m%d")
    time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    found_logs = set()
    start_time = time.time()
    last_log_time = None  # Most recent valid log time seen
    
    if component == "GW":
        remote_log_path = f"{CXR_GW_LOG_PATH}/CXR-GW.log"
    elif component == "IS":
        remote_log_path = f"{CXR_IS_LOG_PATH}/CXR-IS.log"
    log.debug(f"Check the log file : {remote_log_path}")

    global base_time
    if base_time is None:
        log.error("[ERROR] base_time is not set.")
        return False

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=CXR_IP,
            port=SSH_PORT,
            username=SSH_USER_NAME,
            password=SSH_USER_PASSWORD
        )

        while time.time() - start_time < timeout:
            command = f"tail -n 100 {remote_log_path}"
            stdin, stdout, stderr = client.exec_command(command)
            log_raw = stdout.read()

            try:
                log_content = log_raw.decode("utf-8")
            except UnicodeDecodeError:
                log.warning("[WARN] UTF-8 decode failed, falling back to latin-1")
                log_content = log_raw.decode("latin-1")

            for line in log_content.splitlines():
                raw_line = line
                line = line.strip().replace('\r', '').replace('\t', '')

                # Extract timestamp (update if found)
                start_idx = line.find("[20")
                end_idx = line.find("]", start_idx)
                if start_idx != -1 and end_idx != -1:
                    timestamp_str = line[start_idx + 1:end_idx]
                    try:
                        last_log_time = datetime.strptime(timestamp_str, time_format)
                    except Exception as e:
                        log.warning(f"[WARN] Timestamp parse failed: {e}")
                        continue

                # Check if log time is valid
                if last_log_time is None or last_log_time <= base_time:
                    continue

                # Detect expected logs
                for expected in expected_logs:
                    normalized_expected = expected.strip().replace('\r', '').replace('\t', '')
                    if normalized_expected in line:
                        found_logs.add(expected)
                        log.debug(f"[MATCH] {expected} in {repr(raw_line)}")

                if all(exp in found_logs for exp in expected_logs):
                    log.debug("All expected logs found.")
                    client.close()
                    return True

            time.sleep(2)

        client.close()

    except Exception as e:
        log.error(f"[ERROR] Remote log access failed: {e}")
        return False

    missing = [exp for exp in expected_logs if exp not in found_logs]
    if missing:
        log.error(f"Timeout reached. Missing logs: {missing}")
    return False

def _manage_env_file(ssh, component, env_add, env_remove, env_override):
    """
    Internal function to backup .env file and add, modify, or remove specific settings
    
    :param ssh: SSH client object
    :param component: Component to modify .env file (GW, IS available)
    :param env_add: Dictionary of environment variables to add
    :param env_remove: Dictionary of environment variables to remove (only keys are used, values are ignored)
    :param env_override: Dictionary of environment variables to override
    :return: Backup success status
    """
    if component not in ['GW', 'IS']:
        log.error(f"[Error][_manage_env_file] {component} is not supported")
        return False
    
    if component == 'GW':
        component_dir_path = CXR_GW_CONFIG_PATH
    elif component == 'IS':
        component_dir_path = CXR_IS_CONFIG_PATH
    
    def _sudo_execute(command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write('1q2w3e4r%t\n')
        stdin.flush()
        exit_status = stdout.channel.recv_exit_status()
        return stdin, stdout, stderr, exit_status

    # Backup only when .env file modification is needed
    if len(env_add) or len(env_remove) or len(env_override):
        backup_cmd = f'sudo -S sh -c "cd {component_dir_path} && cp .env .env_restart_container.bak"'
        log.debug(f"[_manage_env_file]: backup .env → {backup_cmd}")
        stdin, stdout, stderr, exit_status = _sudo_execute(backup_cmd)
        if exit_status != 0:
            error_msg = stderr.read().decode('utf-8')
            raise RuntimeError(f"failed to backup component env: {error_msg}")

        # Add environment variables to .env file
        if len(env_add):
            add_cmd = f'sudo -S sh -c "cd {component_dir_path} && printf \\"'
            for key in env_add:
                add_cmd += f'{key}={env_add[key]}\\n'
            add_cmd += '\\" >> .env"'
            log.debug(f"[_manage_env_file]: add new .env → {add_cmd}")
            stdin, stdout, stderr, exit_status = _sudo_execute(add_cmd)
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8')
                raise RuntimeError(f"failed to add new env: {error_msg}")
            new_env_file_path = os.path.join(component_dir_path, '.env')
            _sync_env_from_container(ssh, component, new_env_file_path)

        # Remove environment variables from .env file
        if len(env_remove):
            remove_cmd = f"sudo -S sh -c \"cd {component_dir_path} && sed -i '/"
            for i, key in enumerate(env_remove.keys()):
                remove_cmd += f"{key}"
                if i < len(env_remove) - 1:
                    remove_cmd += "|"
            remove_cmd += "/d' .env\""
            log.debug(f"[_manage_env_file]: remove .env → {remove_cmd}")
            stdin, stdout, stderr, exit_status = _sudo_execute(remove_cmd)
            if exit_status != 0:
                error_msg = stderr.read().decode('utf-8')
                raise RuntimeError(f"failed to remove env: {error_msg}")

        # Override environment variables in .env file (replace existing values)
        if len(env_override):
            for key, value in env_override.items():
                # Check if existing line exists and replace it
                override_cmd = f"sudo -S sh -c \"cd {component_dir_path} && sed -i 's/^{key}=.*/{key}={value}/' .env\""
                log.debug(f"[_manage_env_file]: override .env → {override_cmd}")
                stdin, stdout, stderr, exit_status = _sudo_execute(override_cmd)
                if exit_status != 0:
                    error_msg = stderr.read().decode('utf-8')
                    raise RuntimeError(f"failed to override env {key}: {error_msg}")
        
        return True
    return False

def down_docker_container(ssh, component):
    """
    Function to stop Docker container
    
    :param ssh: SSH client object
    :param component: Component name (GW, IS)
    :return: Stop success status
    """
    if component == 'GW':
        component_dir_path = CXR_GW_CONFIG_PATH
    elif component == 'IS':
        component_dir_path = CXR_IS_CONFIG_PATH
    
    def _sudo_execute(command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write('1q2w3e4r%t\n')
        stdin.flush()
        exit_status = stdout.channel.recv_exit_status()
        return stdin, stdout, stderr, exit_status

    down_cmd = f'sudo -S sh -c "cd {component_dir_path} && docker compose down;"'
    log.debug(f"[_down_docker_container] ({component}): down → {down_cmd}")
    stdin, stdout, stderr, exit_status = _sudo_execute(down_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        raise RuntimeError(f"failed to down docker container: {error_msg}")
    
    return True

def start_docker_container(ssh, component):
    """
    Function to start Docker container
    
    :param ssh: SSH client object
    :param component: Component name
    :return: (Start success status, Docker log)
    """
    if component == 'GW':
        component_dir_path = CXR_GW_CONFIG_PATH
    elif component == 'IS':
        component_dir_path = CXR_IS_CONFIG_PATH
    
    def _sudo_execute(command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write('1q2w3e4r%t\n')
        stdin.flush()
        exit_status = stdout.channel.recv_exit_status()
        return stdin, stdout, stderr, exit_status
    
    # Start Docker container
    start_cmd = f'sudo -S sh -c "cd {component_dir_path} && docker compose up -d"'
    log.debug(f"[_start_docker_container] ({component})")
    stdin, stdout, stderr, exit_status = _sudo_execute(start_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        raise RuntimeError(f"failed to start docker container: {error_msg}")

    # Check Docker logs to verify if docker container is running properly
    if component == 'GW':
        time.sleep(10)
    elif component == 'IS':
        time.sleep(60)
        
    grep_docker_log_cmd = f'sudo -S sh -c "cd {component_dir_path} && docker compose logs -t -n 1000"'
    log.debug(f"[_start_docker_container] ({component}): grep docker log")
    stdin, stdout, stderr, exit_status = _sudo_execute(grep_docker_log_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        raise RuntimeError(f"failed to read docker log: {error_msg}")

    docker_log = stdout.read().decode('utf-8')
    
    if component == 'GW':
        start_log = "CXR App Configuration"
    elif component == 'IS':
        start_log = "Initialization done."

    if start_log not in docker_log:
        log.error(f"[ERROR][_start_docker_container] ({component}): {start_log} not found; restart may fail")
        return False, docker_log

    log.debug(f"[_start_docker_container] ({component}): start successfully")
    return True, docker_log

def _sync_env_from_container(ssh, component, env_file_path, exclude_keys=None):
    """
    Internal function to get environment variables from currently running Docker container and overwrite existing keys in .env file
    
    :param ssh: SSH client object
    :param component: Component name ('GW' or 'IS')
    :param env_file_path: .env file path
    :param exclude_keys: Set of keys to exclude from synchronization
    :return: Synchronization success status
    """
    def _sudo_execute(command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write('1q2w3e4r%t\n')
        stdin.flush()
        exit_status = stdout.channel.recv_exit_status()
        return stdin, stdout, stderr, exit_status

    if component not in ['GW', 'IS']:
        log.error(f"[Error][_sync_env_from_container] {component} is not supported")
        return False
    
    # Determine path by component
    if component == 'GW':
        component_dir_path = CXR_GW_CONFIG_PATH
    elif component == 'IS':
        component_dir_path = CXR_IS_CONFIG_PATH
    
    # Get container name from docker-compose.yml file
    read_compose_cmd = f'sudo -S sh -c "cd {component_dir_path} && cat docker-compose.yml"'
    log.debug(f"[_sync_env_from_container] ({component}): read docker-compose.yml → {read_compose_cmd}")
    
    stdin, stdout, stderr, exit_status = _sudo_execute(read_compose_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        log.error(f"[ERROR][_sync_env_from_container] ({component}): failed to read docker-compose.yml: {error_msg}")
        return False
    
    compose_content = stdout.read().decode('utf-8')
    
    # Extract container_name from the first service in services section of docker-compose.yml
    # Modified pattern to match actual docker-compose.yml structure (support service names with hyphens)
    services_pattern = r'services:\s*\n\s*([^:]+):\s*\n(?:[^\n]*\n)*?\s*container_name:\s*([^\n]+)'
    services_match = re.search(services_pattern, compose_content, re.MULTILINE | re.DOTALL)
    
    if not services_match:
        # If container_name is not found, extract only service name using default pattern
        services_match = re.search(r'services:\s*\n\s*([^:]+):', compose_content)
        if not services_match:
            log.error(f"[ERROR][_sync_env_from_container] ({component}): no services found in docker-compose.yml")
            return False
        
        service_name = services_match.group(1).strip()
        container_name = f"{component_dir_path.split('/')[-1]}-{service_name}"
        log.debug(f"[_sync_env_from_container] ({component}): no container_name found, using default: {container_name}")
    else:
        container_name = services_match.group(2).strip()
        log.debug(f"[_sync_env_from_container] ({component}): found container_name in docker-compose.yml: {container_name}")
    
    try:
        # 1. Get environment variables from Docker container
        printenv_cmd = f'sudo -S sh -c "docker exec {container_name} printenv"'
        log.debug(f"[_sync_env_from_container] ({component}): get container env → {printenv_cmd}")
        
        stdin, stdout, stderr, exit_status = _sudo_execute(printenv_cmd)
        if exit_status != 0:
            error_msg = stderr.read().decode('utf-8')
            log.error(f"[ERROR][_sync_env_from_container] ({component}): failed to get container env: {error_msg}")
            return False
        
        container_env_output = stdout.read().decode('utf-8')
        
        # 2. Parse container environment variables into dictionary
        container_env_dict = {}
        for line in container_env_output.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                container_env_dict[key] = value
        
        log.debug(f"[_sync_env_from_container] ({component}): found {len(container_env_dict)} environment variables in container")
        
        # 3. Read .env file
        read_env_cmd = f'sudo -S sh -c "cd {component_dir_path} && cat .env"'
        log.debug(f"[_sync_env_from_container] ({component}): read .env file → {read_env_cmd}")
        
        stdin, stdout, stderr, exit_status = _sudo_execute(read_env_cmd)
        if exit_status != 0:
            error_msg = stderr.read().decode('utf-8')
            log.error(f"[ERROR][_sync_env_from_container] ({component}): failed to read .env file: {error_msg}")
            return False
        
        env_file_content = stdout.read().decode('utf-8')
        
        # 4. Parse existing keys from .env file
        env_file_dict = {}
        for line in env_file_content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_file_dict[key] = value
        
        log.debug(f"[_sync_env_from_container] ({component}): found {len(env_file_dict)} environment variables in .env file")
        
        # 5. Overwrite existing keys in .env file with container values (excluding exclude_keys)
        updated_count = 0
        excluded_count = 0
        for env_key in env_file_dict.keys():
            if env_key in container_env_dict:
                # Exclude keys that are in exclude_keys from synchronization
                if exclude_keys and env_key in exclude_keys:
                    log.debug(f"[_sync_env_from_container] ({component}): excluding {env_key} from sync (duplicate key)")
                    excluded_count += 1
                    continue
                
                container_value = container_env_dict[env_key].replace('|', '\\|')  # Escape | character
                update_cmd = f"sudo -S sh -c \"cd {component_dir_path} && sed -i 's|^{env_key}=.*|{env_key}={container_value}|' .env\""
                log.debug(f"[_sync_env_from_container] ({component}): update {env_key} → {update_cmd}")
                
                stdin, stdout, stderr, exit_status = _sudo_execute(update_cmd)
                if exit_status != 0:
                    error_msg = stderr.read().decode('utf-8')
                    log.warning(f"[WARNING][_sync_env_from_container] ({component}): failed to update {env_key}: {error_msg}")
                else:
                    updated_count += 1
                    log.debug(f"[_sync_env_from_container] ({component}): updated {env_key} = {container_env_dict[env_key]}")
        
        log.info(f"[_sync_env_from_container] ({component}): successfully updated {updated_count} environment variables, excluded {excluded_count} duplicate keys")
        return True
        
    except Exception as e:
        log.error(f"[ERROR][_sync_env_from_container] ({component}): unexpected error: {e}")
        return False

def _restore_original_env_file(ssh, component, env_override_status=False, env_override=None):
    """
    Internal function to remove changes made by adding, modifying, or removing settings for .env file restoration, and get environment variables from currently running Docker container to overwrite existing keys in .env file
    
    :param ssh: SSH client object
    :param component: Component name ('GW' or 'IS')
    :param env_override_status: Whether or not an override occurred in the env file
    :param env_override: 
    :return: Restore success status
    """
    def _sudo_execute(command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write('1q2w3e4r%t\n')
        stdin.flush()
        exit_status = stdout.channel.recv_exit_status()
        return stdin, stdout, stderr, exit_status

    if component not in ['GW', 'IS']:
        log.error(f"[Error][_restore_original_env_file] {component} is not supported")
        return False
    
    # Determine path by component
    if component == 'GW':
        component_dir_path = CXR_GW_CONFIG_PATH
    elif component == 'IS':
        component_dir_path = CXR_IS_CONFIG_PATH

    overrided_keys = set()  # Initialize variable for function scope
    
    if env_override_status and len(env_override) > 0:
        overrided_keys = env_override.keys()

    # 1. Delete .env file
    rm_env_cmd = f'sudo -S sh -c "cd {component_dir_path} && rm -f .env"'
    log.debug(f"[_restore_original_env_file] ({component}): remove .env → {rm_env_cmd}")
    stdin, stdout, stderr, exit_status = _sudo_execute(rm_env_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        log.error(f"[ERROR][_restore_original_env_file] ({component}): failed to remove .env: {error_msg}")
        return False

    # 2. Rename .env_restart_container.bak file to .env
    mv_cmd = f'sudo -S sh -c "cd {component_dir_path} && mv .env_restart_container.bak .env"'
    log.debug(f"[_restore_original_env_file] ({component}): restore .env → {mv_cmd}")
    stdin, stdout, stderr, exit_status = _sudo_execute(mv_cmd)
    if exit_status != 0:
        error_msg = stderr.read().decode('utf-8')
        log.error(f"[ERROR][_restore_original_env_file] ({component}): failed to restore .env: {error_msg}")
        return False

    # 3. Synchronize using _sync_env_from_container function
    env_file_path = os.path.join(component_dir_path, '.env')
    sync_result = _sync_env_from_container(ssh, component, env_file_path, overrided_keys)
    if not sync_result:
        log.error(f"[ERROR][_restore_original_env_file] ({component}): failed to sync .env with container")
        return False

    log.info(f"[_restore_original_env_file] ({component}): .env restored and synced successfully")
    return True

def add_env_and_restart_component(component, env_add):
    """
    Common function to add environment variables to .env file and restart docker container

    :param component: 'GW' or 'IS'
    :param env_add: Dictionary of environment variables to add (e.g., {"KEY": "VALUE"})
    :return: (Success status, docker log)
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=CXR_IP,
        port=SSH_PORT,
        username=SSH_USER_NAME,
        password=SSH_USER_PASSWORD
    )

    # 1. Add environment variables to env file
    _manage_env_file(client, component, env_add, {}, {})

    # 2. Stop container
    down_docker_container(client, component)
    
    # 3. Start container
    start_result, docker_log = start_docker_container(client, component)

    client.close()
    
    return start_result, docker_log

def delete_env_and_restart_component(component, env_delete):
    """
    Common function to delete environment variables from .env file and restart docker container
    
    :param component: 'GW' or 'IS'
    :param env_delete: Dictionary of environment variables to delete (e.g., {"KEY": "VALUE"}), only keys are used, values are ignored. For example, use {"INSIGHT_FREE_PERCENT": "None"}.
    :return: (Success status, docker log)
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=CXR_IP,
        port=SSH_PORT,
        username=SSH_USER_NAME,
        password=SSH_USER_PASSWORD
    )
    
    # 1. Delete environment variables from env file
    _manage_env_file(client, component, {}, env_delete, {})
    
    # 2. Stop container
    down_docker_container(client, component)
    
    # 3. Start container
    start_result, docker_log = start_docker_container(client, component)

    client.close()
    
    return start_result, docker_log

def override_env_and_restart_component(component, env_override):
    """
    Common function to add environment variables to .env file and restart docker container

    :param component: 'GW' or 'IS'
    :param env_override: Dictionary of environment variables to override (e.g., {"KEY": "VALUE"})
    :return: (Success status, docker log)
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=CXR_IP,
        port=SSH_PORT,
        username=SSH_USER_NAME,
        password=SSH_USER_PASSWORD
    )

    # 1. Add environment variables to env file
    _manage_env_file(client, component, {}, {}, env_override)

    # 2. Stop container
    down_docker_container(client, component)
    
    # 3. Start container
    start_result, docker_log = start_docker_container(client, component)

    client.close()
    
    return start_result, docker_log

def restore_env_and_restart_container(component, env_override_status=False, env_override=None):
    """
    Common function to restore .env file from backup and restart docker container with restored .env file
    
    :param component: 'GW' or 'IS'
    :return: (Success status, docker log)
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=CXR_IP,
        port=SSH_PORT,
        username=SSH_USER_NAME,
        password=SSH_USER_PASSWORD
    )
    
    # 1. Restore .env file
    _restore_original_env_file(client, component, env_override_status=env_override_status, env_override=env_override)
    
    # 2. Stop container
    down_docker_container(client, component)
    
    # 3. Start container
    start_result, docker_log = start_docker_container(client, component)
    
    client.close()
    
    return start_result, docker_log