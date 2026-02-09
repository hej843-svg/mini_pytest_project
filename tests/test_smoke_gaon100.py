import sys, os
sys.path.append(os.path.dirname(__file__))
from utils import cxr_1S_inference
from utils import common_util
from utils.common_util import *
from time import sleep 
import pytest_check as check
import logging

log = logging.getLogger()

# [DIMSE] Grayscale SC map 생성
def test_smoke_OUTPUT_01(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": False,
                },
                "windowing": True
            },
            "destinations": [{
                "aeTitle": DEST_AETITLE,
                "hostName": DEST_IP,
                "port": DEST_PORT,
                "scUseCompression": False,
                "creation": {
                    "createSc": True,
                    "dicomSC": {
                        "displayMode": "grayscale",
                        "resultMap": True,
                        "resultReport": False
                    },
                }
            }]
        }],
    }
    
    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)

    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 1:
        # 결과물이 1개 일때까지 sleep 반복
        sleep(1)  

    grayscale_sc_map_file_path = common_util.get_result_file_path(result_dir_path, test_data)["sc_files"][0]
        
    # Assertion : 결과물이 Grayscale SC map 임
    check.equal(common_util.is_grayscale_sc(grayscale_sc_map_file_path), True, "The result file is not a Grayscale Secondary Capture image")
    check.equal(common_util.sc_type(grayscale_sc_map_file_path), "SC_MAP", "The result file is not a Grayscale Secondary Capture image")


# [DIMSE] Color SC map 생성
def test_smoke_OUTPUT_02(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": False,
                },
                "windowing": True
            },
            "destinations": [{
                "aeTitle": DEST_AETITLE,
                "hostName": DEST_IP,
                "port": DEST_PORT,
                "scUseCompression": False,
                "creation": {
                    "createSc": True,
                    "dicomSC": {
                        "displayMode": "color",
                        "resultMap": True,
                        "resultReport": False
                    },
                }
            }]
        }],
    }
    
    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)

    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 1:
        # 결과물이 1개 일때까지 sleep 반복
        sleep(1)  

    color_sc_map_file_path = common_util.get_result_file_path(result_dir_path, test_data)["sc_files"][0]
        
    # Assertion : 결과물이 Color SC map 임
    check.equal(common_util.sc_type(color_sc_map_file_path), "SC_MAP", "The result file is not a Color Secondary Capture image")


# [DIMSE] Combined SC map 생성
def test_smoke_OUTPUT_03(test_name):
     test_id = test_name
     test_data = "cxr_abnormal.dcm"
     updates = {
         "general": {
             "inferenceServer": {
                 "url": INSIGHT_API_HOST,
                 "apiKey": INSIGHT_API_KEY
             },
         },
         "processingRule": [{
             "source": [{
                 "aeTitle": DEST_AETITLE,
                 "ipAddress": SOURCE_IP
             }],
             "aiAnalysis": {
                 "normal_flagging": {
                     "enabled": False,
                 },
                 "windowing": True
             },
             "destinations": [{
                 "aeTitle": DEST_AETITLE,
                 "hostName": DEST_IP,
                 "port": DEST_PORT,
                 "scUseCompression": False,
                 "creation": {
                     "createSc": True,
                     "dicomSC": {
                         "displayMode": "combined",
                         "resultMap": True,
                         "resultReport": False
                     },
                 }
             }]
         }],
     }
     
     # Pre Processing 1 : dimse pre-process
     result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)
 
     # Pre Processing 2 : dcmsend 실행
     common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
     
     # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
     while common_util.check_result_file_count(result_dir_path, test_data) != 1:
         # 결과물이 1개 일때까지 sleep 반복
         sleep(1)  
 
     combined_sc_map_file_path = common_util.get_result_file_path(result_dir_path, test_data)["sc_files"][0]
         
     # Assertion : 수신된 Output을 열었을 때 Combined SC map임
     check.equal(common_util.sc_type(combined_sc_map_file_path), "SC_MAP", "The result file is not a SC MAP image")


