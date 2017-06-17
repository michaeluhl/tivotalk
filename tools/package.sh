#!/bin/bash

SCRIPT_ROOT=`dirname $(readlink -f "$0")`
PROJ_ROOT=`dirname ${SCRIPT_ROOT}`
echo "PROJ_ROOT: $PROJ_ROOT"

LIB_DIR=${PROJ_ROOT}/lib
SKILL_DIR=${PROJ_ROOT}/alexa
BUILD_DIR=${PROJ_ROOT}/build

if [[ -f ${BUILD_DIR}/skill.zip ]]; then
    rm ${BUILD_DIR}/skill.zip ;
fi

cd ${LIB_DIR}
zip -r ${BUILD_DIR}/skill.zip * -x '*__pycache__*'
cd ${SKILL_DIR}
zip -u ${BUILD_DIR}/skill.zip *.py
