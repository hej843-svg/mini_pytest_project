# 공통 rule book
{자동화 프로젝트 Rule book link}

# common_util.py에 있는 공통함수 목록
{공통 함수에 대한 카테고라이징 및 역할 설명 페이지 link}

# CXR-4010, GAON-1000 pytest 주의 사항

#### 1. `destination`을 두 개 이상 설정할 경우, 새롭게 추가된 destination 설정에 아래 JSON 내용 중 특정 key 설정이 'creation' key 하위에 추가되어야 합니다. 이 설정이 누락되면 PUT /config 시 에러가 발생할 수 있습니다.
- 아래 json 구조내에서 'mergeType', 'normalFlagging', 'dicomSC' key 항목 참고

                {
                    "aeTitle": DEST_AETITLE,
                    "hostName": DEST_HL7_IP,
                    "port": DEST_HL7_PORT,
                    "protocol": "hl7",
                    "creation": {
                        "createHl7": True,
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

----------------------
#### 2. `destination`을 두 개 이상 설정할 경우, 새롭게 추가된 destination 설정에 포함되지 않은 key들은 모두 제품의 default 값을 따라 설정됨 유의.
- 원인 : 
  새롭게 추가된 dest에 선언하지 않은 다른 key들의 default 값이 없는 이유는, config의 초기 구조나 기본값이 오직 기존의 정의된 'cxr_app_config.json' 파일 내용만을 신뢰해서 불러오기 때문입니다.
  따라서 destination이 두 개인 변수를 사용하여 update_config()를 호출하면 'cxr_app_config.json' 파일을 기준으로 없었던 key만 추가만 되는 로직.

- 예시 1 : Destination#1 hl7, Destination#2가 dicom
  두번째 destination의 creation.dicomSC.resultReport key 위치의 주석 내용 확인.
                "destinations": [
                    {
                        "aeTitle": DEST_AETITLE,
                        "hostName": DEST_HL7_IP,
                        "port": DEST_HL7_PORT,
                        "protocol": "hl7",
                        "creation": {
                            "createHl7": True,
                        },
                    },
                    {
                        "aeTitle": DEST_AETITLE,
                        "hostName": DEST_IP,
                        "port": DEST_PORT,
                        "protocol": "dicom",
                        "scUseCompression": False,
                        "creation": {
                            "createSc": True,
                            "createGsps": True,
                            "createCaBasicTextSr": True,
                            "createNfBasicTextSr": True,
                            "createHl7": False,
                            "mergeType": "partialMerge",
                            "showLowScore": True,
                            "mwCmScore": True,
                            "abnormalityScore": True,
                            "normalFlagging": {
                                "title": "Report",
                                "report": "FINDINGS:\nLines and tubes:[None present]\nLungs and pleural space: [No focal consolidation, pleural effusion or pneumothorax.]\nCardiac silhouette, hilar regions, and trachea: [Normal.]\nThoracic osseous structures :[Normal.]\nOverlying soft tissues: [Normal.]\nUpper abdomen: [Normal.]\nIMPRESSION:\nNormal chest radiograph.",
                            },
                            "dicomSC": {
                                "displayMode": "grayscale",
                                "resultMap": True,
                                // 해당 부분에서 선언하지 않은 "resultReport" key의 값은 True로 적용되게 됩니다.
                                "normalFlaggingDisplayType": "small",
                            },
                            "gsps": {
                                "invertSoftcopyLut": False,
                                "separateFindingsInfo": False,
                            },
                        },
                    },
                ],

- 예시 2 : Destination#1 dicom, Destination#2가 hl7
  두번째 destination의 creation.createSc key 위치의 주석 내용 확인.
                "destinations": [
                    {
                        "aeTitle": DEST_AETITLE,
                        "hostName": DEST_IP,
                        "port": DEST_PORT,
                        "protocol": "dicom",
                        "creation": {
                            "createSc": True, 
                            "createCaBasicTextSr": True,
                            "mwCmScore": False,
                            "dicomSC": {
                                "resultMap": True
                            }
                        }
                    },
                    {
                        "aeTitle": DEST_AETITLE,
                        "hostName": DEST_HL7_IP,
                        "port": DEST_HL7_PORT,
                        "protocol": "hl7",
                        "creation": {
                            "createHl7": True,
                            "createSc": False, # If set to True, the task will end in a Failed state due to transmission failure over the HL7 protocol.
                        },
                    }
                ]

----------------------