# [DIMSE] Grayscale SC report 생성
def test_smoke_OUTPUT_04(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": False,
                },
                "windowing": True
            },
            "destinations": [{
                "aeTitle": DEST_AETITLE,
                "hostName": DEST_IP,
                "port": DEST_PORT,
                "scUseCompression": False,
                "creation": {
                    "createSc": True,
                    "dicomSC": {
                        "displayMode": "grayscale",
                        "resultMap": False,
                        "resultReport": True
                    },
                }
            }]
        }],
    }
    
    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)

    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 1:
        # 결과물이 1개 일때까지 sleep 반복
        sleep(1)  

    grayscale_sc_report_file_path = common_util.get_result_file_path(result_dir_path, test_data)["sc_files"][0]
        
    # Assertion : 결과물이 Grayscale SC report 임
    check.equal(common_util.is_grayscale_sc(grayscale_sc_report_file_path), True, "The result file is not a Grayscale Secondary Capture image")
    check.equal(common_util.sc_type(grayscale_sc_report_file_path), "SC_REPORT", "The result file is not a SC Report")


# [DIMSE] GSPS 생성
def test_smoke_OUTPUT_05(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": False,
                },
                "windowing": True
            },
            "destinations": [{
                "aeTitle": DEST_AETITLE,
                "hostName": DEST_IP,
                "port": DEST_PORT,
                "creation": {
                    "createGsps": True,
                    "createCaBasicTextSr": False,
                    "mergeType": "partialMerge",
                    "showLowScore": True,
                    "abnormalityScore": True,
                    "mwCmScore": True,
                    "gsps": {
                        "invertSoftcopyLut": False,
                        "separateFindingsInfo": False,
                        "newSeriesNumber": 1
                    }
                }
            }]
        }],        
    }
    
    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)
    
    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 1:
        sleep(1)
    
    # Assertion : 결과물이 GSPS 임
    check.equal(common_util.output_type_check(result_dir_path, test_data)["gsps"], 1, "The result file is not a GSPS file")
    

# [DIMSE] HL7 생성
def test_smoke_OUTPUT_06(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "destinations": [{
                "aeTitle": DEST_AETITLE,
                "hostName": DEST_HL7_IP,
                "port": DEST_HL7_PORT,
                "protocol": "hl7",
                "creation": {
                    "createHl7": True,
                }
            }]
        }],
    }
    
    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)
    
    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 1개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 1:
        sleep(1)
    
    # Assertion : 결과물이 HL7 임
    check.equal(common_util.output_type_check(result_dir_path, test_data)["hl7"], 1, "The result file is not a HL7 file")


# [DIMSE] SC map/report, GSPS, BasicTextSR, HL7 복합 생성
def test_smoke_OUTPUT_07(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": False
                },
                "windowing": True
            },
            "destinations": [
                {
                    "aeTitle": DEST_AETITLE,
                    "hostName": DEST_HL7_IP,
                    "port": DEST_HL7_PORT,
                    "protocol": "hl7",
                    "creation": {
                        "createHl7": True,
                    }
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
                        "createNfBasicTextSr": False,
                        "createHl7": False,
                        "mergeType": "partialMerge",
                        "showLowScore": True,
                        "mwCmScore": True,
                        "abnormalityScore": True,
                        "normalFlagging": {
                            "title": "Report",
                            "report": "FINDINGS:\nLines and tubes:[None present]\nLungs and pleural space: [No focal consolidation, pleural effusion or pneumothorax.]\nCardiac silhouette, hilar regions, and trachea: [Normal.]\nThoracic osseous structures :[Normal.]\nOverlying soft tissues: [Normal.]\nUpper abdomen: [Normal.]\nIMPRESSION:\nNormal chest radiograph."
                        },
                        "dicomSC": {
                            "displayMode": "grayscale",
                            "resultMap": True,
                            "resultReport": True,
                            "normalFlaggingDisplayType": "small",
                        },
                        "gsps": {
                            "invertSoftcopyLut": False,
                            "separateFindingsInfo": False,
                        },
                    }
                }
            ],
        }],
    }

    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)
    
    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 5개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 5:
        sleep(1)
        
    # Assertion : 결과물이 SC map/report, GSPS, BasicTextSR, HL7 임
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["sc_map"], 1, "Mismatch in expected number of SC map file in the results")
    check.equal(result_counts["sc_report"], 1, "Mismatch in expected number of SC report file in the results")
    check.equal(result_counts["gsps"], 1, "Mismatch in expected number of GSPS file in the results")
    check.equal(result_counts["sr"], 1, "Mismatch in expected number of BasicTextSR file in the results")
    check.equal(result_counts["hl7"], 1, "Mismatch in expected number of HL7 file in the results")


