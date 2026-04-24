from typing import Any

class TraceFormatter:
    """日志格式化器"""
    
    @staticmethod
    def format(layer_name: str, direction: str, raw: bytes, decoded: Any) -> str:
        """
        格式化输出字符串，支持报文对齐可视化
        """
        arrow = "->" if direction == "TX" else "<-"
        hex_str = raw.hex(' ').upper()
        prefix = f"{direction} {arrow} "
        
        # 提取帧类型（如果存在）
        frame_type = ""
        if isinstance(decoded, dict) and "type" in decoded:
            frame_type = f"  [{decoded['type']}]"
            
        line1 = f"{prefix}{hex_str}{frame_type}"
        
        if not isinstance(decoded, dict):
            return f"{line1} | {decoded}"
            
        # 提取能够和 raw_hex 一一映射的字段
        fields = [(k, str(v)) for k, v in decoded.items() if k not in ("raw_hex", "type")]
        if not fields:
            return f"{line1} | {decoded}"
            
        # 检查是否能够完美拼合
        assembled = " ".join([v for _, v in fields])
        if assembled != hex_str:
            # 如果解码不是完全按序切分原数据，退回到传统字典展示
            return f"{line1} | {decoded}"
            
        prefix_empty = " " * len(prefix)
        line2_chars = [" "] * len(hex_str)
        line3_chars = [" "] * len(hex_str)
        line4_chars = [" "] * len(hex_str)
        
        cursor = 0
        for idx, (k, v) in enumerate(fields):
            # 动态扩展数组以容纳较长的 key
            needed = cursor + max(len(k), 1)
            while len(line2_chars) < needed:
                line2_chars.append(" ")
                line3_chars.append(" ")
                line4_chars.append(" ")
                
            # 画竖线，对齐到该块的第一个十六进制字符
            line2_chars[cursor] = '|'
            
            # 画标签名，奇偶交错放置，防止名称粘连在一起（如 PRESTART）
            target_line = line3_chars if idx % 2 == 0 else line4_chars
            for i, char in enumerate(k):
                target_line[cursor + i] = char
                
            cursor += len(v) + 1  # 移动到下一个字段 (加上 1 个空格的跨度)
            
        line2 = prefix_empty + "".join(line2_chars).rstrip()
        line3 = prefix_empty + "".join(line3_chars).rstrip()
        line4 = prefix_empty + "".join(line4_chars).rstrip()
        
        result = f"{line1}\n{line2}\n{line3}"
        if line4.strip():
            result += f"\n{line4}"
            
        return result
