from crft.parsers.base_parser import BaseParser, ParsedField, ParsedFrame


# TFI 方向定义
_TFI_DIR = {
    0xD4: "Host to Device",
    0xD5: "Device to Host",
}

# PN532 指令码映射 (TFI=0xD4 为主机发出, TFI=0xD5 为设备响应)
_COMMANDS = {
    # Host -> Device (TFI = D4)
    0xD4: {
        0x00: "Diagnose",
        0x02: "GetFirmwareVersion",
        0x04: "GetGeneralStatus",
        0x06: "ReadRegister",
        0x08: "WriteRegister",
        0x0C: "WriteGPIO",
        0x14: "SAMConfiguration",
        0x16: "PowerDown",
        0x4A: "InListPassiveTarget",
        0x40: "InDataExchange",
        0x42: "InCommunicateThru",
        0x56: "InAutoPoll",
    },
    # Device -> Host (TFI = D5)
    0xD5: {
        0x01: "Diagnose Response",
        0x03: "GetFirmwareVersion Response",
        0x05: "GetGeneralStatus Response",
        0x07: "ReadRegister Response",
        0x09: "WriteRegister Response",
        0x0D: "WriteGPIO Response",
        0x15: "SAMConfiguration Response",
        0x17: "PowerDown Response",
        0x4B: "InListPassiveTarget Response",
        0x41: "InDataExchange Response",
        0x43: "InCommunicateThru Response",
        0x57: "InAutoPoll Response",
    },
}

# InDataExchange / InCommunicateThru 响应状态码
_STATUS = {
    0x00: "Success",
    0x01: "Time Out",
    0x02: "CRC Error",
    0x03: "Parity Error",
    0x04: "Wrong Bit Count",
    0x05: "Framing Error",
    0x06: "Collision Bit Detected",
    0x07: "Buffer Overflow",
    0x09: "RF Buffer Overflow",
    0x0A: "RF Field Not On",
    0x0B: "RF Protocol Error",
    0x0D: "Temperature Error",
    0x0E: "Internal Buffer Overflow",
    0x10: "Invalid Parameter",
    0x12: "DEP Invalid Command",
    0x13: "DEP Invalid Format",
    0x14: "Auth Error",
}


class PN532HSUParser(BaseParser):
    """
    PN532 HSU (高速串口) 帧解析器。

    支持：
      - ACK / NACK 帧
      - 标准数据帧 (Extended frame 待扩展)
    """

    # 已知特殊帧
    _ACK  = b'\x00\x00\xFF\x00\xFF\x00'
    _NACK = b'\x00\x00\xFF\xFF\x00\x00'

    def can_parse(self, data: bytes) -> bool:
        return (
            data == self._ACK
            or data == self._NACK
            or (len(data) >= 6 and data[:3] == b'\x00\x00\xFF')
        )

    def parse(self, data: bytes) -> ParsedFrame:
        # --- ACK ---
        if data == self._ACK:
            return ParsedFrame(
                raw=data,
                label="PN532 ACK",
                fields=[
                    ParsedField("PREAMBLE",  b'\x00',       0x00, "Preamble"),
                    ParsedField("START CODE", b'\x00\xFF',  0x00FF, "Start of Packet"),
                    ParsedField("ACK",        b'\x00\xFF',  0x00FF, "ACK Code"),
                    ParsedField("POSTAMBLE",  b'\x00',      0x00, "Postamble"),
                ]
            )

        # --- NACK ---
        if data == self._NACK:
            return ParsedFrame(
                raw=data,
                label="PN532 NACK",
                fields=[
                    ParsedField("PREAMBLE",  b'\x00',       0x00, "Preamble"),
                    ParsedField("START CODE", b'\x00\xFF',  0x00FF, "Start of Packet"),
                    ParsedField("NACK",       b'\xFF\x00',  0xFF00, "NACK Code"),
                    ParsedField("POSTAMBLE",  b'\x00',      0x00,   "Postamble"),
                ]
            )

        # --- 标准数据帧 ---
        return self._parse_normal_frame(data)

    def _parse_normal_frame(self, data: bytes) -> ParsedFrame:
        """解析标准格式数据帧"""
        fields: list[ParsedField] = []
        is_valid = True

        # FRAME HEADER: 00 00 FF
        fields.append(ParsedField(
            name="FRAME HEADER",
            raw=data[0:3],
            value=0x0000FF,
            description="Preamble + Start Code",
        ))

        if len(data) < 6:
            return ParsedFrame(raw=data, label="PN532 Frame (Truncated)", fields=fields, is_valid=False)

        length = data[3]
        lcs    = data[4]
        lcs_ok = ((length + lcs) & 0xFF) == 0

        # FRAME CONTROL: LEN + LCS
        fc_field = ParsedField(
            name="FRAME CONTROL",
            raw=data[3:5],
            value=(data[3] << 8) | data[4],
            description=f"Length={length}, LCS={'Valid' if lcs_ok else 'Invalid!'}",
        )
        fc_field.children = [
            ParsedField("Length",      data[3:4], length, f"{length} bytes"),
            ParsedField("Length Check", data[4:5], lcs,   "Valid" if lcs_ok else "INVALID"),
        ]
        fields.append(fc_field)

        if not lcs_ok:
            is_valid = False

        # APPLICATION LAYER: TFI + CMD + [STATUS] + PAYLOAD
        app_end   = 3 + 1 + 1 + length  # 跳过 PRE/START/LEN/LCS，取 length 个字节
        app_bytes = data[5:5 + length]

        if len(app_bytes) < 2:
            return ParsedFrame(raw=data, label="PN532 Frame", fields=fields, is_valid=False)

        tfi = app_bytes[0]
        cmd = app_bytes[1]
        direction  = _TFI_DIR.get(tfi, f"Unknown (0x{tfi:02X})")
        cmd_name   = _COMMANDS.get(tfi, {}).get(cmd, f"Unknown (0x{cmd:02X})")

        app_field = ParsedField(
            name="APPLICATION LAYER",
            raw=app_bytes,
            value=tfi,
            description=cmd_name,
        )

        app_children = [
            ParsedField("Direction", bytes([tfi]), tfi, direction),
            ParsedField("Command",   bytes([cmd]), cmd, cmd_name),
        ]

        payload_start = 2
        # 对于响应帧（D5），第3字节通常是状态码
        if tfi == 0xD5 and len(app_bytes) > 2:
            status_byte = app_bytes[2]
            status_desc = _STATUS.get(status_byte, f"Unknown (0x{status_byte:02X})")
            app_children.append(ParsedField("Status", bytes([status_byte]), status_byte, status_desc))
            payload_start = 3

        if len(app_bytes) > payload_start:
            payload = app_bytes[payload_start:]
            app_children.append(ParsedField(
                name="Payload Data",
                raw=payload,
                value=payload[0] if payload else 0,
                description=f"{len(payload)} bytes",
            ))

        app_field.children = app_children
        fields.append(app_field)

        # DCS + POSTAMBLE
        if len(data) >= app_end + 1:
            dcs = data[app_end]
            fields.append(ParsedField("DCS", bytes([dcs]), dcs, "Data Checksum"))
        if len(data) >= app_end + 2:
            fields.append(ParsedField("POSTAMBLE", bytes([data[app_end + 1]]), data[app_end + 1], "End of Packet"))

        return ParsedFrame(raw=data, label="PN532 Normal Frame", fields=fields, is_valid=is_valid)
