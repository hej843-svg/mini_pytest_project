# Test case에서 사용하는 오류 메세지와 예상 응답 내용을 매핑하는 딕셔너리

error_mapping = {
    "previous_dcm is not provided": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "for compare, one of Pneumothorax, PleuralEffusion, Consolidation, Nodule options must be true": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "The request included one or more unlicensed features: (Current-Prior Comparison)": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "for compare, at least one creation sc_map or sc_report must be true": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "basic text sr can be requested with other creations(sc, gsps)": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "report can be requested with other creations": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "if normal flagging report is used, normal flagging feature must be on": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "if normal flagging is used, normal flagging report must be used": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "at least one creation is required": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"    
    },
    "title length must not be empty or exceed 80": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"    
    },
    "custom report length must not be empty or exceed 2000": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"    
    },
    "patient age is lower than specified age": {
        "expected_status": 422,
        "expected_code": "004",
        "expected_insight_error_code": "422.80.GW.004"    
    },
    "limit patient age must be between 4 and 99": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"    
    },
    "at least one finding must be true": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"    
    },
    "failed to request to predict - {\"result\":{\"message\":\"Invalid view-position.\",\"status\":\"FAILED\",\"status_code\":\"400.42.ISW.100\"}}": {
        "expected_status": 400,
        "expected_code": "102",
        "expected_insight_error_code": "400.80.GW.102"
    },
    "failed to get pixel array, check your dcm file: In DicomImage of DCMTK, specified value for an attribute not supported": {
        "expected_status": 415,
        "expected_code": "101",
        "expected_insight_error_code": "415.80.GW.101"
    },
    "one of TbScore, AbnormalityScore options must be true": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "merge type is not valid": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "with merge type partialMerge and fullMerge, gsps and separateFindingsInfo cannot be true at the same time": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "invalid language type": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "mergeType must be one of individual, partialMerge, fullMerge": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "displayMode must be one of color, grayscale, combined": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"
    },
    "limitPatientAge must be between 4 and 99": {
        "expected_status": 400,
        "expected_code": "004",
        "expected_insight_error_code": "400.80.GW.004"        
    },
    "failed to request to predict - {\"result\":{\"message\":\"Zone heatmaps of each lung must be binary maps with valid region existing.\",\"status\":\"FAILED\",\"status_code\":\"400.42.ISW.300\"}}": {
        "expected_status": 400,
        "expected_code": "999",
        "expected_insight_error_code": "400.80.GW.999"
    },
    "Authorization failed" : {
        "expected_status": 401,
        "expected_code": "009",
        "expected_insight_error_code": "401.80.GW.009"
    }
}
