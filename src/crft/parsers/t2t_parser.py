from crft.parsers.base_parser import BaseParser, ParsedField, ParsedFrame


# NFC Forum Type 2 Tag 指令码 (ISO14443-3A 层)
_T2T_CMDS = {
    0x30: ("READ",      "Read 4 pages (16 bytes)"),
    0xA2: ("WRITE",     "Write 1 page (4 bytes)"),
    0x50: ("HALT",      "Halt"),
    0x60: ("AUTH",      "Authenticate"),
    0x1B: ("PWD_AUTH",  "Password Authentication"),
    0x3C: ("READ_SIG",  "Read Signature"),
}

# ACK / NACK 响应
_T2T_RESPONSE = {
    0x0A: "ACK (Success)",
    0x05: "NACK — Invalid argument",
    0x00: "NACK — Not authenticated / Parity error",
}


class T2TParser(BaseParser):
    """
    NFC Forum Type 2 Tag (T2T) 指令解析器。

    解析对象为剥离 PN532 封装后的原始 T2T 帧层数据。
    目前实现：READ / WRITE / PWD_AUTH 指令，以及 ACK/NACK 响应。
    """

    def can_parse(self, data: bytes) -> bool:
        if not data:
            return False
        # 单字节 ACK/NACK
        if len(data) == 1 and data[0] in _T2T_RESPONSE:
            return True
        return data[0] in _T2T_CMDS

    def parse(self, data: bytes) -> ParsedFrame:
        if not data:
            return ParsedFrame(raw=data, label="T2T (Empty)", is_valid=False)

        # ACK / NACK 响应（单字节）
        if len(data) == 1 and data[0] in _T2T_RESPONSE:
            desc = _T2T_RESPONSE[data[0]]
            return ParsedFrame(
                raw=data,
                label="T2T Response",
                fields=[ParsedField("Response", data, data[0], desc)],
            )

        cmd_byte = data[0]
        short_name, cmd_desc = _T2T_CMDS.get(cmd_byte, ("UNKNOWN", f"Unknown Command 0x{cmd_byte:02X}"))

        fields: list[ParsedField] = []
        fields.append(ParsedField("Command", bytes([cmd_byte]), cmd_byte, f"{short_name} — {cmd_desc}"))

        # READ: CMD(1) + PAGE_ADDR(1)
        if cmd_byte == 0x30:
            if len(data) >= 2:
                page = data[1]
                fields.append(ParsedField("Page Address", bytes([page]), page, f"Page {page} (byte offset {page * 4})"))

        # WRITE: CMD(1) + PAGE_ADDR(1) + DATA(4)
        elif cmd_byte == 0xA2:
            if len(data) >= 2:
                page = data[1]
                fields.append(ParsedField("Page Address", bytes([page]), page, f"Page {page}"))
            if len(data) >= 6:
                payload = data[2:6]
                fields.append(ParsedField("Write Data", payload, payload[0], "4-byte page data"))

        # PWD_AUTH: CMD(1) + PWD(4)
        elif cmd_byte == 0x1B:
            if len(data) >= 5:
                pwd = data[1:5]
                fields.append(ParsedField("Password", pwd, int.from_bytes(pwd, "big"), "4-byte password"))

        # HALT: CMD(1) + 0x00
        elif cmd_byte == 0x50:
            if len(data) >= 2:
                fields.append(ParsedField("Reserved", bytes([data[1]]), data[1], "Must be 0x00"))

        # 通用载荷
        else:
            if len(data) > 1:
                payload = data[1:]
                fields.append(ParsedField("Payload", payload, payload[0], f"{len(payload)} bytes"))

        return ParsedFrame(raw=data, label=f"T2T — {short_name}", fields=fields)