# [DIMSE] Normal Flagging 기능
def test_smoke_OUTPUT_08(test_name):
    test_id = test_name
    test_data = "cxr_normal.dcm"
    updates = {
        "general": {
            "inferenceServer": {
                "url": INSIGHT_API_HOST,
                "apiKey": INSIGHT_API_KEY
            },
        },
        "processingRule": [{
            "source": [{
                "aeTitle": DEST_AETITLE,
                "ipAddress": SOURCE_IP
            }],
            "aiAnalysis": {
                "normal_flagging": {
                    "enabled": True
                },
                "windowing": True
            },
            "destinations": [
                {
                    "aeTitle": DEST_AETITLE,
                    "hostName": DEST_HL7_IP,
                    "port": DEST_HL7_PORT,
                    "protocol": "hl7",
                    "creation": {
                        "createHl7": True,
                    }
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
                            "report": "FINDINGS:\nLines and tubes:[None present]\nLungs and pleural space: [No focal consolidation, pleural effusion or pneumothorax.]\nCardiac silhouette, hilar regions, and trachea: [Normal.]\nThoracic osseous structures :[Normal.]\nOverlying soft tissues: [Normal.]\nUpper abdomen: [Normal.]\nIMPRESSION:\nNormal chest radiograph."
                        },
                        "dicomSC": {
                            "displayMode": "grayscale",
                            "resultMap": True,
                            "resultReport": True,
                            "normalFlaggingDisplayType": "small",
                        },
                        "gsps": {
                            "invertSoftcopyLut": False,
                            "separateFindingsInfo": False,
                        },
                    }
                }
            ],
        }],
    }

    # Pre Processing 1 : dimse pre-process
    result_dir_path = common_util.dimse_pre_process(test_id, test_data, updates)
    
    # Pre Processing 2 : dcmsend 실행
    common_util.dcmsend_to_app(CXR_IP, CXR_SCP_PORT, DEST_AETITLE, result_dir_path)
    
    # Pre Processing 3 : 결과물 파일이 5개 존재할때까지 대기
    while common_util.check_result_file_count(result_dir_path, test_data) != 5:
        sleep(1)
        
    # Assertion : 결과물이 SC map/report, GSPS, BasicTextSR, HL7 임
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["sc_map"], 1, "Mismatch in expected number of SC map file in the results")
    check.equal(result_counts["sc_report"], 1, "Mismatch in expected number of SC report file in the results")
    check.equal(result_counts["gsps"], 1, "Mismatch in expected number of GSPS file in the results")
    check.equal(result_counts["sr"], 1, "Mismatch in expected number of BasicTextSR file in the results")
    check.equal(result_counts["hl7"], 1, "Mismatch in expected number of HL7 file in the results")
    
    # Assertion : 모든 결과물이 normal 결과를 가지고 있는지 확인
    non_normal_files = common_util.is_normal_result(result_dir_path, test_data)
    check.equal(len(non_normal_files), 0, "Expected no files with normal results")
    

