OPERATION_CODES = {
    "CREATE": 1,
    "JOIN": 2,
    "LEAVE": 3
}

STATE_CODES = {
    "REQUEST": 0,
    "ACCEPTED": 1,
    "CREATED": 2,
    "SUCCESS": 3,
    "DENIED": 4
}

STATUS_CODES = {
    "SUCCESS": "200",
    "CREATED": "201",
    "ACCEPTED": "202",
    "ROOM_NOT_FOUND": "404",
    "ROOM_EXISTS": "409",
    "USERNAME_EXISTS": "430",
    "USERNAME_NOT_FOUND": "431",
    "SERVER_FULL": "503",
}