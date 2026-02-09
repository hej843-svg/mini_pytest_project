<!-- NOTE : The template below is for your reference. Feel free to modify/delete according to the actual situation. -->

### 🧾 Description (Required)
> PR의 생성 목적을 기술해주세요.

- 예시:
GET /api/v1/config API 역할을 하는 공통함수가 없어서 테스트 함수내에서 독자적으로 요청하도록 작성되고 있었음.
→ GET config API 함수 추가

- 예시:
'영상 분석 및 결과 생성' Depth의 nn행 ~ nn행까지의 테스트 함수를 추가하였습니다.

- 예시:
PR #nn 번의 피드백에 따라 수정하였습니다.

---
### ✨ Changes (Optional)
> 구현하거나 수정한 기능에 대해 기술해주세요.
> 새로운 로직/패턴이 있다면 간략한 설명을 반드시 포함해주세요.

예시:
- [gaon/gaon-100/utils/cxr_config.py] 파일에 GET /api/v1/config API 역할을 하는 get_config_test 함수 추가
- 새롭게 추가된 get_config_test 함수의 사용 예시를 위해 [gaon/gaon-100/cxr-4010/tests/testcase/test_example.py] 파일에  test_get_config_api() 함수 추가
- 분석 결과물들의 "0009,1001" tag의 값이 소수점 둘째자리인지 확인하는 부분에서 이중 for문을 사용하였습니다. 
   - 가장 바깥의 for문에서는 tag_value_Abnormality_Score 리스트의 key와 value를 가져옵니다.
   - 가장 안쪽의 for문에서는 여러개의 values 값들을 하나씩 가져와 for 문안의 내용을 검사하게됩니다.
```python
    # tag_value_Abnormality_Score의 모든 key 값이 소수점 둘째자리인지 확인
    for key, values in tag_value_Abnormality_Score.items():
        for value in values:
            value_str = str(value)
            check.is_true(value_str.isdigit() or value_str.replace('.', '').isdigit(), 
                          f"tag_value_Abnormality_Score: {value_str} from {key} is not a number or a number with two decimal places")
``` 

---
### 📌 Checklist (Optional)
> 리뷰 시 중점적으로 확인해주셨으면 하는 부분이 있다면 적어주세요.

예시:
- [ ] API 응답 필드 구조 검토

- [ ] 공통 로직으로의 분리 방식이 적절한지 확인

- [ ] 실패 케이스 처리 방식에 대한 의견 요청

---
### 🧪 Test Log (Required)
> - 리뷰어가 테스트 내용을 빠르게 이해할 수 있도록 테스트된 항목을 명확히 기술해주세요. 
>   - 각 테스트 로그 상단에 어떤 의도로 출력한 로그인지 간략히 기입해주세요.
>   - 확인하고자 하는 목적에 상관없는 로그는 생략해주세요.
> - PASS 테스트 log는 필수, FAIL 테스트 log는 불가능한 상황을 제외하고 되도록 첨부해주세요.


예시:
- [x] 제품 설정값을 "displayMode": "color", "resultMap": True, 값으로 요청 후 get_config_test 함수 사용하였고, 그 응답값의 body를 출력하여 의도한 설정값대로 반환됨을 확인하였습니다.

```shell
DEBUG    root:test_example.py:867 Response: {
  "version": "4.1.0",
  "general": {
    "language": "en",
    "showLicenseWarning": false,
    "showLicenseWarningDetail": false,
    "inferenceServer": {
      "url": "http://10.120.204.3:8203",
      "apiKey": "your_insight_api_key"
    },
    "insightAeTitle": "LUNIT",
    "taskDataRetention": true,
    "taskDataRetentionDay": 1,
    "unprocessedFileRetention": true,
    "unprocessedFileRetentionHour": 1,
    "processedFileRetention": true,
    "processedFileRetentionHour": 1,
    "storeOutputDelaySec": 0
  },
  "currentPriorComparison": {
    "findScpAeTitle": "DVTK_QR_SCP",
    "findScpHostName": "",
    "findScpPort": 106,
    "searchImagesTaken": 365,
    "excludeImagesTaken": 60,
    "tagForQuery": [
      {
        "include": [],
        "exclude": []
      }
    ],
    "moveScpAeTitle": "DVTK_QR_SCP",
    "moveScpHostName": "",
    "moveScpPort": 106,
    "cmoveProtocolWaitSec": 3,
    "filteringTag": [
      {
        "include": [],
        "exclude": []
      }
    ]
  },
  "processingRule": [
    {
      "source": [
        {
          "any": false,
          "aeTitle": "ej",
          "ipAddress": "10.10.140.37",
          "useForwardDcm": false,
          "forward": {
            "aeTitle": "",
            "hostName": "",
            "port": 0,
            "params": ""
          }
        }
      ],
      "filtering": {
        "useAgeFilter": true,
        "limitPatientAge": 4,
        "frontalXray": false,
        "ignoreDuplicateSop": false,
        "filteringRules": [
          {
            "include": [],
            "exclude": []
          }
        ]
      },
      "aiAnalysis": { ... 생략 ...},
      "destinations": [
        {
          "aeTitle": "ej",
          "protocol": "dicom",
          "hostName": "10.10.140.37",
          "port": 10004,
          "params": "",
          "scUseCompression": false,
          "creation": {
            "createSc": true,
            "createGsps": false,
            "createNfBasicTextSr": false,
            "createCaBasicTextSr": false,
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
              "displayMode": "color",
              "resultMap": true,
              "resultReport": false,
              "normalFlaggingDisplayType": "small",
              "studyDescription": null,
              "seriesDescription": null,
              "createNewSeries": true,
              "newSeriesNumber": 99999999,
              "instanceNumber": 999999
            },
            "gsps": {
              "invertSoftcopyLut": false,
              "separateFindingsInfo": false,
              "newSeriesNumber": 1
            },
            "hl7": {},
            "sr": {
              "newSeriesNumber": 1
            },
            "useComparison": false
          }
        }
      ]
    }
  ]
}
PASSED                                                                                                                                                                                                                                                              [100%]

============================================================================================================================ 1 passed in 3.95s ============================================================================================================================
``` 