# [1Step/inference] Grayscale SC map 생성
def test_smoke_1S_INFERENCE_01(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "sc_map": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "grayscale",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 Grayscale SC map 임
    grayscale_sc_map_file_path = os.path.join(result_dir_path, "scMap0.dcm")
    check.equal(common_util.is_grayscale_sc(grayscale_sc_map_file_path), True, "The result file is not a Grayscale Secondary Capture image")
    check.equal(common_util.sc_type(grayscale_sc_map_file_path), "SC_MAP", "The result file is not a Grayscale Secondary Capture image")


# [1Step/inference] Color SC map 생성
def test_smoke_1S_INFERENCE_02(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "sc_map": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "color",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 Color SC map 임
    color_sc_map_file_path = os.path.join(result_dir_path, "scMap0.dcm")
    check.equal(common_util.sc_type(color_sc_map_file_path), "SC_MAP", "The result file is not a Color Secondary Capture image")


# [1Step/inference] Combined SC map 생성
def test_smoke_1S_INFERENCE_03(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "sc_map": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "combined",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 Grayscale SC map 임
    combined_sc_map_file_path = os.path.join(result_dir_path, "scMap0.dcm")
    check.equal(common_util.sc_type(combined_sc_map_file_path), "SC_MAP", "The result file is not a SC MAP image")


# [1Step/inference] Grayscale SC report 생성
def test_smoke_1S_INFERENCE_04(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "sc_report": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "grayscale",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 Grayscale SC report 임
    grayscale_sc_report_file_path = os.path.join(result_dir_path, "scReport0.dcm")
    check.equal(common_util.is_grayscale_sc(grayscale_sc_report_file_path), True, "The result file is not a Grayscale Secondary Capture image")
    check.equal(common_util.sc_type(grayscale_sc_report_file_path), "SC_REPORT", "The result file is not a SC Report")


# [1Step/inference] GSPS 생성
def test_smoke_1S_INFERENCE_05(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "gsps": True,
        },
        "creation_options": {
            "tb_analysis_score": True,
            "show_low_score": True,
        },
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 GSPS 임을 확인
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["gsps"], 1, "Mismatch in expected number of GSPS file in the results")


# [1Step/inference] HL7 생성
def test_smoke_1S_INFERENCE_06(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "hl7": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 HL7 임을 확인
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["hl7"], 1, "Mismatch in expected number of HL7 file in the results")
    

# [1Step/inference] SC map/report, GSPS, BasicTextSR, HL7 복합 생성
def test_smoke_1S_INFERENCE_07(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "sc_report": True,
            "sc_map": True,
            "gsps": True,
            "basic_text_sr": True,
            "hl7": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "grayscale",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 SC map/report, GSPS, BasicTextSR, HL7 임을 확인
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["sc_map"], 1, "Mismatch in expected number of SC map file in the results")
    check.equal(result_counts["sc_report"], 1, "Mismatch in expected number of SC report file in the results")
    check.equal(result_counts["gsps"], 1, "Mismatch in expected number of GSPS file in the results")
    check.equal(result_counts["sr"], 1, "Mismatch in expected number of BasicTextSR file in the results")
    check.equal(result_counts["hl7"], 1, "Mismatch in expected number of HL7 file in the results")


# [1Step/inference] Normal Flagging 기능
def test_smoke_1S_INFERENCE_08(test_name):
    test_id = test_name
    test_data = "cxr_normal.dcm"
    updates = {
        "creation": {
            "sc_report": True,
            "sc_map": True,
            "gsps": True,
            "basic_text_sr": True,
            "normal_flagging_sr": True,
            "hl7": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "grayscale",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": True,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference 전처리
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : 변환된 Output이 SC map/report, GSPS, BasicTextSR, HL7 임을 확인
    result_counts = common_util.output_type_check(result_dir_path, test_data)
    check.equal(result_counts["sc_map"], 1, "Mismatch in expected number of SC map file in the results")
    check.equal(result_counts["sc_report"], 1, "Mismatch in expected number of SC report file in the results")
    check.equal(result_counts["gsps"], 1, "Mismatch in expected number of GSPS file in the results")
    check.equal(result_counts["sr"], 1, "Mismatch in expected number of BasicTextSR file in the results")
    check.equal(result_counts["hl7"], 1, "Mismatch in expected number of HL7 file in the results")
    
    # Assertion : 모든 결과물이 normal 결과를 가지고 있는지 확인
    non_normal_files = common_util.is_normal_result(result_dir_path, test_data)
    check.equal(len(non_normal_files), 0, "Expected no files with normal results")
    
    
# [1Step/inference] CPC 기능
def test_smoke_1S_INFERENCE_09(test_name):
    test_id = test_name
    test_data1 = "comparison/current.dcm"
    test_data2 = "comparison/previous.dcm"
    updates = {
        "creation": {
            "sc_report": True,
            "sc_map": True,
            "gsps": True,
            "basic_text_sr": True,
            "hl7": True,
        },
        "creation_options": {
            "merge_type": "partialMerge",
            "display_mode": "grayscale",
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        }
    }
    
    # Pre Processing 1 : 1 Step Inference pre-process
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data1, updates)
    result_dir_path, updated_inference_json = common_util.pre_process_1S_inference(test_id, test_data2, updates)
   
    # Pre Processing 2 : 1 Step Inference api request
    test_sample_path1 = os.path.join(result_dir_path, test_data1)
    test_sample_path2 = os.path.join(result_dir_path, test_data2)
    response_data = cxr_1S_inference.post_1S_inference_with_CPC(updated_inference_json, CXR_IP, CXR_APP_PORT, test_sample_path1, test_sample_path2, INSIGHT_API_KEY)
    
    # Pre Processing 3 : Save response body to file
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 200 OK
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertion : Check output counts
    result_counts = common_util.output_type_check(result_dir_path, test_data1)
    
    expected_counts = {
        "sc_map": 1,
        "sc_report": 1,
        "sc_additional": 1,
        "gsps": 1,
        "sr": 1,
        "hl7": 1,
    }
    common_util.check_output_type_counts(result_counts, expected_counts)

    # TODO : Manually verify whether the generated HL7 message contains content successfully analyzed by CPC.


# [1Step/inference/raw-data] Score.json 생성
def test_smoke_1S_RAW_01(test_name):
     test_id = test_name
     test_data = "cxr_abnormal.dcm"
     updates = {
         "creation": {
             "score": True,
         },
         "creation_options": {
             "tb_score": True,
             "show_low_score": True,
             "normal_flagging": {
                 "use": False,
             }
         },
     }
     
     # Pre Processing 1 : 1 Step Inference raw data 전처리
     result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
     
     # Pre Processing 2 : 1 Step Inference Raw Data api 요청
     test_sample_path = os.path.join(result_dir_path, test_data)
     response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
     
     # Pre Processing 3 : 응답 내용을 JSON 파일로 저장
     result_file_path = os.path.join(result_dir_path, 'score0.json')  # 결과 파일 경로 설정
     with open(result_file_path, 'wb') as json_file:  # 'wb' 모드로 파일 열기
         json_file.write(response_data.content)  # 결과를 JSON 형식으로 저장
 
     # Assertions 1 : 200 OK 응답이 돌아옴
     check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
     
     # Assertions 2 : 응답 Body의 json 구조가 메모와 동일하게 구성됨
     # - 아래 Key들이 Json에 모두 포함됨
     # (score, metascore, all_findings_under_thresholds, message)
     common_util.score_json_assertions(result_file_path)    
    

# [1Step/inference/raw-data] Normal Flagging Report.json 생성
def test_smoke_1S_RAW_02(test_name):
    test_id = test_name
    test_data = "cxr_normal.dcm"
    updates = {
        "creation": {
            "score": True,
            "report": True,
            "normal_flagging_report": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "report_note": True,
            "normal_flagging": {
                "use": True,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 파일로 저장
    common_util.save_response_body_to_file(response_data.content, response_data.headers, result_dir_path)
    
    # Assertion : 1 Step Inference Raw Data api 호출 결과가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")

    # Assertions : JSON 결과 파일이 score json 응답 구조인지 확인 
    score_result_file_path = os.path.join(result_dir_path, 'score0.json')  # score json 파일 경로 설정
    common_util.normal_flagging_score_json_assertions(score_result_file_path)

    # Assertions : JSON 결과 파일이 report json 응답 구조인지 확인
    report_result_file_path = os.path.join(result_dir_path, 'report0.json')  # score json 파일 경로 설정
    common_util.normal_flagging_report_json_assertions(report_result_file_path)
    

# [1Step/inference/raw-data] Grayscale map.jpg 생성
def test_smoke_1S_RAW_03(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "grayscale_jpg_map": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장

    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # Assertions 3 : 결과물이 Grayscale map.jpg 임을 확인
    # TODO : jpg 결과물로 grayscale인지 color인지 확인 하는 함수 추가 필요
    

# [1Step/inference/raw-data] Grayscale Report.jpg 생성
def test_smoke_1S_RAW_04(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "grayscale_jpg_report": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장

    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # Assertions 3 : 결과물이 Grayscale Report.jpg 임을 확인
    # TODO : jpg 결과물로 grayscale인지 color인지 확인 하는 함수 추가 필요
    

# [1Step/inference/raw-data] Color map.jpg 생성 
def test_smoke_1S_RAW_05(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "color_jpg_map": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장
        
    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # TODO : Assertions 3 : response body가 Color Report.jpg 이미지임


# [1Step/inference/raw-data] Color Report.jpg 생성 
def test_smoke_1S_RAW_06(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "color_jpg_report": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장
    
    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # TODO : Assertions 3 : response body가 Color Report.jpg 이미지임


# [1Step/inference/raw-data] Combined map.jpg 생성
def test_smoke_1S_RAW_07(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "combined_jpg_map": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장
    
    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # TODO : Assertions 3 : response body가 Combined map.jpg 이미지임


# [1Step/inference/raw-data] Combined Report.jpg 생성
def test_smoke_1S_RAW_08(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "combined_jpg_report": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JPG 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.jpg')  # 결과 파일 경로 설정
    with open(result_file_path, 'wb') as jpg_file:  # 'wb' 모드로 파일 열기
        jpg_file.write(response_data.content)  # 결과를 JPG 형식으로 저장
    
    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : 결과물이 JPG 형식인지 확인
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # TODO : Assertions 3 : response body가 Combined Report.jpg 이미지임


# [1Step/inference/raw-data] grayscale.json 생성
def test_smoke_1S_RAW_09(test_name):
     test_id = test_name
     test_data = "cxr_abnormal.dcm"
     updates = {
         "creation": {
             "grayscale_json": True,
         },
         "creation_options": {
             "tb_score": True,
             "show_low_score": True,
             "normal_flagging": {
                 "use": False,
             }
         },
     }
     
     # Pre Processing 1 : 1 Step Inference raw data 전처리
     result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
     
     # Pre Processing 2 : 1 Step Inference Raw Data api 요청
     test_sample_path = os.path.join(result_dir_path, test_data)
     response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
     
     # Pre Processing 3 : 응답 내용을 JSON 파일로 저장
     result_file_path = os.path.join(result_dir_path, 'result.json')  # 결과 파일 경로 설정
     with open(result_file_path, 'w') as json_file:  # 'w' 모드로 파일 열기
         json_file.write(response_data.content.decode('utf-8'))  # 바이트를 문자열로 변환하여 저장
 
     # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
     check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
     
     # Assertions : JSON 결과 파일이 grayscale json 응답 구조인지 확인
     common_util.grayscale_json_assertions(result_file_path)
     
     # Assertions : Check that the result.front.pos_map key is not included in the json file
     with open(result_file_path, 'r') as json_file:
        grayscale_response_json = json.load(json_file)
        check.is_false("pos_map" in grayscale_response_json.get("result", {}).get("front", {}), "pos_map key should not be present in the response")
 

# [1Step/inference/raw-data] color.json 생성
def test_smoke_1S_RAW_10(test_name):
     test_id = test_name
     test_data = "cxr_abnormal.dcm"
     updates = {
         "creation": {
             "color_json": True,
         },
         "creation_options": {
             "tb_score": True,
             "show_low_score": True,
             "normal_flagging": {
                 "use": False,
             }
         },
     }
     
     # Pre Processing 1 : 1 Step Inference raw data 전처리
     result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
     
     # Pre Processing 2 : 1 Step Inference Raw Data api 요청
     test_sample_path = os.path.join(result_dir_path, test_data)
     response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
     
     # Pre Processing 3 : 응답 내용을 JSON 파일로 저장
     result_file_path = os.path.join(result_dir_path, 'result.json')  # 결과 파일 경로 설정
     with open(result_file_path, 'w') as json_file:  # 'w' 모드로 파일 열기
         json_file.write(response_data.content.decode('utf-8'))  # 바이트를 문자열로 변환하여 저장
 
     # Assertion : 1 Step Inference api 호출 결과가 200 인지 확인
     check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
     
     # Assertions : JSON 결과 파일이 color json 응답 구조인지 확인
     common_util.color_json_assertions(result_file_path)
     
    # Assertions : Check that the result.frontal.findings key key is not included in the json file
     with open(result_file_path, 'r') as json_file:
        color_response_json = json.load(json_file)
        check.is_false("findings" in color_response_json.get("result", {}).get("frontal", {}), "findings key should not be present in the response")


# [1Step/inference/raw-data] Combined.json 생성
def test_smoke_1S_RAW_11(test_name):
    test_id = test_name
    test_data = "cxr_abnormal.dcm"
    updates = {
        "creation": {
            "combined_json": True,
        },
        "creation_options": {
            "tb_score": True,
            "show_low_score": True,
            "normal_flagging": {
                "use": False,
            }
        },
    }
    
    # Pre Processing 1 : 1 Step Inference raw data 전처리
    result_dir_path, updated_inference_raw_data_json = common_util.pre_process_1S_inference_raw_data(test_id, test_data, updates)
    
    # Pre Processing 2 : 1 Step Inference Raw Data api 요청
    test_sample_path = os.path.join(result_dir_path, test_data)
    response_data = cxr_1S_inference.post_1S_inference_raw_data(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path, INSIGHT_API_KEY)
    
    # Pre Processing 3 : 응답 내용을 JSON 파일로 저장
    result_file_path = os.path.join(result_dir_path, 'result.json')  # 결과 파일 경로 설정
    with open(result_file_path, 'w') as json_file:  # 'w' 모드로 파일 열기
        json_file.write(response_data.content.decode('utf-8'))  # 바이트를 문자열로 변환하여 저장

    # Assertions 1 : API 응답 코드가 200 인지 확인
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")
    
    # Assertions 2 : JSON 결과 파일이 combined json 응답 구조인지 확인
    common_util.combined_json_assertions(result_file_path)


# [1Step/inference/raw-data] Grayscale Additional.jpg 생성
def test_smoke_1S_RAW_12(test_name):
    test_id = test_name
    test_data1 = "comparison/current.dcm"
    test_data2 = "comparison/previous.dcm"
    updates = {
        "creation": {
            "grayscale_jpg_additional": True,
        },
        "creation_options": {
            "tb_score": True,
            "abnormality_score": True,
            "normal_flagging": {
                "use": False,
            },
        },
    }

    # Pre Processing 1 : 1 Step Inference raw data pre-process
    result_dir_path, updated_inference_raw_data_json = (common_util.pre_process_1S_inference_raw_data(test_id, test_data1, updates))
    result_dir_path, updated_inference_raw_data_json = (common_util.pre_process_1S_inference_raw_data(test_id, test_data2, updates))

    # Pre processing 2 : 1 Step Inference Raw Data API request
    test_sample_path1 = os.path.join(result_dir_path, test_data1)
    test_sample_path2 = os.path.join(result_dir_path, test_data2)
    response_data = cxr_1S_inference.post_1S_inference_raw_data_with_CPC(updated_inference_raw_data_json, CXR_IP, CXR_APP_PORT, test_sample_path1, test_sample_path2)

    # Pre Processing 3 : Save response body to file
    result_file_path = os.path.join(result_dir_path, "result.jpg")  # Set the output file path
    with open(result_file_path, "wb") as json_file: # Open the file in 'wb' (write-binary) mode
        json_file.write(response_data.content)  # Save the result in JPG format

    # Assertion : 200 OK
    check.equal(response_data.status_code, 200, "The API request did not return a status code of 200.")

    # Assertions : Check the respons_data.content is jpg type
    common_util.is_jpg_file(response_data.content, response_data.headers)
    
    # TODO : Manually verify whether the response body is the grayscale additional.jpg image.