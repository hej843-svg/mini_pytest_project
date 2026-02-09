# Mini Pytest Project

CXR-4010, GAON-1000 제품을 위한 pytest 기반 자동화 테스트 프로젝트입니다.

## 목차

- [개요](#개요)
- [프로젝트 구조](#프로젝트-구조)
- [환경 설정](#환경-설정)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [테스트 유형](#테스트-유형)
- [설정 가이드](#설정-가이드)
- [주의사항](#주의사항)
- [참고 자료](#참고-자료)

## 개요

이 프로젝트는 Insight CXR 제품(CXR-4010, GAON-1000)의 기능을 자동으로 테스트하기 위한 pytest 기반 테스트 프레임워크입니다.

### 주요 기능

- **DIMSE 프로토콜 테스트**: DICOM 이미지 전송 및 결과 수신 테스트
- **1Step Inference API 테스트**: REST API를 통한 영상 분석 테스트
- **1Step Inference Raw Data API 테스트**: JSON/JPG 형식의 원시 데이터 테스트
- **QA 리포트 자동 생성**: 테스트 결과를 CSV/Excel 형식으로 자동 생성
- **다양한 출력 형식 검증**: SC map/report, GSPS, HL7, BasicTextSR 등

## 프로젝트 구조

```
mini_pytest_project/
├── conftest.py              # pytest 설정 및 픽스처
├── pytest.ini              # pytest 설정 및 환경 변수
├── qareport.py             # QA 리포트 자동 생성 플러그인
├── requirements.txt         # Python 패키지 의존성
├── tests/                   # 테스트 케이스
│   └── test_smoke_gaon100.py
├── utils/                   # 공통 유틸리티 모듈
│   ├── common_util.py       # 공통 유틸리티 함수
│   ├── cxr_common_api.py    # CXR API 공통 함수
│   ├── cxr_config.py        # Config API 함수
│   ├── cxr_1S_inference.py  # 1Step Inference API 함수
│   ├── error_mapping.py     # 에러 매핑
│   └── *.json               # 설정 파일들
└── resources/               # 테스트 리소스
    └── hl7rcv/              # HL7 수신 관련 리소스
```

## 환경 설정

### 필수 요구사항

- Python 3.8 이상
- DCMTK 라이브러리 (DICOM 전송용)
- CXR 제품 서버 접근 권한
- SSH 접속 권한 (원격 서버 설정 변경용)

### 환경 변수 설정

`pytest.ini` 파일의 `[DEFAULT]` 섹션에서 다음 환경 변수를 설정해야 합니다:

#### CXR 서버 설정
- `CXR_IP`: CXR 서버 IP 주소
- `CXR_APP_PORT`: CXR 애플리케이션 포트 (기본값: 8000)
- `CXR_SCP_PORT`: CXR SCP 포트 (기본값: 13824)
- `CXR_TOKEN`: CXR 인증 토큰
- `CXR_VERSION`: CXR 제품 버전

#### Inference 서버 설정
- `INSIGHT_API_HOST`: Inference 서버 URL
- `INSIGHT_API_KEY`: Insight API 키

#### DICOM 설정
- `SOURCE_IP`: 원본 DICOM 소스 IP 주소
- `DEST_IP`: 결과 DICOM 수신 IP 주소
- `DEST_PORT`: 결과 DICOM 수신 포트
- `DEST_AETITLE`: AE Title
- `DEST_HL7_IP`: HL7 수신 IP 주소
- `DEST_HL7_PORT`: HL7 수신 포트

#### 로컬 설정
- `DCMTK_ROOT_PATH`: DICOM 라이브러리 경로
- `RESULT_DIR`: 테스트 결과 저장 경로
- `PYTHON_ROOT_PATH`: Python 설치 경로

## 설치 방법

1. 저장소 클론:
```bash
git clone <repository-url>
cd mini_pytest_project
```

2. Python 패키지 설치:
```bash
pip install -r requirements.txt
```

3. `pytest.ini` 파일에서 환경 변수 설정 (위의 [환경 설정](#환경-설정) 참고)

## 사용 방법

### 기본 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_smoke_gaon100.py

# 특정 테스트 함수 실행
pytest tests/test_smoke_gaon100.py::test_smoke_OUTPUT_01

# 마커를 사용한 필터링
pytest -m p1  # Priority 1 테스트만 실행
pytest -m p2  # Priority 2 테스트만 실행
```

### 테스트 결과 확인

테스트 실행 후 다음 위치에서 결과를 확인할 수 있습니다:

- **CSV 리포트**: `pytest.ini`의 `qa_csv_path`에 지정된 경로
- **Excel 리포트**: `qa_auto_excel_mode = true`로 설정된 경우 자동 업데이트
- **로그 파일**: `pytest_log.txt`

## 테스트 유형

### 1. DIMSE 프로토콜 테스트 (`test_smoke_OUTPUT_*`)

DICOM 이미지를 DIMSE 프로토콜로 전송하고 결과를 수신하여 검증합니다.

- **OUTPUT_01**: Grayscale SC map 생성
- **OUTPUT_02**: Color SC map 생성
- **OUTPUT_03**: Combined SC map 생성
- **OUTPUT_04**: Grayscale SC report 생성
- **OUTPUT_05**: GSPS 생성
- **OUTPUT_06**: HL7 생성
- **OUTPUT_07**: SC map/report, GSPS, BasicTextSR, HL7 복합 생성
- **OUTPUT_08**: Normal Flagging 기능

### 2. 1Step Inference API 테스트 (`test_smoke_1S_INFERENCE_*`)

REST API를 통해 영상 분석을 수행하고 DICOM 형식의 결과를 검증합니다.

- **1S_INFERENCE_01**: Grayscale SC map 생성
- **1S_INFERENCE_02**: Color SC map 생성
- **1S_INFERENCE_03**: Combined SC map 생성
- **1S_INFERENCE_04**: Grayscale SC report 생성
- **1S_INFERENCE_05**: GSPS 생성
- **1S_INFERENCE_06**: HL7 생성
- **1S_INFERENCE_07**: SC map/report, GSPS, BasicTextSR, HL7 복합 생성
- **1S_INFERENCE_08**: Normal Flagging 기능
- **1S_INFERENCE_09**: CPC (Comparison) 기능

### 3. 1Step Inference Raw Data API 테스트 (`test_smoke_1S_RAW_*`)

REST API를 통해 영상 분석을 수행하고 JSON/JPG 형식의 원시 데이터를 검증합니다.

- **1S_RAW_01**: Score.json 생성
- **1S_RAW_02**: Normal Flagging Report.json 생성
- **1S_RAW_03**: Grayscale map.jpg 생성
- **1S_RAW_04**: Grayscale Report.jpg 생성
- **1S_RAW_05**: Color map.jpg 생성
- **1S_RAW_06**: Color Report.jpg 생성
- **1S_RAW_07**: Combined map.jpg 생성
- **1S_RAW_08**: Combined Report.jpg 생성
- **1S_RAW_09**: Grayscale.json 생성
- **1S_RAW_10**: Color.json 생성
- **1S_RAW_11**: Combined.json 생성
- **1S_RAW_12**: Grayscale Additional.jpg 생성 (CPC)

## 설정 가이드

### Destination 설정

`destination`을 두 개 이상 설정할 경우, 새롭게 추가된 destination 설정에 특정 key 설정이 `creation` key 하위에 추가되어야 합니다. 이 설정이 누락되면 `PUT /config` 시 에러가 발생할 수 있습니다.

#### 필수 설정 항목

아래 JSON 구조 내에서 `mergeType`, `normalFlagging`, `dicomSC` key 항목을 참고하세요:

```json
{
    "aeTitle": DEST_AETITLE,
    "hostName": DEST_HL7_IP,
    "port": DEST_HL7_PORT,
    "protocol": "hl7",
    "creation": {
        "createHl7": true,
        "mergeType": "partialMerge",
        "normalFlagging": {
            "title": "Report",
            "report": "FINDINGS:\nLines and tubes:[None present]\nLungs and pleural space: [No focal consolidation, pleural effusion or pneumothorax.]\nCardiac silhouette, hilar regions, and trachea: [Normal.]\nThoracic osseous structures :[Normal.]\nOverlying soft tissues: [Normal.]\nUpper abdomen: [Normal.]\nIMPRESSION:\nNormal chest radiograph."
        },
        "dicomSC": {
            "displayMode": "grayscale",
            "normalFlaggingDisplayType": "small"
        }
    }
}
```

### QA 리포트 설정

`pytest.ini` 파일의 `[pytest]` 섹션에서 QA 리포트 설정을 변경할 수 있습니다:

```ini
; CSV result file path
qa_csv_path = "./report/qa_report.csv"

; Excel automatic update mode
qa_auto_excel_mode = false

; Excel file path (target for automatic test result entry)
qa_excel_path = "/path/to/testcase.xlsm"

; Excel sheet name
qa_excel_sheet = "Sheet1"

; Test ID column header in Excel
qa_excel_id_col = "Auto Script"

; Result entry column header in Excel
qa_excel_result_col = "Result (Linux)"

; Auto classification column header in Excel
qa_excel_auto_classification = "Auto"

; Header row number in Excel
qa_excel_header_row = 2
```

## 주의사항

### 1. Destination 기본값 동작

`destination`을 두 개 이상 설정할 경우, 새롭게 추가된 destination 설정에 포함되지 않은 key들은 모두 제품의 default 값을 따라 설정됩니다.

**원인:**
- 새롭게 추가된 dest에 선언하지 않은 다른 key들의 default 값이 없는 이유는, config의 초기 구조나 기본값이 오직 기존의 정의된 `cxr_app_config.json` 파일 내용만을 신뢰해서 불러오기 때문입니다.
- 따라서 destination이 두 개인 변수를 사용하여 `update_config()`를 호출하면 `cxr_app_config.json` 파일을 기준으로 없었던 key만 추가만 되는 로직입니다.

### 2. HL7 프로토콜 사용 시 주의

HL7 프로토콜을 사용하는 destination에서 `createSc`를 `True`로 설정하면, 전송 실패로 인해 작업이 Failed 상태로 종료됩니다.

### 3. 테스트 실행 전 확인사항

- CXR 서버가 정상적으로 실행 중인지 확인
- Inference 서버 접근 가능 여부 확인
- DICOM 수신 서버(storescp)가 실행 중인지 확인
- HL7 수신 서버가 실행 중인지 확인 (HL7 테스트의 경우)
- 테스트 데이터 파일이 올바른 위치에 있는지 확인

## 참고 자료

- [공통 Rule Book]({자동화 프로젝트 Rule book link})
- [common_util.py 공통함수 목록]({공통 함수에 대한 카테고라이징 및 역할 설명 페이지 link})

## 예시

### 예시 1: Destination#1 (HL7), Destination#2 (DICOM)

두 번째 destination의 `creation.dicomSC.resultReport` key 위치의 주석 내용을 확인하세요.

```json
{
    "destinations": [
        {
            "aeTitle": DEST_AETITLE,
            "hostName": DEST_HL7_IP,
            "port": DEST_HL7_PORT,
            "protocol": "hl7",
            "creation": {
                "createHl7": true
            }
        },
        {
            "aeTitle": DEST_AETITLE,
            "hostName": DEST_IP,
            "port": DEST_PORT,
            "protocol": "dicom",
            "scUseCompression": false,
            "creation": {
                "createSc": true,
                "createGsps": true,
                "createCaBasicTextSr": true,
                "createNfBasicTextSr": true,
                "createHl7": false,
                "mergeType": "partialMerge",
                "showLowScore": true,
                "mwCmScore": true,
                "abnormalityScore": true,
                "normalFlagging": {
                    "title": "Report",
                    "report": "FINDINGS:\nLines and tubes:[None present]\nLungs and pleural space: [No focal consolidation, pleural effusion or pneumothorax.]\nCardiac silhouette, hilar regions, and trachea: [Normal.]\nThoracic osseous structures :[Normal.]\nOverlying soft tissues: [Normal.]\nUpper abdomen: [Normal.]\nIMPRESSION:\nNormal chest radiograph."
                },
                "dicomSC": {
                    "displayMode": "grayscale",
                    "resultMap": true,
                    // 해당 부분에서 선언하지 않은 "resultReport" key의 값은 True로 적용되게 됩니다.
                    "normalFlaggingDisplayType": "small"
                },
                "gsps": {
                    "invertSoftcopyLut": false,
                    "separateFindingsInfo": false
                }
            }
        }
    ]
}
```

### 예시 2: Destination#1 (DICOM), Destination#2 (HL7)

두 번째 destination의 `creation.createSc` key 위치의 주석 내용을 확인하세요.

```json
{
    "destinations": [
        {
            "aeTitle": DEST_AETITLE,
            "hostName": DEST_IP,
            "port": DEST_PORT,
            "protocol": "dicom",
            "creation": {
                "createSc": true,
                "createCaBasicTextSr": true,
                "mwCmScore": false,
                "dicomSC": {
                    "resultMap": true
                }
            }
        },
        {
            "aeTitle": DEST_AETITLE,
            "hostName": DEST_HL7_IP,
            "port": DEST_HL7_PORT,
            "protocol": "hl7",
            "creation": {
                "createHl7": true,
                "createSc": false
                // If set to True, the task will end in a Failed state due to transmission failure over the HL7 protocol.
            }
        }
    ]
}
```

