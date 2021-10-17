#!/bin/bash
/usr/sbin/cupsd
lpadmin -p ${CUPS_PRINTER_NAME} -E -v ${CUPS_PRINTER_PATH}  -P ${CUPS_PPD_PATH}
tail -F YOU_CAN_IGNORE_THIS_ERROR
